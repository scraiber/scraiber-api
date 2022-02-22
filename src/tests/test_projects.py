from fastapi.testclient import TestClient
import json
from kubernetes import client, config
import os
import time
from typing import List
from pydantic import EmailStr

from app.api.models.auth0 import Auth0User
from .helper_functions import (
    generate_user, 
    generate_project, 
    generate_project_blacklist, 
    mock_mail_project_post, 
    mock_mail_project_put, 
    mock_mail_project_delete,
    mock_mail_um_post_internal,
    mock_mail_um_post_internal_owner,
    mock_mail_um_post_external
)
from app.main import app
from app.auth0 import current_user

from app.kubernetes_setup import clusters


cluster_name = json.loads(os.environ['CLUSTER_DICT'])["EU1"]["Config-Name"]
config.load_kube_config("config.yaml", context=cluster_name)
v1=client.CoreV1Api()



user1 = generate_user()
user2 = generate_user()
user_list = [user1, user2]


#get_user_by_email = generate_get_user_by_email([user1, user2])
#get_user_by_id = generate_get_user_by_id([user1, user2])


async def get_user_by_email(email: EmailStr) -> Auth0User:
    for user in user_list:
        if user.email == email:
            return user

async def get_user_by_id(id: str) -> Auth0User:
    for user in user_list:
        if user.user_id == id:
            return user

async def get_user_list_by_id(id_list: List[str]) -> List[Auth0User]:
    output_list = []
    for user in user_list:
        if user.user_id in id_list:
            output_list.append(user)
    return output_list

project = generate_project()



def test_project_create(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.projects.mail_project_post", mock_mail_project_post)

    session.execute('SELECT COUNT(*) FROM public.projects')
    old_number = session.fetchone()[0]

    response = v1.list_namespace()
    names = [item.metadata.name for item in response.items]
    assert (project["name"] in names) == False

    #Create project without e-mail verified - should fail
    app.dependency_overrides[current_user] = lambda: user1
    response = client.post('projects/', data=json.dumps(project))
    assert response.status_code == 401
    session.execute('SELECT COUNT(*) FROM public.projects')
    assert session.fetchone()[0] == old_number
    response = v1.list_namespace()
    names = [item.metadata.name for item in response.items]
    assert (project["name"] in names) == False

    #Create project with e-mail verified but in blacklist - should fail
    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1.copy(update={"is_verified": True})
    blacklist_name = clusters["EU1"]["blacklist"][0]
    response = client.post('projects/', data=json.dumps(generate_project_blacklist(blacklist_name)))
    assert response.status_code == 403
    session.execute('SELECT COUNT(*) FROM public.projects')
    assert session.fetchone()[0] == old_number
    response = v1.list_namespace()
    names = [item.metadata.name for item in response.items]
    assert (blacklist_name in names) == True

    #Create project with e-mail verified - should work
    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1.copy(update={"is_verified": True})
    response = client.post('projects/', data=json.dumps(project))
    assert response.status_code == 201
    session.execute('SELECT COUNT(*) FROM public.projects')
    assert session.fetchone()[0] == old_number+1
    response = v1.list_namespace()
    names = [item.metadata.name for item in response.items]
    assert (project["name"] in names) == True

    rq_json = v1.read_namespaced_resource_quota(name="resource-quota-for-"+project["name"], namespace=project["name"]).status.hard
    lr_json = v1.read_namespaced_limit_range(name="limit-range-for-"+project["name"], namespace=project["name"]).spec.limits[0].default
    assert rq_json == {'limits.cpu': '10', 'limits.memory': '512Mi'}
    assert lr_json == {'cpu': '100m', 'memory': '64Mi'}

    response2 = client.post('projects/', data=json.dumps(project))
    assert response2.status_code == 403
    session.execute('SELECT COUNT(*) FROM public.projects')
    assert session.fetchone()[0] == old_number+1


def test_project_get(client: TestClient):
    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    data = {"name": project["name"], "region": project["region"]}
    response = client.get('projects/', data=json.dumps(data))
    assert response.status_code == 200
    test_json = project.copy()
    test_json.update({"owner_id": user1.user_id})
    assert response.json() == test_json

    #non-existent project
    data = {"name": project["name"]+"a", "region": project["region"]}
    response = client.get('projects/', data=json.dumps(data))
    assert response.status_code == 404

    #unassociated user
    app.dependency_overrides[current_user] = lambda: user2
    data = {"name": project["name"], "region": project["region"]}
    response = client.get('projects/', data=json.dumps(data))
    assert response.status_code == 404

    #wrong token
    app.dependency_overrides = {}
    response = client.get('projects/', data=json.dumps(data))
    assert response.status_code == 401
    assert response.json() == {"detail":"Not authenticated"}


def test_project_get_by_user(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.mail_um_post_internal", mock_mail_um_post_internal)
    monkeypatch.setattr("app.api.routes.user_management.mail_um_post_internal_owner", mock_mail_um_post_internal_owner)
    monkeypatch.setattr("app.api.routes.user_management.mail_um_post_external", mock_mail_um_post_external)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)

    session.execute("SELECT COUNT(*) FROM public.project2user WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 1

    #Check for user 2 - should throw error
    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user2
    response = client.get('projects/by_user')
    assert response.status_code == 404

    #Assign user 2 to project 1
    app.dependency_overrides[current_user] = lambda: user1
    response = client.post('project_user_management/',
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user2.email}))
    assert response.status_code == 201
    session.execute("SELECT COUNT(*) FROM public.project2user WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 2

    #Check for user 1
    response = client.get('projects/by_user')
    assert response.status_code == 200
    assert len(response.json()) == 1
    #Check for user 2 again
    response = client.get('projects/by_user')
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_project_get_by_owner(client: TestClient):
    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    response = client.get('projects/by_owner')
    assert response.status_code == 200
    test_json = project.copy()
    test_json.update({"owner_id": user1.user_id})
    assert response.json()[0] == test_json
    assert len(response.json()) == 1

    #Check for user 2
    app.dependency_overrides[current_user] = lambda: user2
    response = client.get('projects/by_owner')
    assert response.status_code == 404

    #wrong token
    app.dependency_overrides = {}
    response = client.get('projects/by_owner')
    assert response.status_code == 401
    assert response.json() == {"detail":"Not authenticated"}


def test_project_update_cpu_memory(client: TestClient, monkeypatch):
    monkeypatch.setattr("app.api.routes.projects.mail_project_put", mock_mail_project_put)
    monkeypatch.setattr("app.api.routes.user_management.get_user_list_by_id", get_user_list_by_id)

    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    data = {"name": project["name"], "region": project["region"], "max_project_cpu": 20, "max_project_mem": 1024, "default_limit_pod_cpu": 0.2, "default_limit_pod_mem": 128}
    response = client.put('projects/update_cpu_memory', data=json.dumps(data))
    assert response.status_code == 200
    test_json = project.copy()
    test_json.update({"max_project_cpu": 20, "max_project_mem": 1024, "default_limit_pod_cpu": 0.2, "default_limit_pod_mem": 128})
    assert response.json() == test_json

    rq_json = v1.read_namespaced_resource_quota(name="resource-quota-for-"+project["name"], namespace=project["name"]).status.hard
    lr_json = v1.read_namespaced_limit_range(name="limit-range-for-"+project["name"], namespace=project["name"]).spec.limits[0].default
    assert rq_json == {'limits.cpu': '20', 'limits.memory': '1Gi'}
    assert lr_json == {'cpu': '200m', 'memory': '128Mi'}

    #wrong token
    app.dependency_overrides = {}
    response = client.put('projects/update_cpu_memory', data=json.dumps(data))
    assert response.status_code == 401
    assert response.json() == {"detail":"Not authenticated"}


def test_delete(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.projects.mail_project_delete", mock_mail_project_delete)
    monkeypatch.setattr("app.api.routes.user_management.get_user_list_by_id", get_user_list_by_id)

    session.execute('SELECT COUNT(*) FROM public.projects')
    current_no = session.fetchone()[0]

    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    data = {"name": project["name"], "region": project["region"]}
    response = client.delete('projects/', data=json.dumps(data))
    assert response.status_code == 200
    assert response.json() == data

    session.execute('SELECT COUNT(*) FROM public.projects')
    assert session.fetchone()[0] == current_no-1

    #check if no namespace remains
    time.sleep(10)
    response = v1.list_namespace()
    names = [item.metadata.name for item in response.items]
    assert (project["name"] in names) == False
    
    #wrong token
    app.dependency_overrides = {}
    response = client.delete('projects/', data=json.dumps(data))
    assert response.status_code == 401
    assert response.json() == {"detail":"Not authenticated"}    