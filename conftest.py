import pytest
from app import create_app
from app.extensions import db

@pytest.fixture
def app():
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    client.post('/api/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'pass1234'
    })

    response = client.post('/api/login', json={
        'email': 'test@example.com',
        'password': 'pass1234'
    })

    token = response.get_json()['access_token']

    return {'Authorization': f'Bearer {token}'}    

@pytest.fixture
def other_auth_headers(client):
    client.post('/api/register', json={
        'username': 'otheruser',
        'email': 'other@example.com',
        'password': 'pass1234'
    })

    response = client.post('/api/login', json={
        'email': 'other@example.com',
        'password': 'pass1234'
    })

    token = response.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}    