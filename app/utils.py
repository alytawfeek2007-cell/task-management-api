from app.models import ProjectMember

def get_membership(project_id, user_id):
    return ProjectMember.query.filter_by(
        project_id=project_id,
        user_id=user_id
    ).first()