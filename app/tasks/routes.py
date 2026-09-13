from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Project, Task, ProjectMember
from app.utils import get_membership  # reuse helper

def validate_assignee(project_id, assignee_id):
    if assignee_id is None:
        return None

    if not isinstance(assignee_id, int):
        return {'error': 'assignee_id must be an integer'}, 400

    if get_membership(project_id, assignee_id) is None:
        return {'error': 'assignee must be a member of this project'}, 400

    return None

def get_task_or_404(project_id, task_id):
    return Task.query.filter_by(id=task_id, project_id=project_id).first()

VALID_STATUSES = {'todo', 'in_progress', 'done'}
VALID_PRIORITIES = {'low', 'medium', 'high'}


def validate_task_fields(data):
    if 'title' in data:
        if not isinstance(data['title'], str) or not data['title'].strip():
            return {'error': 'title must be a non-empty string'}, 400

    if 'description' in data and data['description'] is not None:
        if not isinstance(data['description'], str):
            return {'error': 'description must be a string'}, 400

    if 'status' in data:
        if not isinstance(data['status'], str) or data['status'] not in VALID_STATUSES:
            return {'error': f'status must be one of {sorted(VALID_STATUSES)}'}, 400

    if 'priority' in data:
        if not isinstance(data['priority'], str) or data['priority'] not in VALID_PRIORITIES:
            return {'error': f'priority must be one of {sorted(VALID_PRIORITIES)}'}, 400

    return None

tasks_bp = Blueprint('tasks', __name__)



def task_to_dict(task):
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'project_id': task.project_id,
        'assignee_id': task.assignee_id,
        'created_at': task.created_at.isoformat(),
    }


@tasks_bp.route('/projects/<int:project_id>/tasks', methods=['POST'])
@jwt_required()
def create_task(project_id):
    user_id = int(get_jwt_identity())
    if get_membership(project_id, user_id) is None:
        return jsonify({'error': 'project not found'}), 404

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'request body must be valid JSON'}), 400

    error = validate_task_fields(data)
    if error:
        body, status = error
        return jsonify(body), status

    title = data.get('title')
    if not title:
        return jsonify({'error': 'title is required'}), 400

    assignee_id = data.get('assignee_id')
    error = validate_assignee(project_id, assignee_id)
    if error:
        body, status = error
        return jsonify(body), status

    task = Task(
        title=title,
        description=data.get('description'),
        status=data.get('status', 'todo'),
        priority=data.get('priority', 'medium'),
        project_id=project_id,
        assignee_id=assignee_id,
        creator_id=user_id,
    )
    db.session.add(task)
    db.session.commit()
    return jsonify(task_to_dict(task)), 201

@tasks_bp.route('/projects/<int:project_id>/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(project_id, task_id):
    user_id = int(get_jwt_identity())
    if get_membership(project_id, user_id) is None:
        return jsonify({'error': 'project not found'}), 404

    task = get_task_or_404(project_id, task_id)
    if task is None:
        return jsonify({'error': 'task not found'}), 404

    return jsonify(task_to_dict(task)), 200

@tasks_bp.route('/projects/<int:project_id>/tasks/<int:task_id>', methods=['PATCH'])
@jwt_required()
def update_task(project_id, task_id):
    user_id = int(get_jwt_identity())
    if get_membership(project_id, user_id) is None:
        return jsonify({'error': 'project not found'}), 404

    task = get_task_or_404(project_id, task_id)
    if task is None:
        return jsonify({'error': 'task not found'}), 404

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'request body must be valid JSON'}), 400

    error = validate_task_fields(data)
    if error:
        body, status = error
        return jsonify(body), status

    if 'assignee_id' in data:
        error = validate_assignee(project_id, data['assignee_id'])
        if error:
            body, status = error
            return jsonify(body), status
        task.assignee_id = data['assignee_id']

    for field in ('title', 'description', 'status', 'priority'):
        if field in data:
            setattr(task, field, data[field])

    db.session.commit()
    return jsonify(task_to_dict(task)), 200

@tasks_bp.route('/projects/<int:project_id>/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(project_id, task_id):
    user_id = int(get_jwt_identity())
    if get_membership(project_id, user_id) is None:
        return jsonify({'error': 'project not found'}), 404

    task = get_task_or_404(project_id, task_id)
    if task is None:
        return jsonify({'error': 'task not found'}), 404

    db.session.delete(task)
    db.session.commit()
    return '', 204

@tasks_bp.route('/projects/<int:project_id>/tasks', methods=['GET'])
@jwt_required()
def list_tasks(project_id):
    user_id = int(get_jwt_identity())
    if get_membership(project_id, user_id) is None:
        return jsonify({'error': 'project not found'}), 404

    query = Task.query.filter_by(project_id=project_id)

    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)

    priority = request.args.get('priority')
    if priority:
        query = query.filter_by(priority=priority)

    assignee_id = request.args.get('assignee_id', type=int)
    if assignee_id:
        query = query.filter_by(assignee_id=assignee_id)

    sort = request.args.get('sort', default='created_at')
    sort_fields = {
        'created_at': Task.created_at,
        'due_date': Task.due_date,
        'priority': Task.priority,
    }
    descending = sort.startswith('-')
    sort_key = sort.lstrip('-')
    column = sort_fields.get(sort_key)
    if column is None:
        return jsonify({'error': 'invalid sort field'}), 400

    if descending:
        query = query.order_by(column.desc())
    else:
        query = query.order_by(column.asc())

    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)
    per_page = min(per_page, 100)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    tasks = pagination.items

    return jsonify({
        'tasks': [task_to_dict(t) for t in tasks],
        'page': pagination.page,
        'per_page': pagination.per_page,
        'total_pages': pagination.pages,
        'total_items': pagination.total
    }), 200