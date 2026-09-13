def test_create_task_success(client, auth_headers):
    project_resp = client.post('/api/projects', json={'name': 'P1'}, headers=auth_headers)
    project_id = project_resp.get_json()['id']

    response = client.post(f'/api/projects/{project_id}/tasks', json={
        'title': 'Fix bug'
    }, headers=auth_headers)

    assert response.status_code == 201
    assert response.get_json()['status'] == 'todo'


def test_create_task_invalid_status(client, auth_headers):
    project_resp = client.post('/api/projects', json={'name': 'P1'}, headers=auth_headers)
    project_id = project_resp.get_json()['id']

    response = client.post(f'/api/projects/{project_id}/tasks', json={
        'title': 'Fix bug',
        'status': 'not_a_real_status'
    }, headers=auth_headers)

    assert response.status_code == 400


def test_create_task_non_member_gets_404(client, auth_headers, other_auth_headers):
    project_resp = client.post('/api/projects', json={'name': 'P1'}, headers=auth_headers)
    project_id = project_resp.get_json()['id']

    response = client.post(f'/api/projects/{project_id}/tasks', json={
        'title': 'Sneaky task'
    }, headers=other_auth_headers)

    assert response.status_code == 404


def test_list_tasks_filter_by_status(client, auth_headers):
    project_resp = client.post('/api/projects', json={'name': 'P1'}, headers=auth_headers)
    project_id = project_resp.get_json()['id']

    client.post(f'/api/projects/{project_id}/tasks', json={'title': 'A', 'status': 'done'}, headers=auth_headers)
    client.post(f'/api/projects/{project_id}/tasks', json={'title': 'B', 'status': 'todo'}, headers=auth_headers)

    response = client.get(f'/api/projects/{project_id}/tasks?status=done', headers=auth_headers)
    data = response.get_json()

    assert response.status_code == 200
    assert len(data['tasks']) == 1
    assert data['tasks'][0]['title'] == 'A'