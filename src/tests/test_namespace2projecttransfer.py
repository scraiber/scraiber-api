import time
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
user3 = generate_user()

user_list1 = [user1, user2, user3]

namespace_blacklist = generate_namespace()
namespace_blacklist.update({"name": "default"})

namespace1 = generate_namespace()
namespace2 = generate_namespace()
namespace3 = generate_namespace()


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


async def get_user_list_by_id(id_list: List[str], require_200_status_code: bool = False) -> List[Auth0User]:
    output_list = []
    for user in user_list1:
        if user.user_id in id_list:
            output_list.append(user)
    return output_list

project = generate_project()
project2 = generate_project()
project3 = generate_project()


def test_transfer_candidate_add(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)
    monkeypatch.setattr("app.api.routes.namespaces.get_user_by_id", get_user_by_id)
    monkeypatch.setattr("app.api.routes.namespaces.get_user_list_by_id", get_user_list_by_id)
    monkeypatch.setattr("app.api.routes.namespace2projecttransfer.get_user_list_by_id", get_user_list_by_id)

    #create project 1
    app.dependency_overrides[current_user] = lambda: user1
    response = client.post('projects/', data=json.dumps(project))
    project.update({"project_id": response.json()["project_id"]})
    #create project 2
    response = client.post('projects/', data=json.dumps(project2))
    project2.update({"project_id": response.json()["project_id"]})

    response = client.post('projects/', data=json.dumps(project3))
    project3.update({"project_id": response.json()["project_id"]})

    response = client.post('project_user_management/',
                           data=json.dumps({"project_id": project["project_id"], "e_mail": user2.email}))
    response = client.post('project_user_management/',
                           data=json.dumps({"project_id": project2["project_id"], "e_mail": user3.email}))

    app.dependency_overrides[current_user] = lambda: user2
    response = client.post('project_user_management/accept_user_invitation',
                           data=json.dumps({"project_id": project["project_id"]}))
    app.dependency_overrides[current_user] = lambda: user3
    response = client.post('project_user_management/accept_user_invitation',
                           data=json.dumps({"project_id": project2["project_id"]}))

    app.dependency_overrides[current_user] = lambda: user1
    namespace1.update({"project_id": project["project_id"]})
    response = client.post("namespaces/", data=json.dumps(namespace1))
    namespace2.update({"project_id": project["project_id"]})
    response = client.post("namespaces/", data=json.dumps(namespace2))
    namespace3.update({"project_id": project["project_id"]})
    response = client.post("namespaces/", data=json.dumps(namespace3))

    data = {"name": namespace1["name"], "region": namespace1["region"], "old_project_id": project["project_id"],
            "new_project_id": project2["project_id"]}

    app.dependency_overrides[current_user] = lambda: user1.copy(update={"is_verified": False})
    response = client.post('namespace2projecttransfer/', data=json.dumps(data))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides[current_user] = lambda: user2
    response = client.post('namespace2projecttransfer/', data=json.dumps(data))
    assert response.status_code == 401
    assert response.json()["detail"] == "Project for user not found or user not admin"

    app.dependency_overrides[current_user] = lambda: user1

    data_nonsense = {"name": namespace1["name"], "region": namespace1["region"], "old_project_id": project["project_id"],
                     "new_project_id": str(uuid.uuid4())}
    response = client.post('namespace2projecttransfer/', data=json.dumps(data_nonsense))
    assert response.status_code == 404
    assert response.json()["detail"] == "Target project not found"

    data_nonsense = {"name": "nonsense", "region": namespace1["region"], "old_project_id": project["project_id"],
            "new_project_id": project2["project_id"]}
    response = client.post('namespace2projecttransfer/', data=json.dumps(data_nonsense))
    assert response.status_code == 404
    assert response.json()["detail"] == "Namespace not found"

    data_nonsense = {"name": namespace1["name"], "region": namespace1["region"], "old_project_id": project2["project_id"],
                     "new_project_id": project["project_id"]}
    response = client.post('namespace2projecttransfer/', data=json.dumps(data_nonsense))
    assert response.status_code == 403
    assert response.json()["detail"] == "Namespace not associated to source project"

    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 3
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE old_project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE new_project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 0

    response = client.post('namespace2projecttransfer/', data=json.dumps(data))
    assert response.status_code == 201
    assert response.json() == data

    data2 = {"name": namespace2["name"], "region": namespace2["region"], "old_project_id": project["project_id"],
            "new_project_id": project2["project_id"]}
    response = client.post('namespace2projecttransfer/', data=json.dumps(data2))

    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 3
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE old_project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 2
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE new_project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 2
    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 0

    app.dependency_overrides = {}
    response = client.post('namespace2projecttransfer/', data=json.dumps(data))
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_transfer_candidate_accept(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.namespace2projecttransfer.get_user_list_by_id", get_user_list_by_id)

    data1 = {"name": namespace1["name"], "region": namespace1["region"]}

    app.dependency_overrides[current_user] = lambda: user1.copy(update={"is_verified": False})
    response = client.post('namespace2projecttransfer/accept', data=json.dumps(data1))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides[current_user] = lambda: user1

    data_nonsense = {"name": "nonsense", "region": namespace1["region"]}
    response = client.post('namespace2projecttransfer/accept', data=json.dumps(data_nonsense))
    assert response.status_code == 404
    assert response.json()["detail"] == "Namespace not found"

    data3 = {"name": namespace3["name"], "region": namespace3["region"]}
    response = client.post('namespace2projecttransfer/accept', data=json.dumps(data3))
    assert response.status_code == 404
    assert response.json()["detail"] == "Namespace is not transfer candidate"

    app.dependency_overrides[current_user] = lambda: user3
    response = client.post('namespace2projecttransfer/accept', data=json.dumps(data1))
    assert response.status_code == 401
    assert response.json()["detail"] == "Project for user not found or user not admin"

    role_bindings = rbac.list_namespaced_role_binding(namespace1["name"])
    assert len(role_bindings.items) == 2
    namespace1_e_mails = [item.subjects[0].name for item in role_bindings.items]
    assert user1.email in namespace1_e_mails
    assert user2.email in namespace1_e_mails

    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 3
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE old_project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 2
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE new_project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 2
    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 0

    app.dependency_overrides[current_user] = lambda: user1
    response = client.post('namespace2projecttransfer/accept', data=json.dumps(data1))
    assert response.status_code == 201
    assert response.json() == {"name": namespace1["name"], "region": namespace1["region"],
                               "old_project_id": project["project_id"], "new_project_id": project2["project_id"]}

    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 2
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE old_project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 1
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE new_project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 1
    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 1

    role_bindings = rbac.list_namespaced_role_binding(namespace1["name"])
    assert len(role_bindings.items) == 2
    namespace1_e_mails = [item.subjects[0].name for item in role_bindings.items]
    assert user1.email in namespace1_e_mails
    assert user3.email in namespace1_e_mails

    app.dependency_overrides = {}
    response = client.post('namespace2projecttransfer/accept', data=json.dumps(data1))
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_transfer_get_by_source_project(client: TestClient):
    app.dependency_overrides[current_user] = lambda: user2.copy(update={"is_verified": False})
    response = client.get('namespace2projecttransfer/by_source_project', data=json.dumps({"project_id": project2["project_id"]}))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides[current_user] = lambda: user2
    response = client.get('namespace2projecttransfer/by_source_project', data=json.dumps({"project_id": project2["project_id"]}))
    assert response.status_code == 404
    assert response.json()["detail"] == "Project for user not found"

    response = client.get('namespace2projecttransfer/by_source_project', data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == namespace2["name"]
    assert response.json()[0]["region"] == namespace2["region"]
    assert response.json()[0]["old_project_id"] == project["project_id"]
    assert response.json()[0]["new_project_id"] == project2["project_id"]

    app.dependency_overrides[current_user] = lambda: user1
    response = client.get('namespace2projecttransfer/by_source_project', data=json.dumps({"project_id": project3["project_id"]}))
    assert response.status_code == 200
    assert len(response.json()) == 0

    app.dependency_overrides = {}
    response = client.get('namespace2projecttransfer/by_source_project', data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_transfer_get_by_target_project(client: TestClient):
    app.dependency_overrides[current_user] = lambda: user3.copy(update={"is_verified": False})
    response = client.get('namespace2projecttransfer/by_target_project', data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides[current_user] = lambda: user3
    response = client.get('namespace2projecttransfer/by_target_project', data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 404
    assert response.json()["detail"] == "Project for user not found"

    response = client.get('namespace2projecttransfer/by_target_project', data=json.dumps({"project_id": project2["project_id"]}))
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == namespace2["name"]
    assert response.json()[0]["region"] == namespace2["region"]
    assert response.json()[0]["old_project_id"] == project["project_id"]
    assert response.json()[0]["new_project_id"] == project2["project_id"]

    app.dependency_overrides[current_user] = lambda: user1
    response = client.get('namespace2projecttransfer/by_target_project', data=json.dumps({"project_id": project3["project_id"]}))
    assert response.status_code == 200
    assert len(response.json()) == 0

    app.dependency_overrides = {}
    response = client.get('namespace2projecttransfer/by_target_project', data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_transfer_get(client: TestClient):
    data2 = {"name": namespace2["name"], "region": namespace2["region"]}

    app.dependency_overrides[current_user] = lambda: user1.copy(update={"is_verified": False})
    response = client.get('namespace2projecttransfer/', data=json.dumps(data2))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides[current_user] = lambda: user1
    data_nonsense = {"name": "nonsense", "region": namespace1["region"]}
    response = client.get('namespace2projecttransfer/', data=json.dumps(data_nonsense))
    assert response.status_code == 404
    assert response.json()["detail"] == "Namespace not found"

    app.dependency_overrides[current_user] = lambda: user3
    response = client.get('namespace2projecttransfer/', data=json.dumps(data2))
    assert response.status_code == 404
    assert response.json()["detail"] == "Project for user not found"

    app.dependency_overrides[current_user] = lambda: user1

    data1 = {"name": namespace1["name"], "region": namespace1["region"]}
    response = client.get('namespace2projecttransfer/', data=json.dumps(data1))
    assert response.status_code == 403
    assert response.json()["detail"] == "Namespace is not transfer candidate"

    app.dependency_overrides[current_user] = lambda: user2

    response = client.get('namespace2projecttransfer/', data=json.dumps(data2))
    assert response.status_code == 200
    assert response.json() == {"name": namespace2["name"], "region": namespace2["region"],
                                "old_project_id": project["project_id"], "new_project_id": project2["project_id"]}

    app.dependency_overrides = {}
    response = client.get('namespace2projecttransfer/', data=json.dumps(data2))
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_transfer_delete(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)
    monkeypatch.setattr("app.api.routes.namespace2projecttransfer.get_user_list_by_id", get_user_list_by_id)

    data2 = {"name": namespace2["name"], "region": namespace2["region"]}

    app.dependency_overrides[current_user] = lambda: user1.copy(update={"is_verified": False})
    response = client.delete('namespace2projecttransfer/', data=json.dumps(data2))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides[current_user] = lambda: user1
    data_nonsense = {"name": "nonsense", "region": namespace1["region"]}
    response = client.delete('namespace2projecttransfer/', data=json.dumps(data_nonsense))
    assert response.status_code == 404
    assert response.json()["detail"] == "Namespace not found"

    data1 = {"name": namespace1["name"], "region": namespace1["region"]}
    response = client.delete('namespace2projecttransfer/', data=json.dumps(data1))
    assert response.status_code == 404
    assert response.json()["detail"] == "Namespace is not transfer candidate"

    app.dependency_overrides[current_user] = lambda: user2
    response = client.delete('namespace2projecttransfer/', data=json.dumps(data2))
    assert response.status_code == 401
    assert response.json()["detail"] == "Project for user not found or user not admin"

    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 2
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE old_project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 1
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE new_project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 1
    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 1

    app.dependency_overrides[current_user] = lambda: user1
    response = client.put('project_user_management/admin_state',
                          data=json.dumps({"project_id": project2["project_id"], "user_id": user3.user_id, "is_admin": True}))
    app.dependency_overrides[current_user] = lambda: user3
    response = client.put('project_user_management/admin_state',
                          data=json.dumps({"project_id": project2["project_id"], "user_id": user1.user_id, "is_admin": False}))

    response = client.delete('namespace2projecttransfer/', data=json.dumps(data2))
    assert response.status_code == 200
    assert response.json() == "No records remaining"

    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 2
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE old_project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE new_project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 1

    app.dependency_overrides[current_user] = lambda: user1
    data2 = {"name": namespace2["name"], "region": namespace2["region"], "old_project_id": project["project_id"],
             "new_project_id": project2["project_id"]}
    response = client.post('namespace2projecttransfer/', data=json.dumps(data2))

    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 2
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE old_project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 1
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE new_project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 1
    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 1

    response = client.delete('namespace2projecttransfer/', data=json.dumps(data2))
    assert response.status_code == 200
    assert response.json() == "No records remaining"

    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 2
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE old_project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE new_project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 1

    response = client.delete('projects/', data=json.dumps({"project_id": project["project_id"]}))

    app.dependency_overrides[current_user] = lambda: user3
    response = client.delete('projects/', data=json.dumps({"project_id": project2["project_id"]}))
