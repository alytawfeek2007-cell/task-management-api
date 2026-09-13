import io

def _create_project_and_task(client, auth_headers):
    project_resp = client.post('/api/projects', json={'name': 'P1'}, headers=auth_headers)
    project_id = project_resp.get_json()['id']
    task_resp = client.post(f'/api/projects/{project_id}/tasks', json={'title': 'T1'}, headers=auth_headers)
    task_id = task_resp.get_json()['id']
    return project_id, task_id


def test_upload_attachment_success(client, auth_headers):
    _, task_id = _create_project_and_task(client, auth_headers)

    data = {
        'file': (io.BytesIO(b'fake file content'), 'notes.txt')
    }

    response = client.post(
        f'/api/tasks/{task_id}/attachments',
        data=data,
        content_type='multipart/form-data',
        headers=auth_headers
    )

    assert response.status_code == 201
    assert response.get_json()['filename'] == 'notes.txt'


def test_delete_attachment_by_uploader(client, auth_headers):
    _, task_id = _create_project_and_task(client, auth_headers)

    data = {'file': (io.BytesIO(b'content'), 'file.txt')}
    upload_resp = client.post(
        f'/api/tasks/{task_id}/attachments',
        data=data,
        content_type='multipart/form-data',
        headers=auth_headers
    )
    attachment_id = upload_resp.get_json()['id']

    response = client.delete(f'/api/attachments/{attachment_id}', headers=auth_headers)

    assert response.status_code == 204