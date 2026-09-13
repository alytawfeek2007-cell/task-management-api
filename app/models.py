from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc)
from app.extensions import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)     
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    owned_projects = db.relationship('Project', backref='owner', lazy=True)
    project_memberships = db.relationship('ProjectMember', backref='user', lazy=True)

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    members = db.relationship('ProjectMember', backref='project', cascade='all, delete-orphan', lazy=True)
    tasks = db.relationship('Task', backref='project', cascade='all, delete-orphan', lazy=True)

class ProjectMember(db.Model):
    __tablename__ = 'project_members'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'owner' or 'member'
    joined_at = db.Column(db.DateTime, default=utcnow)

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='todo')
    priority = db.Column(db.String(20), nullable=False, default='medium')
    due_date = db.Column(db.DateTime, nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    assignee = db.relationship('User', foreign_keys=[assignee_id], backref='assigned_tasks', lazy=True)
    creator = db.relationship('User', foreign_keys=[creator_id], backref='created_tasks', lazy=True)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)    
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    task = db.relationship('Task', backref=db.backref('comments', cascade='all, delete-orphan'), lazy=True)
    author = db.relationship('User', backref='comments', lazy=True)

class Attachment(db.Model):  
    __tablename__ = 'attachments'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=utcnow)
    task = db.relationship('Task', backref=db.backref('attachments', cascade='all, delete-orphan'), lazy=True)
    uploader = db.relationship('User', backref='attachments', lazy=True)