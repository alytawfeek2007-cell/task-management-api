def _create_project_and_task(client, auth_headers):
    project_resp = client.post('/api/projects', json={'name': 'P1'}, headers=auth_headers)
    project_id = project_resp.get_json()['id']
    task_resp = client.post(f'/api/projects/{project_id}/tasks', json={'title': 'T1'}, headers=auth_headers)
    task_id = task_resp.get_json()['id']
    return project_id, task_id


def test_create_comment_success(client, auth_headers):
    project_id, task_id = _create_project_and_task(client, auth_headers)

    response = client.post(
        f'/api/projects/{project_id}/tasks/{task_id}/comments',
        json={'content': 'Looks good'},
        headers=auth_headers
    )

    assert response.status_code == 201
    assert response.get_json()['content'] == 'Looks good'


def test_update_comment_non_author_forbidden(client, auth_headers, other_auth_headers):
    project_id, task_id = _create_project_and_task(client, auth_headers)

    create_resp = client.post(
        f'/api/projects/{project_id}/tasks/{task_id}/comments',
        json={'content': 'Original'},
        headers=auth_headers
    )
    comment_id = create_resp.get_json()['id']

    response = client.patch(
        f'/api/comments/{comment_id}',
        json={'content': 'Hacked'},
        headers=other_auth_headers
    )

    assert response.status_code == 403


def test_delete_comment_by_non_author_non_owner_forbidden(client, auth_headers, other_auth_headers):
    project_id, task_id = _create_project_and_task(client, auth_headers)

    create_resp = client.post(
        f'/api/projects/{project_id}/tasks/{task_id}/comments',
        json={'content': 'Original'},
        headers=auth_headers
    )
    comment_id = create_resp.get_json()['id']

    response = client.delete(f'/api/comments/{comment_id}', headers=other_auth_headers)

    assert response.status_code == 403