import uuid, os
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Task, Attachment
from app.utils import get_membership

attachments_bp = Blueprint('attachments', __name__)

@attachments_bp.route('/tasks/<int:task_id>/attachments', methods=['POST'])
@jwt_required()
def upload_attachment(task_id):
    current_user_id = int(get_jwt_identity())

    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    membership = get_membership(task.project_id, current_user_id)
    if not membership:
        return jsonify({'error': 'Task not found'}), 404

    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    original_filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)

    file.save(filepath)

    attachment = Attachment(
        filename=original_filename,
        filepath=filepath,
        file_type=file.content_type,
        task_id=task.id,
        uploader_id=current_user_id
    )
    try:
        db.session.add(attachment)
        db.session.commit()
    except Exception:
        db.session.rollback()
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': 'Failed to save attachment'}), 500

    return jsonify({
        'id': attachment.id,
        'filename': attachment.filename,
        'file_type': attachment.file_type,
        'uploaded_at': attachment.uploaded_at.isoformat(),
        'uploader_id': attachment.uploader_id
    }), 201

@attachments_bp.route('/tasks/<int:task_id>/attachments', methods=['GET'])
@jwt_required()
def list_attachments(task_id):
    current_user_id = int(get_jwt_identity())

    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    membership = get_membership(task.project_id, current_user_id)
    if not membership:
        return jsonify({'error': 'Task not found'}), 404

    attachments = Attachment.query.filter_by(task_id=task_id).order_by(Attachment.uploaded_at.desc()).all()

    return jsonify([{
        'id': a.id,
        'filename': a.filename,
        'file_type': a.file_type,
        'uploaded_at': a.uploaded_at.isoformat(),
        'uploader_id': a.uploader_id
    } for a in attachments]), 200

@attachments_bp.route('/attachments/<int:attachment_id>/download', methods=['GET'])
@jwt_required()
def download_attachment(attachment_id):
    current_user_id = int(get_jwt_identity())

    attachment = db.session.get(Attachment, attachment_id)
    if not attachment:
        return jsonify({'error': 'Attachment not found'}), 404

    task = attachment.task
    membership = get_membership(task.project_id, current_user_id)
    if not membership:
        return jsonify({'error': 'Attachment not found'}), 404

    return send_file(
        attachment.filepath,
        as_attachment=True,
        download_name=attachment.filename
    )

@attachments_bp.route('/attachments/<int:attachment_id>', methods=['DELETE'])
@jwt_required()
def delete_attachment(attachment_id):
    current_user_id = int(get_jwt_identity())

    attachment = db.session.get(Attachment, attachment_id)
    if not attachment:
        return jsonify({'error': 'Attachment not found'}), 404

    task = attachment.task
    membership = get_membership(task.project_id, current_user_id)
    if not membership:
        return jsonify({'error': 'Attachment not found'}), 404

    if attachment.uploader_id != current_user_id and membership.role != 'owner':
        return jsonify({'error': 'Only the attachment uploader or the project owner can delete this attachment'}), 403

    if os.path.exists(attachment.filepath):
        os.remove(attachment.filepath)

    db.session.delete(attachment)
    db.session.commit()

    return '', 204