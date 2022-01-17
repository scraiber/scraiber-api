from fastapi.testclient import TestClient
import json

from .helper_functions import generate_user, generate_project, mock_mail_project_post, mock_mail_project_delete
from app.main import app
from app.fastapiusers import current_user, current_verified_user



user1 = generate_user()
user2 = generate_user()
user3 = generate_user()
user4 = generate_user()

project = generate_project()
project2 = generate_project()


def test_auth(client: TestClient, session):
    #Create user 1
    r =client.post('/auth/register', data=json.dumps({"email": user1.email, "password": "abcd1234"}))
    assert r.status_code == 201

    user1.id = r.json()["id"]
    assert r.json()["email"] == user1.email

    session.execute("SELECT hashed_password FROM public.user WHERE id = '"+str(user1.id)+"'")
    user1.hashed_password = session.fetchone()[0]

    #Create user 2
    r =client.post('/auth/register', data=json.dumps({"email": user2.email, "password": "abcd1234"}))
    assert r.status_code == 201
    user2.id = r.json()["id"]
    assert r.json()["email"] == user2.email

    session.execute("SELECT hashed_password FROM public.user WHERE id = '"+str(user2.id)+"'")
    user2.hashed_password = session.fetchone()[0]


def test_user_add(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.projects.mail_project_post", mock_mail_project_post)
    #create project 1
    app.dependency_overrides[current_verified_user] = lambda: user1
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


def test_get_users_by_project(client: TestClient):
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


def test_put_admin_state(client: TestClient):
    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user2
    response = client.put('project_user_management/admin_state',
        data=json.dumps({"name": project["name"],"region": project["region"], "user_id": user1.id, "is_admin": False}))
    assert response.status_code == 401
    assert response.json()["detail"] == "Project for user not found or user not admin"

    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    response = client.put('project_user_management/admin_state',
        data=json.dumps({"name": project["name"],"region": project["region"], "user_id": user2.id, "is_admin": True}))
    assert response.status_code == 200

    app.dependency_overrides[current_user] = lambda: user2
    response = client.put('project_user_management/admin_state',
        data=json.dumps({"name": project["name"],"region": project["region"], "user_id": user1.id, "is_admin": False}))
    assert response.status_code == 401
    assert response.json()["detail"] == "The owner's admin state cannot be changed"

    app.dependency_overrides[current_user] = lambda: user1
    response = client.put('project_user_management/admin_state',
        data=json.dumps({"name": project2["name"],"region": project2["region"], "user_id": user2.id, "is_admin": True}))
    assert response.status_code == 404


def test_delete_external_from_project(client: TestClient, session):
    session.execute("SELECT COUNT(*) FROM public.project2external WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 1    

    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    response = client.delete('project_user_management/external_from_project',
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user3.email}))
    assert response.status_code == 200

    session.execute("SELECT COUNT(*) FROM public.project2external WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 0


def test_delete_all_externals_from_project(client: TestClient, session):
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
    #Delete non-existent project
    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    response = client.delete('project_user_management/user_from_project',
        data=json.dumps({"name": "nonesense-name","region": project["region"], "user_id": user2.id}))
    assert response.json()["detail"] == "Project for user not found or user not admin"
    assert response.status_code == 401

    app.dependency_overrides[current_user] = lambda: user2
    response = client.delete('project_user_management/user_from_project',
        data=json.dumps({"name": project["name"],"region": project["region"], "user_id": user1.id}))
    assert response.json()["detail"] == "The owner cannot be deleted"
    assert response.status_code == 401

    session.execute("SELECT COUNT(*) FROM public.project2user WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 2

    app.dependency_overrides[current_user] = lambda: user1
    response = client.delete('project_user_management/user_from_project',
        data=json.dumps({"name": project["name"],"region": project["region"], "user_id": user2.id}))
    assert response.status_code == 200

    session.execute("SELECT COUNT(*) FROM public.project2user WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 1

 
    monkeypatch.setattr("app.api.routes.projects.mail_project_delete", mock_mail_project_delete)
    #clean up
    response = client.delete('projects/', data=json.dumps({"name": project["name"], "region": project["region"]}))
    response = client.delete('projects/', data=json.dumps({"name": project2["name"], "region": project2["region"]}))