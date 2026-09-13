def test_register_success(client):
    response = client.post('/api/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })

    assert response.status_code == 201

def test_register_duplicate_username(client):
    client.post('/api/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'pass1234'
    })

    response = client.post('/api/register', json={
        'username': 'testuser',   # <- must match the first call's username
        'email': 'testt@example.com',     
        'password': 'pass123'
    })

    assert response.status_code == 409

def test_login_success(client):
    client.post('/api/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'pass1234'
    })

    response = client.post('/api/login', json={
        'email': 'test@example.com',
        'password': 'pass1234'
    })

    assert response.status_code == 200
    assert 'access_token' in response.get_json()

