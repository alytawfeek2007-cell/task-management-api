from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Project, ProjectMember, User
from app.utils import get_membership

def project_to_dict(project):
    return {
        'id': project.id,
        'name': project.name,
        'description': project.description
    }

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/projects', methods=['POST'])
@jwt_required()
def create_project():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'request body must be valid JSON'}), 400

    name = data.get('name')
    description=data.get('description')

    if not isinstance(name, str) or not name.strip():
        return jsonify({'error': 'name must be a non-empty string'}), 400

    if description is not None and not isinstance(description, str):
        return jsonify({'error': 'description must be a string'}), 400


    current_user_id =int(get_jwt_identity()) 

    new_project = Project(name=name, description=description, owner_id=current_user_id)
    db.session.add(new_project)
    db.session.flush()  

    membership = ProjectMember(
        project_id=new_project.id,
        user_id=current_user_id,
        role='owner'
    )
    db.session.add(membership)
    db.session.commit()

    return jsonify(project_to_dict(new_project)), 201  

@projects_bp.route('/projects', methods=['GET'])
@jwt_required()
def list_projects():
    current_user_id =int(get_jwt_identity()) 

    projects =Project.query.join(ProjectMember).filter(
        ProjectMember.user_id == current_user_id
    ).all()

    result = [project_to_dict(p) for p in projects]
    return jsonify(result), 200

@projects_bp.route('/projects/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    current_user_id = int(get_jwt_identity())

    project = db.session.get(Project, project_id)  
    if project is None:
        return jsonify({'error': 'project not found'}), 404

    membership = get_membership(project_id, current_user_id)  
    if membership is None:
        return jsonify({'error': 'project not found'}), 404  # 404, per the reasoning above

    return jsonify({**project_to_dict(project), 'your_role': membership.role}), 200

@projects_bp.route('/projects/<int:project_id>', methods=['PATCH'])
@jwt_required()
def update_project(project_id):
    current_user_id = int(get_jwt_identity())

    project = db.session.get(Project, project_id)
    if project is None:
        return jsonify({'error': 'project not found'}), 404

    membership = get_membership(project_id, current_user_id)
    if membership is None:
        return jsonify({'error': 'project not found'}), 404

    if membership.role != 'owner':
        return jsonify({'error': 'only owners can update the project'}), 403 

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'request body must be valid JSON'}), 400

    if 'name' in data:
        if not isinstance(data['name'], str) or not data['name'].strip():
            return jsonify({'error': 'name must be a non-empty string'}), 400
        project.name = data['name']

    if 'description' in data:
        if data['description'] is not None and not isinstance(data['description'], str):
            return jsonify({'error': 'description must be a string'}), 400
        project.description = data['description']
        
    db.session.commit()

    return jsonify(project_to_dict(project)), 200

@projects_bp.route('/projects/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    current_user_id = int(get_jwt_identity())

    project = db.session.get(Project, project_id)
    if project is None:
        return jsonify({'error': 'project not found'}), 404

    membership = get_membership(project_id,current_user_id)
    if membership is None:
        return jsonify({'error': 'project not found'}), 404

    if membership.role != 'owner':
        return jsonify({'error': 'only owners can delete the project'}), 403

    db.session.delete(project)
    db.session.commit()

    return '', 204   


@projects_bp.route('/projects/<int:project_id>/members', methods=['POST'])
@jwt_required()
def add_member(project_id):
    current_user_id = int(get_jwt_identity())

    project = db.session.get(Project, project_id)
    if project is None:
        return jsonify({'error': 'project not found'}), 404

    membership = get_membership(project_id, current_user_id)
    if membership is None or membership.role != 'owner':
        return jsonify({'error': 'only owners can add members'}), 403

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'request body must be valid JSON'}), 400

    new_user_id = data.get('user_id')
    role = data.get('role', 'member')

    if not isinstance(new_user_id, int):
        return jsonify({'error': 'user_id must be an integer'}), 400

    if role not in ('owner', 'member'):
        return jsonify({'error': 'role must be owner or member'}), 400

    invited_user = db.session.get(User, new_user_id)
    if invited_user is None:
        return jsonify({'error': 'user not found'}), 404

    existing = get_membership(project_id, new_user_id)
    if existing is not None:
        return jsonify({'error': 'user is already added'}), 409

    new_membership = ProjectMember(
        project_id=project_id,
        user_id=new_user_id,
        role=role
    )
    db.session.add(new_membership)
    db.session.commit()

    return jsonify({
        'user_id': new_membership.user_id,
        'role': new_membership.role
    }), 201

@projects_bp.route('/projects/<int:project_id>/members', methods=['GET'])
@jwt_required()
def list_members(project_id):
    current_user_id = int(get_jwt_identity())

    project = db.session.get(Project, project_id)
    if project is None:
        return jsonify({'error': 'project not found'}), 404

    membership = get_membership(project_id, current_user_id)
    if membership is None:
        return jsonify({'error': 'project not found'}), 404

    members = project.members  

    result = []
    for m in members:
        result.append({
            'user_id': m.user_id,
            'username': m.user.username,  
            'email': m.user.email,
            'role': m.role
        })

    return jsonify(result), 200

@projects_bp.route('/projects/<int:project_id>/members/<int:user_id>', methods=['PATCH'])
@jwt_required()
def update_member_role(project_id, user_id):
    current_user_id = int(get_jwt_identity())

    project = db.session.get(Project, project_id)
    if project is None:
        return jsonify({'error': 'project not found'}), 404

    current_membership = get_membership(project_id, current_user_id)
    if current_membership is None or current_membership.role != 'owner':
        return jsonify({'error': 'only owners can change roles'}), 403

    target_membership = get_membership(project_id, user_id)  
    if target_membership is None:
        return jsonify({'error': 'user not found'}), 404

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'request body must be valid JSON'}), 400
        
    new_role = data.get('role')
    if new_role not in ('owner', 'member'):
        return jsonify({'error': 'role must be owner or member'}), 400

   
    if target_membership.role == 'owner' and new_role != 'owner':
        owner_count = ProjectMember.query.filter_by(
            project_id=project_id,
            role='owner'
        ).count()
        if owner_count == 1:
            return jsonify({'error': 'cannot demote the last owner'}), 400

    target_membership.role = new_role
    db.session.commit()

    return jsonify({
        'user_id': target_membership.user_id,
        'role': target_membership.role
    }), 200


@projects_bp.route('/projects/<int:project_id>/members/<int:user_id>', methods=['DELETE'])
@jwt_required()
def remove_member(project_id, user_id):
    current_user_id = int(get_jwt_identity())

    project = db.session.get(Project, project_id)
    if project is None:
        return jsonify({'error': 'project not found'}), 404

    current_membership = get_membership(project_id, current_user_id)
    if current_membership is None or current_membership.role != 'owner':
        return jsonify({'error': 'only owners can remove members'}), 403

    target_membership = get_membership(project_id, user_id)
    if target_membership is None:
        return jsonify({'error': 'user not found'}), 404

    # last-owner protection: only matters if the person being removed IS an owner
    if target_membership.role == 'owner':
        owner_count = ProjectMember.query.filter_by(
            project_id=project_id,
            role='owner'
        ).count()
        if owner_count == 1:
            return jsonify({'error': 'cannot remove the last owner'}), 400

    db.session.delete(target_membership)
    db.session.commit()

    return '', 204