from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from app.extensions import db, bcrypt
from app.models import User
from sqlalchemy.exc import IntegrityError

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'request body must be valid JSON'}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all(isinstance(v, str) and v.strip() for v in (username, email, password)):
        return jsonify({'error': 'username, email, and password must be non-empty strings'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'username already taken'}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'email already registered'}), 409

    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    new_user = User(username=username, email=email, password_hash=password_hash)

    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'username or email already taken'}), 409


    return jsonify({
        'message': 'user registered successfully',
        'user': {
            'id': new_user.id,
            'username': new_user.username,
            'email': new_user.email
        }
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'request body must be valid JSON'}), 400
        
    email = data.get('email')
    password = data.get('password')

    if not all(isinstance(v, str) and v.strip() for v in (email, password)):
        return jsonify({'error': 'email and password must be non-empty strings'}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({'error': 'invalid email or password'}), 401

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return jsonify({'error': 'user not found'}), 404

    new_access_token = create_access_token(identity=user_id)

    return jsonify({
        'access_token': new_access_token
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return jsonify({'error': 'user not found'}), 404

    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email
    }), 200