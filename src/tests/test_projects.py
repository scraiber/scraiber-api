from fastapi.testclient import TestClient
import json
from kubernetes import client, config
import os
import time
from typing import List
from pydantic import EmailStr
from fastapi import HTTPException
import uuid

from app.api.models.auth0 import Auth0User
from .helper_functions import (
    generate_user,
    generate_project,
    generate_namespace,
    generate_external
)
from app.main import app
from app.auth0 import current_user

from app.kubernetes_setup import clusters

cluster_name = json.loads(os.environ['CLUSTER_DICT'])["EU1"]["Config-Name"]
config.load_kube_config("config.yaml", context=cluster_name)
v1 = client.CoreV1Api()

user1 = generate_user()
user2 = generate_user()
user_list = [user1, user2]

external1 = generate_external()
external2 = generate_external()

# get_user_by_email = generate_get_user_by_email([user1, user2])
# get_user_by_id = generate_get_user_by_id([user1, user2])


async def get_user_by_email(email: EmailStr) -> Auth0User:
    for user in user_list:
        if user.email == email:
            return user
    raise HTTPException(status_code=404, detail="User could not be retrieved")


async def get_user_by_id(id: str) -> Auth0User:
    for user in user_list:
        if user.user_id == id:
            return user
    raise HTTPException(status_code=404, detail="User could not be retrieved")


async def get_user_list_by_id(id_list: List[str]) -> List[Auth0User]:
    output_list = []
    for user in user_list:
        if user.user_id in id_list:
            output_list.append(user)
    return output_list


project = generate_project()
project2 = project.copy()


namespace1 = generate_namespace()
namespace2 = generate_namespace()
namespace3 = generate_namespace()


def test_project_create(client: TestClient, session):
    session.execute('SELECT COUNT(*) FROM public.projects')
    old_number = session.fetchone()[0]
    # Create project without e-mail verified - should fail
    app.dependency_overrides[current_user] = lambda: user1.copy(update={"is_verified": False})
    response = client.post('projects/', data=json.dumps(project))

    assert response.status_code == 401
    session.execute('SELECT COUNT(*) FROM public.projects')
    assert session.fetchone()[0] == old_number

    # Create project with e-mail verified - should work
    app.dependency_overrides = {current_user: lambda: user1}
    response = client.post('projects/', data=json.dumps(project))
    project.update({"project_id": response.json()["project_id"]})
    assert response.status_code == 201
    session.execute('SELECT COUNT(*) FROM public.projects')
    assert session.fetchone()[0] == old_number + 1

    response2 = client.post('projects/', data=json.dumps(project))
    project2.update({"project_id": response2.json()["project_id"]})
    assert response2.status_code == 201
    session.execute('SELECT COUNT(*) FROM public.projects')
    assert session.fetchone()[0] == old_number + 2


def test_project_get(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.get_user_list_by_id", get_user_list_by_id)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.namespaces.get_user_list_by_id", get_user_list_by_id)

    app.dependency_overrides = {current_user: lambda: user1}

    data = {"project_id": project["project_id"]}
    response = client.get('projects/', data=json.dumps(data))

    assert response.status_code == 200
    assert response.json()["project_id"] == project["project_id"]
    assert response.json()["name"] == project["name"]
    assert len(response.json()["namespaces"]) == 0
    assert len(response.json()["users"]) == 1
    assert len(response.json()["user_candidates"]) == 0
    assert len(response.json()["externals"]) == 0

    response = v1.list_namespace()
    namespaces_names = [item.metadata.name for item in response.items]
    assert (namespace1["name"] in namespaces_names) == False
    assert (namespace2["name"] in namespaces_names) == False

    response = client.post("project_user_management/", data=json.dumps({"project_id": project["project_id"], "e_mail": external1["e_mail"]}))
    response = client.post("project_user_management/", data=json.dumps({"project_id": project["project_id"], "e_mail": external2["e_mail"]}))
    response = client.post("project_user_management/", data=json.dumps({"project_id": project["project_id"], "e_mail": user2.email}))
    namespace1.update({"project_id": project["project_id"]})
    response = client.post("namespaces/", data=json.dumps(namespace1))
    namespace2.update({"project_id": project["project_id"]})
    response = client.post("namespaces/", data=json.dumps(namespace2))

    #add namespace 3 to project 2
    namespace3.update({"project_id": project2["project_id"]})
    response = client.post("namespaces/", data=json.dumps(namespace3))


    data_transfer = {"name": namespace1["name"], "region": namespace1["region"], "old_project_id": project["project_id"],
             "new_project_id": project2["project_id"]}
    response = client.post('namespace2projecttransfer/', data=json.dumps(data_transfer))

    data_transfer = {"name": namespace3["name"], "region": namespace3["region"], "old_project_id": project2["project_id"],
                     "new_project_id": project["project_id"]}
    response = client.post('namespace2projecttransfer/', data=json.dumps(data_transfer))

    response = client.get('projects/', data=json.dumps(data))

    assert response.status_code == 200
    assert response.json()["project_id"] == project["project_id"]
    assert response.json()["name"] == project["name"]
    assert len(response.json()["namespaces"]) == 2
    assert len(response.json()["users"]) == 1
    assert len(response.json()["externals"]) == 2
    assert len(response.json()["user_candidates"]) == 1
    assert len(response.json()["transfer_source_namespace"]) == 1
    assert len(response.json()["transfer_target_namespace"]) == 1

    session.execute("SELECT COUNT(*) FROM public.projects WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 1
    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 2
    session.execute("SELECT COUNT(*) FROM public.project2user WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 1
    session.execute("SELECT COUNT(*) FROM public.project2usercandidate WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 1
    session.execute("SELECT COUNT(*) FROM public.project2external WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 2
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE old_project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 1
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE new_project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 1

    response = v1.list_namespace()
    namespaces_names = [item.metadata.name for item in response.items]
    assert (namespace1["name"] in namespaces_names) == True
    assert (namespace2["name"] in namespaces_names) == True
    assert (namespace3["name"] in namespaces_names) == True

    # non-existent project
    data = {"project_id": str(uuid.uuid4())}
    response = client.get('projects/', data=json.dumps(data))
    assert response.status_code == 404

    # unassociated user
    app.dependency_overrides[current_user] = lambda: user2.copy(update={"is_verified": False})
    data = {"project_id": project["project_id"]}
    response = client.get('projects/', data=json.dumps(data))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides[current_user] = lambda: user2
    response = client.get('projects/', data=json.dumps(data))
    assert response.status_code == 404
    # wrong token
    app.dependency_overrides = {}
    response = client.get('projects/', data=json.dumps(data))
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_project_get_by_user(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.get_user_list_by_id", get_user_list_by_id)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)

    session.execute("SELECT COUNT(*) FROM public.project2user WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 1

    # Check for user 2, when unverified - should throw error
    app.dependency_overrides = {current_user: lambda: user2.copy(update={"is_verified": False})}
    response = client.get('projects/by_user')
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    # Check for user 2 - should throw error
    app.dependency_overrides = {current_user: lambda: user2}
    response = client.get('projects/by_user')
    assert response.status_code == 404
    # Assign user 2 to project 1
    app.dependency_overrides[current_user] = lambda: user2
    response = client.post('project_user_management/accept_user_invitation',
                           data=json.dumps(
                               {"project_id": project["project_id"]}))

    session.execute("SELECT COUNT(*) FROM public.project2usercandidate WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.project2user WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 2

    # Check for user 1
    app.dependency_overrides[current_user] = lambda: user1
    response = client.get('projects/by_user')
    assert response.status_code == 200
    assert len(response.json()) == 2
    response = client.get('projects/by_user?admin_state=True')
    assert response.status_code == 200
    assert len(response.json()) == 2
    # Check for user 2 again
    app.dependency_overrides = {current_user: lambda: user2}
    response = client.get('projects/by_user')
    assert response.status_code == 200
    assert len(response.json()) == 1
    response = client.get('projects/by_user?admin_state=True')
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_project_update_name(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.get_user_list_by_id", get_user_list_by_id)

    app.dependency_overrides = {current_user: lambda: user1.copy(update={"is_verified": False})}
    data = {"name": project["name"]+"_new", "project_id": project["project_id"]}
    response = client.put('projects/name', data=json.dumps(data))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides = {current_user: lambda: user1}
    data = {"name": project["name"]+"_new", "project_id": project["project_id"]}
    response = client.put('projects/name', data=json.dumps(data))
    assert response.status_code == 200
    assert response.json()["name"] == project["name"]+"_new"

    session.execute("SELECT name FROM public.projects WHERE project_id='" + project["project_id"] + "'")
    new_name = session.fetchone()[0]
    assert new_name == project["name"]+"_new"
    # wrong token
    app.dependency_overrides = {}
    response = client.put('projects/name', data=json.dumps(data))
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_delete(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.get_user_list_by_id", get_user_list_by_id)

    session.execute("SELECT COUNT(*) FROM public.projects")
    current_no = session.fetchone()[0]

    data = {"project_id": project["project_id"]}

    app.dependency_overrides = {current_user: lambda: user1.copy(update={"is_verified": False})}
    response = client.delete('projects/', data=json.dumps(data))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides = {current_user: lambda: user1}
    response = client.delete('projects/', data=json.dumps(data))
    assert response.status_code == 200
    assert response.json() == data

    data2 = {"project_id": project2["project_id"]}
    response = client.delete('projects/', data=json.dumps(data2))

    time.sleep(10)
    response = v1.list_namespace()
    namespaces_names = [item.metadata.name for item in response.items]
    assert (namespace1["name"] in namespaces_names) == False
    assert (namespace2["name"] in namespaces_names) == False
    assert (namespace3["name"] in namespaces_names) == False

    session.execute('SELECT COUNT(*) FROM public.projects')
    assert session.fetchone()[0] == current_no - 2

    session.execute("SELECT COUNT(*) FROM public.projects WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.project2user WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.project2usercandidate WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.project2external WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE old_project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE new_project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 0

    # wrong token
    app.dependency_overrides = {}
    response = client.delete('projects/', data=json.dumps(data))
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
