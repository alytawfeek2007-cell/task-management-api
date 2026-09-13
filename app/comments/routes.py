from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Comment
from app.utils import get_membership
from app.tasks.routes import get_task_or_404

comments_bp = Blueprint('comments', __name__)

def comment_to_dict(comment):
    return {
        'id': comment.id,
        'content': comment.content,
        'task_id': comment.task_id,
        'author_id': comment.author_id,
        'author_username': comment.author.username,
        'created_at': comment.created_at.isoformat()
    }

@comments_bp.route('/projects/<int:project_id>/tasks/<int:task_id>/comments', methods=['POST'])
@jwt_required()
def create_comment(project_id, task_id):
    task = get_task_or_404(project_id, task_id)
    user_id = int(get_jwt_identity())

    membership = get_membership(project_id, user_id)
    if not membership:
        return jsonify({'error': 'Not a member of this project'}), 403

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid or missing JSON body'}), 400

    content = data.get('content')
    if not isinstance(content, str) or not content.strip():
        return jsonify({'error': 'content is required and must be a non-empty string'}), 400

    comment = Comment(content=content.strip(), task_id=task.id, author_id=user_id)
    db.session.add(comment)
    db.session.commit()

    return jsonify(comment_to_dict(comment)), 201

@comments_bp.route('/projects/<int:project_id>/tasks/<int:task_id>/comments', methods=['GET'])
@jwt_required()
def list_comments(project_id, task_id):
    task = get_task_or_404(project_id, task_id)
    user_id = int(get_jwt_identity())

    membership = get_membership(project_id, user_id)
    if not membership:
        return jsonify({'error': 'Not a member of this project'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    pagination = Comment.query.filter_by(task_id=task.id) \
        .order_by(Comment.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'comments': [comment_to_dict(c) for c in pagination.items],
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total_pages': pagination.pages,
        'total_items': pagination.total
    }), 200

@comments_bp.route('/comments/<int:comment_id>', methods=['PATCH'])
@jwt_required()
def update_comment(comment_id):
    comment = db.session.get(Comment, comment_id)
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404

    user_id = int(get_jwt_identity())

    if comment.author_id != user_id:
        return jsonify({'error': 'Only the comment author can edit this comment'}), 403

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid or missing JSON body'}), 400

    if 'content' in data:
        content = data['content']
        if not isinstance(content, str) or not content.strip():
            return jsonify({'error': 'content must be a non-empty string'}), 400
        comment.content = content.strip()

    db.session.commit()
    return jsonify(comment_to_dict(comment)), 200

@comments_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    comment = db.session.get(Comment, comment_id)
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404

    user_id = int(get_jwt_identity())

    is_author = comment.author_id == user_id
    membership = get_membership(comment.task.project_id, user_id)
    is_owner = membership is not None and membership.role == 'owner'

    if not is_author and not is_owner:
        return jsonify({'error': 'Only the comment author or the project owner can delete this comment'}), 403

    db.session.delete(comment)
    db.session.commit()

    return '', 204    