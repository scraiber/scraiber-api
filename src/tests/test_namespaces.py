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
namespace4 = generate_namespace()

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



def test_namespace_add(client: TestClient, session, monkeypatch):
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

    response = client.post('project_user_management/',
                           data=json.dumps({"project_id": project["project_id"], "e_mail": user2.email}))
    response = client.post('project_user_management/',
                           data=json.dumps({"project_id": project["project_id"], "e_mail": user3.email}))

    app.dependency_overrides[current_user] = lambda: user2
    response = client.post('project_user_management/accept_user_invitation',
                           data=json.dumps({"project_id": project["project_id"]}))

    app.dependency_overrides[current_user] = lambda: user2.copy(update={"is_verified": False})
    namespace1.update({"project_id": project["project_id"]})
    response = client.post("namespaces/", data=json.dumps(namespace1))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides[current_user] = lambda: user2
    namespace1.update({"project_id": project["project_id"]})
    response = client.post("namespaces/", data=json.dumps(namespace1))
    assert response.status_code == 401
    assert response.json()["detail"] == "Project for user not found or user not admin"

    app.dependency_overrides[current_user] = lambda: user3
    namespace1.update({"project_id": project["project_id"]})
    response = client.post("namespaces/", data=json.dumps(namespace1))
    assert response.status_code == 401
    assert response.json()["detail"] == "Project for user not found or user not admin"

    response = v1.list_namespace()
    namespaces_names = [item.metadata.name for item in response.items]
    assert (namespace1["name"] in namespaces_names) == False
    assert (namespace2["name"] in namespaces_names) == False
    assert (namespace3["name"] in namespaces_names) == False
    assert (namespace4["name"] in namespaces_names) == False
    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 0

    app.dependency_overrides[current_user] = lambda: user1
    namespace_blacklist.update({"project_id": project["project_id"]})
    response = client.post("namespaces/", data=json.dumps(namespace_blacklist))
    assert response.status_code == 403
    assert response.json()["detail"] == "Namespace already exists"

    namespace1.update({"project_id": str(uuid.uuid4())})
    response = client.post("namespaces/", data=json.dumps(namespace1))
    assert response.status_code == 401
    assert response.json()["detail"] == "Project for user not found or user not admin"

    namespace1.update({"project_id": project["project_id"]})
    response = client.post("namespaces/", data=json.dumps(namespace1))
    assert response.status_code == 201
    response = client.post("namespaces/", data=json.dumps(namespace1))
    assert response.status_code == 403
    assert response.json()["detail"] == "Namespace already exists"

    response = v1.list_namespace()
    namespaces_names = [item.metadata.name for item in response.items]
    assert (namespace1["name"] in namespaces_names) == True
    assert (namespace2["name"] in namespaces_names) == False
    assert (namespace3["name"] in namespaces_names) == False
    assert (namespace4["name"] in namespaces_names) == False
    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 1
    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 0

    namespace2.update({"project_id": project["project_id"]})
    response = client.post("namespaces/", data=json.dumps(namespace2))
    assert response.status_code == 201
    namespace3.update({"project_id": project2["project_id"]})
    response = client.post("namespaces/", data=json.dumps(namespace3))
    assert response.status_code == 201
    namespace4.update({"project_id": project2["project_id"]})
    response = client.post("namespaces/", data=json.dumps(namespace4))
    assert response.status_code == 201

    response = v1.list_namespace()
    namespaces_names = [item.metadata.name for item in response.items]
    assert (namespace1["name"] in namespaces_names) == True
    assert (namespace2["name"] in namespaces_names) == True
    assert (namespace3["name"] in namespaces_names) == True
    assert (namespace4["name"] in namespaces_names) == True
    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 2
    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 2

    role_bindings = rbac.list_namespaced_role_binding(namespace1["name"])
    assert len(role_bindings.items) == 2
    role_bindings = rbac.list_namespaced_role_binding(namespace2["name"])
    assert len(role_bindings.items) == 2
    role_bindings = rbac.list_namespaced_role_binding(namespace3["name"])
    assert len(role_bindings.items) == 1
    role_bindings = rbac.list_namespaced_role_binding(namespace4["name"])
    assert len(role_bindings.items) == 1


def test_namespace_get(client: TestClient):
    app.dependency_overrides[current_user] = lambda: user1.copy(update={"is_verified": False})
    response = client.get("namespaces/", data=json.dumps({"name": "nonsense", "region": "EU1"}))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides[current_user] = lambda: user1
    response = client.get("namespaces/", data=json.dumps({"name": "nonsense", "region": "EU1"}))
    assert response.status_code == 404
    assert response.json()["detail"] == "Namespace not found"

    response = client.get("namespaces/", data=json.dumps({"name": namespace1["name"], "region": namespace1["region"]}))
    assert response.status_code == 200
    assert response.json() == namespace1

    app.dependency_overrides[current_user] = lambda: user3
    response = client.get("namespaces/", data=json.dumps({"name": namespace1["name"], "region": namespace1["region"]}))
    assert response.status_code == 404
    assert response.json()["detail"] == "Project/Namespace for user not found"


def test_namespace_get_by_project(client: TestClient):
    app.dependency_overrides[current_user] = lambda: user1.copy(update={"is_verified": False})
    response = client.get("namespaces/by_project", data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides[current_user] = lambda: user1
    response = client.get("namespaces/by_project", data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert namespace1 in response.json()
    assert namespace2 in response.json()

    response = client.get("namespaces/by_project", data=json.dumps({"project_id": str(uuid.uuid4())}))
    assert response.status_code == 404
    assert response.json()["detail"] == "Project for user not found"

    app.dependency_overrides[current_user] = lambda: user3
    response = client.get("namespaces/by_project", data=json.dumps({"project_id": project["project_id"]}))
    assert response.status_code == 404
    assert response.json()["detail"] == "Project for user not found"


def test_namespace_get_by_user(client: TestClient):
    response = client.get("namespaces/by_user")
    assert response.status_code == 404
    assert response.json()["detail"] == "No Project found for user"

    app.dependency_overrides[current_user] = lambda: user3.copy(update={"is_verified": False})
    response = client.get("namespaces/by_user")
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides[current_user] = lambda: user2
    response = client.get("namespaces/by_user")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert namespace1 in response.json()
    assert namespace2 in response.json()

    app.dependency_overrides[current_user] = lambda: user1
    response = client.get("namespaces/by_user")
    assert response.status_code == 200
    assert len(response.json()) == 4
    assert namespace1 in response.json()
    assert namespace2 in response.json()
    assert namespace3 in response.json()
    assert namespace4 in response.json()


def test_namespace_update_cpu_memory(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.namespaces.get_user_by_id", get_user_by_id)
    monkeypatch.setattr("app.api.routes.namespaces.get_user_list_by_id", get_user_list_by_id)

    data = {"name": namespace1["name"], "region": namespace1["region"], "max_namespace_cpu": 20,
            "max_namespace_mem": 1024, "default_limit_pod_cpu": 0.2, "default_limit_pod_mem": 128,
            "project_id": namespace1["project_id"]}

    app.dependency_overrides[current_user] = lambda: user1.copy(update={"is_verified": False})
    response = client.put('namespaces/update_cpu_memory', data=json.dumps(data))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides[current_user] = lambda: user2
    response = client.put('namespaces/update_cpu_memory', data=json.dumps(data))
    assert response.status_code == 401
    assert response.json()["detail"] == "Project for user not found or user not admin"

    app.dependency_overrides[current_user] = lambda: user1

    data = {"name": "nonsense", "region": namespace1["region"], "max_namespace_cpu": 20,
            "max_namespace_mem": 1024, "default_limit_pod_cpu": 0.2, "default_limit_pod_mem": 128,
            "project_id": namespace1["project_id"]}
    response = client.put('namespaces/update_cpu_memory', data=json.dumps(data))
    assert response.status_code == 404
    assert response.json()["detail"] == "Namespace not found"

    data = {"name": namespace1["name"], "region": namespace1["region"], "max_namespace_cpu": 20,
            "max_namespace_mem": 1024, "default_limit_pod_cpu": 0.2, "default_limit_pod_mem": 128,
            "project_id": project2["project_id"]}
    response = client.put('namespaces/update_cpu_memory', data=json.dumps(data))
    assert response.status_code == 404
    assert response.json()["detail"] == "Namespace does not belong to the project outlined"

    session.execute("SELECT max_namespace_cpu,max_namespace_mem,default_limit_pod_cpu,default_limit_pod_mem " +
                    "FROM public.namespaces WHERE name='" + namespace1["name"] + "' AND region='" + namespace1["region"] + "'")
    assert session.fetchone() == (10.0, 512.0, 0.1, 64.0)

    data = {"name": namespace1["name"], "region": namespace1["region"], "max_namespace_cpu": 20,
            "max_namespace_mem": 1024, "default_limit_pod_cpu": 0.2, "default_limit_pod_mem": 128,
            "project_id": namespace1["project_id"]}
    response = client.put('namespaces/update_cpu_memory', data=json.dumps(data))
    assert response.status_code == 200
    assert response.json() == data

    rq_json = v1.read_namespaced_resource_quota(name="resource-quota-for-"+namespace1["name"], namespace=namespace1["name"]).status.hard
    lr_json = v1.read_namespaced_limit_range(name="limit-range-for-"+namespace1["name"], namespace=namespace1["name"]).spec.limits[0].default
    assert rq_json == {'limits.cpu': '20', 'limits.memory': '1Gi'}
    assert lr_json == {'cpu': '200m', 'memory': '128Mi'}

    #wrong token
    app.dependency_overrides = {}
    response = client.put('projects/update_cpu_memory', data=json.dumps(data))
    assert response.status_code == 404


def test_namespace_delete(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.namespaces.get_user_by_id", get_user_by_id)
    monkeypatch.setattr("app.api.routes.namespaces.get_user_list_by_id", get_user_list_by_id)

    data = {"name": namespace1["name"], "region": namespace1["region"]}
    app.dependency_overrides[current_user] = lambda: user1.copy(update={"is_verified": False})
    response = client.delete('namespaces/', data=json.dumps(data))
    assert response.status_code == 401
    assert response.json()["detail"] == "User e-mail not verified"

    app.dependency_overrides[current_user] = lambda: user2
    response = client.delete('namespaces/', data=json.dumps(data))
    assert response.status_code == 401
    assert response.json()["detail"] == "Project for user not found or user not admin"

    app.dependency_overrides[current_user] = lambda: user1

    data = {"name": "nonsense", "region": namespace1["region"]}
    response = client.delete('namespaces/', data=json.dumps(data))
    assert response.status_code == 404
    assert response.json()["detail"] == "Namespace not found"

    app.dependency_overrides[current_user] = lambda: user3

    data = {"name": namespace1["name"], "region": namespace1["region"]}
    response = client.delete('namespaces/', data=json.dumps(data))
    assert response.status_code == 404
    assert response.json()["detail"] == "Project/Namespace for user not found"

    app.dependency_overrides = {}
    response = client.delete('namespaces/', data=json.dumps(data))
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    app.dependency_overrides[current_user] = lambda: user1

    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE old_project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE new_project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 0
    data_transfer = {"name": namespace1["name"], "region": namespace1["region"], "old_project_id": project["project_id"],
                     "new_project_id": project2["project_id"]}
    response = client.post('namespace2projecttransfer/', data=json.dumps(data_transfer))
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE old_project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 1
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE new_project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 1

    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE name='" + namespace1["name"] + "' AND region='" + namespace1["region"] + "'")
    assert session.fetchone()[0] == 1
    response = v1.list_namespace()
    namespaces_names = [item.metadata.name for item in response.items]
    assert (namespace1["name"] in namespaces_names) == True

    response = client.delete('namespaces/', data=json.dumps(data))
    assert response.status_code == 200
    assert response.json() == data

    session.execute("SELECT COUNT(*) FROM public.namespaces WHERE name='" + namespace1["name"] + "' AND region='" + namespace1["region"] + "'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE old_project_id='" + project["project_id"] + "'")
    assert session.fetchone()[0] == 0
    session.execute("SELECT COUNT(*) FROM public.namespace2projecttransfer WHERE new_project_id='" + project2["project_id"] + "'")
    assert session.fetchone()[0] == 0

    time.sleep(10)
    response = v1.list_namespace()
    namespaces_names = [item.metadata.name for item in response.items]
    assert (namespace1["name"] in namespaces_names) == False

    response = client.delete('projects/', data=json.dumps({"project_id": project["project_id"]}))
    response = client.delete('projects/', data=json.dumps({"project_id": project2["project_id"]}))