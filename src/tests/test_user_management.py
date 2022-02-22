from fastapi.testclient import TestClient
import json
from typing import List
from pydantic import EmailStr
from fastapi import HTTPException

from app.api.models.auth0 import Auth0User
from app.api.auth0.users import get_user_by_email

from .helper_functions import (
    generate_user, 
    generate_project, 
    mock_mail_project_post, 
    mock_mail_project_delete,
    mock_mail_um_post_internal,
    mock_mail_um_post_internal_owner,
    mock_mail_um_post_external,
    mock_mail_um_put_owner,
    mock_mail_um_put_changed_user,
    mock_mail_um_delete_external,
    mock_mail_um_delete_all_externals,
    mock_mail_um_delete_owner,
    mock_mail_um_delete_deleted_user
)
from app.main import app
from app.auth0 import current_user


user1 = generate_user()
user2 = generate_user()
user3 = generate_user()
user4 = generate_user()
user_list1 = [user1, user2]
user_list2 = [user3, user4]


async def get_user_by_email(email: EmailStr) -> Auth0User:
    for user in user_list1:
        if user.email == email:
            return user
    for user in user_list2:
        if user.email == email:
            raise HTTPException(status_code=404, detail="User could not be retrieved")


async def get_user_by_id(id: str) -> Auth0User:
    for user in user_list1:
        if user.user_id == id:
            return user
    for user in user_list2:
        if user.user_id == id:
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
    monkeypatch.setattr("app.api.routes.projects.mail_project_post", mock_mail_project_post)
    monkeypatch.setattr("app.api.routes.user_management.mail_um_post_internal", mock_mail_um_post_internal)
    monkeypatch.setattr("app.api.routes.user_management.mail_um_post_internal_owner", mock_mail_um_post_internal_owner)
    monkeypatch.setattr("app.api.routes.user_management.mail_um_post_external", mock_mail_um_post_external)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)

    #create project 1
    app.dependency_overrides[current_user] = lambda: user1.copy(update={"is_verified": True})
    response = client.post('projects/', data=json.dumps(project))
    #create project 2
    response = client.post('projects/', data=json.dumps(project2))

    session.execute("SELECT COUNT(*) FROM public.project2user WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 1

    #Assign user 2 to project 1
    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    response = client.post('project_user_management/',
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user2.email}))
    assert response.status_code == 201
    session.execute("SELECT COUNT(*) FROM public.project2user WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 2

    response = client.post('project_user_management/',
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user2.email}))
    assert response.status_code == 403

    app.dependency_overrides[current_user] = lambda: user2
    response = client.post('project_user_management/',
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user3.email}))
    assert response.status_code == 401
    assert response.json()["detail"] == "Project for user not found or user not admin"

    session.execute("SELECT COUNT(*) FROM public.project2external WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 0

    app.dependency_overrides[current_user] = lambda: user1
    response = client.post('project_user_management/',
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user3.email}))
    print(response.json())
    assert response.status_code == 201
    session.execute("SELECT COUNT(*) FROM public.project2external WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 1


def test_get_externals_by_project(client: TestClient):
    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    response = client.get('project_user_management/externals_by_project',
        data=json.dumps({"name": project["name"],"region": project["region"]}))
    assert response.status_code == 200
    test_json = {"name": project["name"],"region": project["region"], "e_mail": user3.email, "is_admin": False}
    assert response.json()[0] == test_json
    assert len(response.json()) == 1    

    response = client.get('project_user_management/externals_by_project',
        data=json.dumps({"name": project2["name"],"region": project2["region"]}))
    assert response.status_code == 404


def test_get_users_by_project(client: TestClient, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.get_user_list_by_id", get_user_list_by_id)

    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    response = client.get('project_user_management/users_by_project',
        data=json.dumps({"name": project["name"],"region": project["region"]}))
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = client.get('project_user_management/users_by_project',
        data=json.dumps({"name": project2["name"],"region": project2["region"]}))
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_put_admin_state(client: TestClient, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.mail_um_put_owner", mock_mail_um_put_owner)
    monkeypatch.setattr("app.api.routes.user_management.mail_um_put_changed_user", mock_mail_um_put_changed_user)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)

    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user2
    response = client.put('project_user_management/admin_state',
        data=json.dumps({"name": project["name"],"region": project["region"], "user_id": user1.user_id, "is_admin": False}))
    assert response.status_code == 401
    assert response.json()["detail"] == "Project for user not found or user not admin"

    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    response = client.put('project_user_management/admin_state',
        data=json.dumps({"name": project["name"],"region": project["region"], "user_id": user2.user_id, "is_admin": True}))
    assert response.status_code == 200

    app.dependency_overrides[current_user] = lambda: user2
    response = client.put('project_user_management/admin_state',
        data=json.dumps({"name": project["name"],"region": project["region"], "user_id": user1.user_id, "is_admin": False}))
    assert response.status_code == 401
    assert response.json()["detail"] == "The owner's admin state cannot be changed"

    app.dependency_overrides[current_user] = lambda: user1
    response = client.put('project_user_management/admin_state',
        data=json.dumps({"name": project2["name"],"region": project2["region"], "user_id": user2.user_id, "is_admin": True}))
    assert response.status_code == 404


def test_delete_external_from_project(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.mail_um_delete_external", mock_mail_um_delete_external)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)

    session.execute("SELECT COUNT(*) FROM public.project2external WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 1    

    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    response = client.delete('project_user_management/external_from_project',
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user3.email}))
    assert response.status_code == 200

    session.execute("SELECT COUNT(*) FROM public.project2external WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 0


def test_delete_all_externals_from_project(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.mail_um_post_internal", mock_mail_um_post_internal)
    monkeypatch.setattr("app.api.routes.user_management.mail_um_post_internal_owner", mock_mail_um_post_internal_owner)
    monkeypatch.setattr("app.api.routes.user_management.mail_um_post_external", mock_mail_um_post_external)
    monkeypatch.setattr("app.api.routes.user_management.mail_um_delete_all_externals", mock_mail_um_delete_all_externals)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)

    session.execute("SELECT COUNT(*) FROM public.project2external WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 0    

    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    response = client.post('project_user_management/',
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user3.email}))
    assert response.status_code == 201
    response = client.post('project_user_management/',
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user4.email}))
    assert response.status_code == 201
    session.execute("SELECT COUNT(*) FROM public.project2external WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 2

    response = client.delete('project_user_management/all_externals_from_project',
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user3.email}))
    assert response.status_code == 200

    session.execute("SELECT COUNT(*) FROM public.project2external WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 0


def test_delete_user_from_project(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.mail_um_delete_owner", mock_mail_um_delete_owner)
    monkeypatch.setattr("app.api.routes.user_management.mail_um_delete_deleted_user", mock_mail_um_delete_deleted_user)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)

    #Delete non-existent project
    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    response = client.delete('project_user_management/user_from_project',
        data=json.dumps({"name": "nonesense-name","region": project["region"], "user_id": user2.user_id}))
    assert response.json()["detail"] == "Project for user not found or user not admin"
    assert response.status_code == 401

    app.dependency_overrides[current_user] = lambda: user2
    response = client.delete('project_user_management/user_from_project',
        data=json.dumps({"name": project["name"],"region": project["region"], "user_id": user1.user_id}))
    assert response.json()["detail"] == "The owner cannot be deleted"
    assert response.status_code == 401

    session.execute("SELECT COUNT(*) FROM public.project2user WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 2

    app.dependency_overrides[current_user] = lambda: user1
    response = client.delete('project_user_management/user_from_project',
        data=json.dumps({"name": project["name"],"region": project["region"], "user_id": user2.user_id}))
    assert response.status_code == 200

    session.execute("SELECT COUNT(*) FROM public.project2user WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 1

 
    monkeypatch.setattr("app.api.routes.projects.mail_project_delete", mock_mail_project_delete)
    #clean up
    response = client.delete('projects/', data=json.dumps({"name": project["name"], "region": project["region"]}))
    response = client.delete('projects/', data=json.dumps({"name": project2["name"], "region": project2["region"]}))