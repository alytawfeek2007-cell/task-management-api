def test_create_project_success(client, auth_headers):
    response = client.post('/api/projects', json={'name': 'My Project'}, headers=auth_headers)

    assert response.status_code == 201
    assert response.get_json()['name'] == 'My Project'


def test_create_project_missing_name(client, auth_headers):
    response = client.post('/api/projects', json={}, headers=auth_headers)

    assert response.status_code == 400


def test_get_project_as_member(client, auth_headers):
    create_resp = client.post('/api/projects', json={'name': 'P1'}, headers=auth_headers)
    project_id = create_resp.get_json()['id']

    response = client.get(f'/api/projects/{project_id}', headers=auth_headers)

    assert response.status_code == 200
    assert response.get_json()['your_role'] == 'owner'


def test_get_project_as_non_member_returns_404(client, auth_headers, other_auth_headers):
    create_resp = client.post('/api/projects', json={'name': 'P1'}, headers=auth_headers)
    project_id = create_resp.get_json()['id']

    response = client.get(f'/api/projects/{project_id}', headers=other_auth_headers)

    assert response.status_code == 404


def test_update_project_as_owner(client, auth_headers):
    create_resp = client.post('/api/projects', json={'name': 'Old Name'}, headers=auth_headers)
    project_id = create_resp.get_json()['id']

    response = client.patch(f'/api/projects/{project_id}', json={'name': 'New Name'}, headers=auth_headers)

    assert response.status_code == 200
    assert response.get_json()['name'] == 'New Name'


def test_update_project_as_non_owner_forbidden(client, auth_headers, other_auth_headers):
    create_resp = client.post('/api/projects', json={'name': 'P1'}, headers=auth_headers)
    project_id = create_resp.get_json()['id']

    # add other_user as a plain 'member', not owner
    other_login = client.post('/api/login', json={'email': 'other@example.com', 'password': 'pass1234'})
    other_user_id = other_login.get_json()['user']['id']

    client.post(f'/api/projects/{project_id}/members', json={
        'user_id': other_user_id,
        'role': 'member'
    }, headers=auth_headers)

    response = client.patch(f'/api/projects/{project_id}', json={'name': 'Hacked'}, headers=other_auth_headers)

    assert response.status_code == 403


def test_delete_project_as_owner(client, auth_headers):
    create_resp = client.post('/api/projects', json={'name': 'P1'}, headers=auth_headers)
    project_id = create_resp.get_json()['id']

    response = client.delete(f'/api/projects/{project_id}', headers=auth_headers)

    assert response.status_code == 204


def test_add_member_success(client, auth_headers, other_auth_headers):
    create_resp = client.post('/api/projects', json={'name': 'P1'}, headers=auth_headers)
    project_id = create_resp.get_json()['id']

    other_login = client.post('/api/login', json={'email': 'other@example.com', 'password': 'pass1234'})
    other_user_id = other_login.get_json()['user']['id']

    response = client.post(f'/api/projects/{project_id}/members', json={
        'user_id': other_user_id,
        'role': 'member'
    }, headers=auth_headers)

    assert response.status_code == 201
    assert response.get_json()['role'] == 'member'


def test_cannot_demote_last_owner(client, auth_headers):
    create_resp = client.post('/api/projects', json={'name': 'P1'}, headers=auth_headers)
    project_id = create_resp.get_json()['id']

    login_resp = client.post('/api/login', json={'email': 'test@example.com', 'password': 'pass1234'})
    owner_user_id = login_resp.get_json()['user']['id']

    response = client.patch(f'/api/projects/{project_id}/members/{owner_user_id}', json={
        'role': 'member'
    }, headers=auth_headers)

    assert response.status_code == 400