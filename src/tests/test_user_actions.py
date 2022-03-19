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
v1 = client.CoreV1Api()
rbac = client.RbacAuthorizationV1Api()

user1 = generate_user()
user2 = generate_user()


user_list1 = [user1]
user_list2 = [user2]


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

namespace1 = generate_namespace()
namespace2 = generate_namespace()
namespace3 = generate_namespace()
namespace4 = generate_namespace()

def test_user_add(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)

    #create project 1
    app.dependency_overrides[current_user] = lambda: user1
    response = client.post('projects/', data=json.dumps(project))
    project.update({"project_id": response.json()["project_id"]})
    #create project 2
    response = client.post('projects/', data=json.dumps(project2))
    project2.update({"project_id": response.json()["project_id"]})

    response = client.post('project_user_management/',
                           data=json.dumps({"project_id": project["project_id"], "e_mail": user2.email}))
    response = client.post('project_user_management/',
                           data=json.dumps({"project_id": project2["project_id"], "e_mail": user2.email}))

    session.execute("SELECT COUNT(*) FROM public.project2user WHERE user_id='"+user2.user_id+"'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.project2usercandidate WHERE user_id='"+user2.user_id+"'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.project2external WHERE e_mail='"+user2.email+"'")
    assert session.fetchone()[0] == 2

    app.dependency_overrides[current_user] = lambda: user2.copy(update={"is_verified": False})
    response = client.post('user_actions/')
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides[current_user] = lambda: user2
    response = client.post('user_actions/')
    assert response.status_code == 201
    session.execute("SELECT COUNT(*) FROM public.project2user WHERE user_id='"+user2.user_id+"'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.project2usercandidate WHERE user_id='"+user2.user_id+"'")
    assert session.fetchone()[0] == 2
    session.execute("SELECT COUNT(*) FROM public.project2external WHERE e_mail='"+user2.email+"'")
    assert session.fetchone()[0] == 0

    user_list1.append(user2)

    response = client.post('project_user_management/accept_user_invitation',
                           data=json.dumps({"project_id": project["project_id"]}))
    response = client.post('project_user_management/accept_user_invitation',
                           data=json.dumps({"project_id": project2["project_id"]}))

    session.execute("SELECT COUNT(*) FROM public.project2user WHERE user_id='"+user2.user_id+"'")
    assert session.fetchone()[0] == 2
    session.execute("SELECT COUNT(*) FROM public.project2usercandidate WHERE user_id='"+user2.user_id+"'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.project2external WHERE e_mail='"+user2.email+"'")
    assert session.fetchone()[0] == 0

def test_user_delete(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)
    monkeypatch.setattr("app.api.routes.user_management.get_user_list_by_id", get_user_list_by_id)
    monkeypatch.setattr("app.api.routes.namespaces.get_user_by_id", get_user_by_id)
    monkeypatch.setattr("app.api.routes.namespaces.get_user_list_by_id", get_user_list_by_id)

    app.dependency_overrides[current_user] = lambda: user1
    namespace1.update({"project_id": project["project_id"]})
    response = client.post("namespaces/", data=json.dumps(namespace1))
    namespace2.update({"project_id": project["project_id"]})
    response = client.post("namespaces/", data=json.dumps(namespace2))
    namespace3.update({"project_id": project2["project_id"]})
    response = client.post("namespaces/", data=json.dumps(namespace3))
    namespace4.update({"project_id": project2["project_id"]})
    response = client.post("namespaces/", data=json.dumps(namespace4))

    response = client.delete('user_actions/')
    assert response.status_code == 403
    assert response.json()["detail"] == "There are projects where you are the only admin. Please add at least another admin per project or delete them."

    role_bindings = rbac.list_namespaced_role_binding(namespace1["name"])
    assert len(role_bindings.items) == 2
    role_bindings = rbac.list_namespaced_role_binding(namespace2["name"])
    assert len(role_bindings.items) == 2
    role_bindings = rbac.list_namespaced_role_binding(namespace3["name"])
    assert len(role_bindings.items) == 2
    role_bindings = rbac.list_namespaced_role_binding(namespace4["name"])
    assert len(role_bindings.items) == 2

    response = client.put('project_user_management/admin_state',
                          data=json.dumps({"project_id": project["project_id"], "user_id": user2.user_id, "is_admin": True}))
    response = client.put('project_user_management/admin_state',
                          data=json.dumps({"project_id": project2["project_id"], "user_id": user2.user_id, "is_admin": True}))
    response = client.delete('project_user_management/user_from_project',
                             data=json.dumps({"project_id": project["project_id"], "user_id": user1.user_id}))

    app.dependency_overrides[current_user] = lambda: user2
    response = client.post('project_user_management/',
                           data=json.dumps({"project_id": project["project_id"], "e_mail": user1.email}))

    app.dependency_overrides[current_user] = lambda: user1
    session.execute("SELECT COUNT(*) FROM public.project2user WHERE user_id='"+user1.user_id+"'")
    assert session.fetchone()[0] == 1
    session.execute("SELECT COUNT(*) FROM public.project2usercandidate WHERE user_id='"+user1.user_id+"'")
    assert session.fetchone()[0] == 1

    response = client.delete('user_actions/')
    assert response.status_code == 200

    role_bindings = rbac.list_namespaced_role_binding(namespace1["name"])
    assert len(role_bindings.items) == 1
    role_bindings = rbac.list_namespaced_role_binding(namespace2["name"])
    assert len(role_bindings.items) == 1
    role_bindings = rbac.list_namespaced_role_binding(namespace3["name"])
    assert len(role_bindings.items) == 1
    role_bindings = rbac.list_namespaced_role_binding(namespace4["name"])
    assert len(role_bindings.items) == 1

    app.dependency_overrides[current_user] = lambda: user2
    response = client.delete('projects/', data=json.dumps({"project_id": project["project_id"]}))
    response = client.delete('projects/', data=json.dumps({"project_id": project2["project_id"]}))
