import uuid
from kubernetes import client, config
import os
from fastapi.testclient import TestClient
import json
from typing import List
from pydantic import EmailStr
from fastapi import HTTPException

from app.api.models.auth0 import Auth0User

from .helper_functions import (
    generate_user, 
    generate_project,
    generate_namespace
)
from app.main import app
from app.auth0 import current_user

cluster_name = json.loads(os.environ['CLUSTER_DICT'])["EU1"]["Config-Name"]
config.load_kube_config("config.yaml", context=cluster_name)
rbac = client.RbacAuthorizationV1Api()

user1 = generate_user()
user2 = generate_user()
user3 = generate_user()
user4 = generate_user()
user5 = generate_user()

user_list1 = [user1, user2, user3]
user_list2 = [user4, user5]

namespace1 = generate_namespace()
namespace2 = generate_namespace()


async def get_user_by_email(email: EmailStr) -> Auth0User:
    for user in user_list1:
        if user.email == email:
            return user
    raise HTTPException(status_code=404, detail="User could not be retrieved")


async def get_user_by_id(id: str) -> Auth0User:
    for user in user_list1:
        if user.user_id == id:
            return user
    raise HTTPException(status_code=404, detail="User could not be retrieved")


async def get_user_list_by_id(id_list: List[str]) -> List[Auth0User]:
    output_list = []
    for user in user_list1:
        if user.user_id in id_list:
            output_list.append(user)
    return output_list

project = generate_project()
project2 = generate_project()



def test_user_add(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)
    monkeypatch.setattr("app.api.routes.namespaces.get_user_by_id", get_user_by_id)
    monkeypatch.setattr("app.api.routes.namespaces.get_user_list_by_id", get_user_list_by_id)

    #create project 1
    app.dependency_overrides[current_user] = lambda: user1
    response = client.post('projects/', data=json.dumps(project))
    project.update({"project_id": response.json()["project_id"]})
    #create project 2
    response = client.post('projects/', data=json.dumps(project2))
    project2.update({"project_id": response.json()["project_id"]})

    namespace1.update({"project_id": project["project_id"]})
    response = client.post("namespaces/", data=json.dumps(namespace1))
    namespace2.update({"project_id": project2["project_id"]})
    response = client.post("namespaces/", data=json.dumps(namespace2))

    session.execute("SELECT COUNT(*) FROM public.project2user WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 1
    session.execute("SELECT COUNT(*) FROM public.project2usercandidate WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 0

    app.dependency_overrides = {current_user: lambda: user1.copy(update={"is_verified": False})}
    response = client.post('project_user_management/',
                           data=json.dumps({"project_id": project["project_id"], "e_mail": user2.email}))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    #Assign user 2 to project 1
    app.dependency_overrides = {current_user: lambda: user1}
    response = client.post('project_user_management/',
        data=json.dumps({"project_id": project["project_id"], "e_mail": user2.email}))
    assert response.status_code == 201
    session.execute("SELECT COUNT(*) FROM public.project2user WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 1
    session.execute("SELECT COUNT(*) FROM public.project2usercandidate WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 1

    response = client.post('project_user_management/',
        data=json.dumps({"project_id": project["project_id"], "e_mail": user2.email}))
    assert response.status_code == 403

    app.dependency_overrides[current_user] = lambda: user2
    response = client.post('project_user_management/',
        data=json.dumps({"project_id": project["project_id"], "e_mail": user4.email}))
    assert response.status_code == 401
    assert response.json()["detail"] == "Project for user not found or user not admin"

    session.execute("SELECT COUNT(*) FROM public.project2external WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 0

    app.dependency_overrides[current_user] = lambda: user1
    response = client.post('project_user_management/',
        data=json.dumps({"project_id": project["project_id"], "e_mail": user4.email}))
    assert response.status_code == 201
    session.execute("SELECT COUNT(*) FROM public.project2external WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 1

    role_bindings = rbac.list_namespaced_role_binding(namespace1["name"])
    assert len(role_bindings.items) == 1
    role_bindings = rbac.list_namespaced_role_binding(namespace2["name"])
    assert len(role_bindings.items) == 1



def test_accept_user_invitation(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)

    #Assign user 2 to project 1
    app.dependency_overrides = {current_user: lambda: user3.copy(update={"is_verified": False})}
    response = client.post('project_user_management/accept_user_invitation',
                           data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides = {current_user: lambda: user3}
    response = client.post('project_user_management/accept_user_invitation',
                           data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 404

    app.dependency_overrides = {current_user: lambda: user2.copy(update={"is_verified": False})}
    response = client.post('project_user_management/accept_user_invitation',
                           data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    role_bindings = rbac.list_namespaced_role_binding(namespace1["name"])
    assert len(role_bindings.items) == 1
    role_bindings = rbac.list_namespaced_role_binding(namespace2["name"])
    assert len(role_bindings.items) == 1

    app.dependency_overrides = {current_user: lambda: user2}
    response = client.post('project_user_management/accept_user_invitation',
                           data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 201

    role_bindings = rbac.list_namespaced_role_binding(namespace1["name"])
    assert len(role_bindings.items) == 2
    role_bindings = rbac.list_namespaced_role_binding(namespace2["name"])
    assert len(role_bindings.items) == 1

    session.execute("SELECT COUNT(*) FROM public.project2user WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 2
    session.execute("SELECT COUNT(*) FROM public.project2usercandidate WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 0


def test_get_externals_by_project(client: TestClient):
    app.dependency_overrides = {current_user: lambda: user3.copy(update={"is_verified": False})}
    response = client.get('project_user_management/externals_by_project',
                          data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides = {current_user: lambda: user3}
    response = client.get('project_user_management/externals_by_project',
                          data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 404

    app.dependency_overrides = {current_user: lambda: user2}
    response = client.get('project_user_management/externals_by_project',
                          data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 200
    test_json = {"project_id": project["project_id"], "e_mail": user4.email, "is_admin": False}
    assert response.json()[0] == test_json
    assert len(response.json()) == 1

    app.dependency_overrides = {current_user: lambda: user1}
    response = client.get('project_user_management/externals_by_project',
                          data=json.dumps({"project_id": project2["project_id"]}))
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_get_invited_users_by_project(client: TestClient, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)
    monkeypatch.setattr("app.api.routes.user_management.get_user_list_by_id", get_user_list_by_id)

    app.dependency_overrides = {current_user: lambda: user1}
    response = client.post('project_user_management/',
                           data=json.dumps({"project_id": project["project_id"], "e_mail": user3.email}))
    assert response.status_code == 201

    app.dependency_overrides = {current_user: lambda: user3.copy(update={"is_verified": False})}
    response = client.get('project_user_management/invited_users_by_project',
                          data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides = {current_user: lambda: user3}
    response = client.get('project_user_management/invited_users_by_project',
                          data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 404

    app.dependency_overrides = {current_user: lambda: user2}
    response = client.get('project_user_management/invited_users_by_project',
                          data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 200
    assert response.json()[0]["sub"] == user3.user_id
    assert len(response.json()) == 1

    app.dependency_overrides = {current_user: lambda: user1}
    response = client.get('project_user_management/invited_users_by_project',
                          data=json.dumps({"project_id": project2["project_id"]}))
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_get_users_by_project(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.get_user_list_by_id", get_user_list_by_id)

    app.dependency_overrides = {current_user: lambda: user1.copy(update={"is_verified": False})}
    response = client.get('project_user_management/users_by_project',
                          data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    session.execute("SELECT COUNT(*) FROM public.project2user WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 2

    app.dependency_overrides = {current_user: lambda: user1}
    response = client.get('project_user_management/users_by_project',
                          data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 200
    assert len(response.json()) == 2

    session.execute("SELECT COUNT(*) FROM public.project2user WHERE project_id='"+project2["project_id"]+"'")
    assert session.fetchone()[0] == 1

    response = client.get('project_user_management/users_by_project',
                          data=json.dumps({"project_id": project2["project_id"]}))
    assert response.status_code == 200
    assert len(response.json()) == 1

    app.dependency_overrides = {current_user: lambda: user2}
    response = client.get('project_user_management/users_by_project',
                          data=json.dumps({"project_id": project2["project_id"]}))
    assert response.status_code == 404


def test_put_admin_state(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)

    app.dependency_overrides = {current_user: lambda: user2.copy(update={"is_verified": False})}
    response = client.put('project_user_management/admin_state',
                          data=json.dumps({"project_id": project["project_id"], "user_id": user1.user_id, "is_admin": False}))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides = {current_user: lambda: user2}
    response = client.put('project_user_management/admin_state',
        data=json.dumps({"project_id": project["project_id"], "user_id": user1.user_id, "is_admin": False}))
    assert response.status_code == 401
    assert response.json()["detail"] == "Project for user not found or user not admin"

    app.dependency_overrides = {current_user: lambda: user1}
    response = client.put('project_user_management/admin_state',
                          data=json.dumps({"project_id": str(uuid.uuid4()), "user_id": user2.user_id, "is_admin": True}))
    assert response.status_code == 401
    assert response.json()["detail"] == "Project for user not found or user not admin"

    response = client.put('project_user_management/admin_state',
        data=json.dumps({"project_id": project["project_id"], "user_id": user2.user_id, "is_admin": True}))
    assert response.status_code == 200

    session.execute("SELECT is_admin FROM public.project2user WHERE project_id='"+project["project_id"]+"' AND user_id='"+user2.user_id +"'")
    assert session.fetchone()[0] == True

    app.dependency_overrides[current_user] = lambda: user2
    response = client.put('project_user_management/admin_state',
        data=json.dumps({"project_id": project["project_id"], "user_id": user1.user_id, "is_admin": True}))
    assert response.status_code == 403
    assert response.json()["detail"] == "Admin state would not change"

    response = client.put('project_user_management/admin_state',
                          data=json.dumps({"project_id": project["project_id"], "user_id": user1.user_id, "is_admin": False}))
    assert response.status_code == 200
    session.execute("SELECT is_admin FROM public.project2user WHERE project_id='"+project["project_id"]+"' AND user_id='"+user1.user_id +"'")
    assert session.fetchone()[0] == False

    app.dependency_overrides[current_user] = lambda: user1
    response = client.put('project_user_management/admin_state',
        data=json.dumps({"project_id": project2["project_id"], "user_id": user2.user_id, "is_admin": True}))
    assert response.status_code == 404

    response = client.put('project_user_management/admin_state',
                          data=json.dumps({"project_id": project2["project_id"], "user_id": user1.user_id, "is_admin": False}))
    assert response.status_code == 403
    assert response.json()["detail"] == "There has to be at least one admin"


def test_delete_external_from_project(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)

    session.execute("SELECT COUNT(*) FROM public.project2external WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 1

    app.dependency_overrides = {current_user: lambda: user1.copy(update={"is_verified": False})}
    response = client.delete('project_user_management/external_from_project',
                             data=json.dumps({"project_id": project["project_id"], "e_mail": user4.email}))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides = {current_user: lambda: user1}
    response = client.delete('project_user_management/external_from_project',
        data=json.dumps({"project_id": project["project_id"], "e_mail": user4.email}))
    assert response.status_code == 401
    assert response.json()["detail"] == "Project for user not found or user not admin"

    session.execute("SELECT COUNT(*) FROM public.project2external WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 1

    app.dependency_overrides = {current_user: lambda: user2}
    response = client.delete('project_user_management/external_from_project',
                             data=json.dumps({"project_id": project["project_id"], "e_mail": user4.email}))
    assert response.status_code == 200

    session.execute("SELECT COUNT(*) FROM public.project2external WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 0


def test_delete_all_externals_from_project(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)

    session.execute("SELECT COUNT(*) FROM public.project2external WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 0    

    app.dependency_overrides = {current_user: lambda: user2}
    response = client.post('project_user_management/',
        data=json.dumps({"project_id": project["project_id"], "e_mail": user4.email}))
    assert response.status_code == 201
    response = client.post('project_user_management/',
        data=json.dumps({"project_id": project["project_id"], "e_mail": user5.email}))
    assert response.status_code == 201
    session.execute("SELECT COUNT(*) FROM public.project2external WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 2

    app.dependency_overrides = {current_user: lambda: user2.copy(update={"is_verified": False})}
    response = client.delete('project_user_management/all_externals_from_project',
                             data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides = {current_user: lambda: user2}
    response = client.delete('project_user_management/all_externals_from_project',
        data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 200

    session.execute("SELECT COUNT(*) FROM public.project2external WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 0


def test_delete_user_from_project(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)

    app.dependency_overrides = {current_user: lambda: user1.copy(update={"is_verified": False})}
    response = client.delete('project_user_management/user_from_project',
                             data=json.dumps({"project_id": str(uuid.uuid4()), "user_id": user2.user_id}))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    #Delete non-existent project
    app.dependency_overrides = {current_user: lambda: user1}
    response = client.delete('project_user_management/user_from_project',
        data=json.dumps({"project_id": str(uuid.uuid4()), "user_id": user2.user_id}))
    assert response.json()["detail"] == "Project for user not found or user not admin"
    assert response.status_code == 401

    role_bindings = rbac.list_namespaced_role_binding(namespace1["name"])
    assert len(role_bindings.items) == 2
    role_bindings = rbac.list_namespaced_role_binding(namespace2["name"])
    assert len(role_bindings.items) == 1

    session.execute("SELECT COUNT(*) FROM public.project2user WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 2

    app.dependency_overrides = {current_user: lambda: user2}
    response = client.delete('project_user_management/user_from_project',
        data=json.dumps({"project_id": project["project_id"], "user_id": user2.user_id}))
    assert response.json()["detail"] == "There has to be at least one admin"
    assert response.status_code == 403

    session.execute("SELECT COUNT(*) FROM public.project2user WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 2

    response = client.delete('project_user_management/user_from_project',
                             data=json.dumps({"project_id": project["project_id"], "user_id": user1.user_id}))
    assert response.status_code == 200

    role_bindings = rbac.list_namespaced_role_binding(namespace1["name"])
    assert len(role_bindings.items) == 1
    role_bindings = rbac.list_namespaced_role_binding(namespace2["name"])
    assert len(role_bindings.items) == 1

    session.execute("SELECT COUNT(*) FROM public.project2user WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 1


def test_delete_user_candidate(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)

    app.dependency_overrides = {current_user: lambda: user2.copy(update={"is_verified": False})}
    response = client.delete('project_user_management/user_candidate',
                             data=json.dumps({"project_id": project["project_id"], "user_id": user1.user_id}))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides = {current_user: lambda: user2}
    response = client.delete('project_user_management/user_candidate',
                             data=json.dumps({"project_id": project["project_id"], "user_id": user1.user_id}))
    assert response.status_code == 404
    assert response.json()["detail"] == "No invitation found for user and project"

    response = client.post('project_user_management/',
                           data=json.dumps({"project_id": project["project_id"], "e_mail": user1.email}))

    app.dependency_overrides = {current_user: lambda: user1}
    response = client.post('project_user_management/accept_user_invitation',
                           data=json.dumps({"project_id": project["project_id"]}))

    session.execute("SELECT COUNT(*) FROM public.project2usercandidate WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 1

    response = client.delete('project_user_management/user_candidate',
                           data=json.dumps({"project_id": project["project_id"], "user_id": user3.user_id}))
    assert response.json()["detail"] == "Project for user not found or user not admin"
    assert response.status_code == 401

    session.execute("SELECT COUNT(*) FROM public.project2usercandidate WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 1

    app.dependency_overrides = {current_user: lambda: user2}
    response = client.delete('project_user_management/user_candidate',
                           data=json.dumps({"project_id": project["project_id"], "user_id": user3.user_id}))
    assert response.status_code == 200

    session.execute("SELECT COUNT(*) FROM public.project2usercandidate WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 0


def test_delete_decline_user_invitation(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)

    app.dependency_overrides = {current_user: lambda: user3.copy(update={"is_verified": False})}
    response = client.delete('project_user_management/decline_user_invitation',
                             data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides = {current_user: lambda: user3}
    response = client.delete('project_user_management/decline_user_invitation',
                             data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 404
    assert response.json()["detail"] == "No invitation found for user and project"

    app.dependency_overrides = {current_user: lambda: user2}
    response = client.post('project_user_management/',
                           data=json.dumps({"project_id": project["project_id"], "e_mail": user3.email}))

    session.execute("SELECT COUNT(*) FROM public.project2usercandidate WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 1

    app.dependency_overrides = {current_user: lambda: user3}
    response = client.delete('project_user_management/decline_user_invitation',
                             data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 200

    session.execute("SELECT COUNT(*) FROM public.project2usercandidate WHERE project_id='"+project["project_id"]+"'")
    assert session.fetchone()[0] == 0

    #clean up
    response = client.delete('projects/', data=json.dumps({"project_id": project["project_id"]}))
    response = client.delete('projects/', data=json.dumps({"project_id": project2["project_id"]}))

