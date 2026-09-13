import os
from flask import Flask, jsonify
from config import config
from app.extensions import db, jwt, bcrypt, migrate

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)  

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) 

    from app.auth.routes import auth_bp
    from app.projects.routes import projects_bp
    from app.tasks.routes import tasks_bp
    from app.comments.routes import comments_bp
    from app.tasks.attachments.routes import attachments_bp

    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(projects_bp, url_prefix='/api')
    app.register_blueprint(tasks_bp, url_prefix='/api')
    app.register_blueprint(comments_bp, url_prefix='/api')
    app.register_blueprint(attachments_bp, url_prefix='/api')   

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'An internal error occurred'}), 500

    return app