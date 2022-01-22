from fastapi.testclient import TestClient
import json

from .helper_functions import (
    generate_user, 
    generate_project, 
    mock_mail_project_post, 
    mock_mail_project_delete,
    mock_mail_um_post_internal,
    mock_mail_um_post_internal_owner,
    mock_mail_um_post_external,
    mock_mail_ot_post,
    mock_mail_project_put_old_owner,
    mock_mail_project_put_new_owner,
    mock_mail_project_delete_inform_owner,
    mock_mail_project_delete_inform_candidate,
    mock_mail_registration_confirmation
)
from app.main import app
from app.fastapiusers import current_user, current_verified_user


user1 = generate_user()
user2 = generate_user()
user3 = generate_user()
user4 = generate_user()

project = generate_project()
project2 = generate_project()



def test_auth(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.usermanager.mail_registration_confirmation", mock_mail_registration_confirmation)
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

    #Create user 3
    r =client.post('/auth/register', data=json.dumps({"email": user3.email, "password": "abcd1234"}))
    assert r.status_code == 201
    user3.id = r.json()["id"]
    assert r.json()["email"] == user3.email

    session.execute("SELECT hashed_password FROM public.user WHERE id = '"+str(user3.id)+"'")
    user3.hashed_password = session.fetchone()[0]


def test_user_add(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.projects.mail_project_post", mock_mail_project_post)
    monkeypatch.setattr("app.api.routes.user_management.mail_um_post_internal", mock_mail_um_post_internal)
    monkeypatch.setattr("app.api.routes.user_management.mail_um_post_internal_owner", mock_mail_um_post_internal_owner)
    monkeypatch.setattr("app.api.routes.user_management.mail_um_post_external", mock_mail_um_post_external)
    monkeypatch.setattr("app.api.routes.owner_transfer.mail_ot_post", mock_mail_ot_post)

    #create project
    app.dependency_overrides[current_verified_user] = lambda: user1
    response = client.post('projects/', data=json.dumps(project))
    app.dependency_overrides[current_user] = lambda: user1
    response = client.post('project_user_management/',
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user2.email}))

    app.dependency_overrides[current_user] = lambda: user2
    response = client.post('owner_transfer/',
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user3.email}))
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found or user not owner"

    app.dependency_overrides[current_user] = lambda: user1
    response = client.post('owner_transfer/',
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user4.email}))
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"

    response = client.post('owner_transfer/',
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user3.email}))
    assert response.status_code == 403
    assert response.json()["detail"] == "User not assigned to project"

 #   response = client.post('owner_transfer/',
 #       data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user2.email}))
 #   assert response.status_code == 403
 #   assert response.json()["detail"] == "User e-mail of new owner candidate is not verified"
#
 #   session.execute("UPDATE public.user a SET is_verified = true WHERE id = '"+str(user2.id)+"'")

    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 0  

    response = client.post('owner_transfer/',
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user2.email}))
    assert response.status_code == 201
    assert response.json() == {"name": project["name"],"region": project["region"], "candidate_id": user2.id}
    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 1

    response = client.post('owner_transfer/',
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user2.email}))
    assert response.status_code == 401
    assert response.json()["detail"] == "Please delete the already existent candidate first"

    response = client.post('project_user_management/',
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user3.email}))
    response = client.post('owner_transfer/',
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user3.email}))
    assert response.status_code == 401
    assert response.json()["detail"] == "Please delete the already existent candidate first"
    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 1
    session.execute("SELECT candidate_id FROM public.project2ownercandidate WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == user2.id


def test_get_owner_candidate_by_project(client: TestClient, monkeypatch):
    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    response = client.get('owner_transfer/owner_candidate_by_project',
        data=json.dumps({"name": project["name"],"region": project["region"]}))
    assert response.status_code == 200
    assert response.json()["id"] == user2.id

    app.dependency_overrides[current_user] = lambda: user2
    response = client.get('owner_transfer/owner_candidate_by_project',
        data=json.dumps({"name": project["name"],"region": project["region"]}))
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found or user not owner"

    monkeypatch.setattr("app.api.routes.projects.mail_project_post", mock_mail_project_post)
    app.dependency_overrides = {}
    app.dependency_overrides[current_verified_user] = lambda: user1
    response = client.post('projects/', data=json.dumps(project2))
    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    response = client.get('owner_transfer/owner_candidate_by_project',
        data=json.dumps({"name": project2["name"],"region": project2["region"]}))
    assert response.status_code == 404
    assert response.json()["detail"] == "No associated owner candidate found"


def test_get_projects_for_owner_candidate(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.mail_um_post_internal", mock_mail_um_post_internal)
    monkeypatch.setattr("app.api.routes.user_management.mail_um_post_internal_owner", mock_mail_um_post_internal_owner)
    monkeypatch.setattr("app.api.routes.user_management.mail_um_post_external", mock_mail_um_post_external)
    monkeypatch.setattr("app.api.routes.owner_transfer.mail_ot_post", mock_mail_ot_post)

    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE candidate_id='"+user2.id+"'")
    assert session.fetchone()[0] == 1

    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user2
    response = client.get('owner_transfer/projects_for_owner_candidate')
    assert response.status_code == 200
    assert len(response.json()) == 1

    #add user 2 to project 2 and make him owner candidate
    app.dependency_overrides[current_user] = lambda: user1
    response = client.post('project_user_management/',
        data=json.dumps({"name": project2["name"],"region": project2["region"], "e_mail": user2.email}))
    response = client.post('owner_transfer/',
        data=json.dumps({"name": project2["name"],"region": project2["region"], "e_mail": user2.email}))

    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE candidate_id='"+user2.id+"'")
    assert session.fetchone()[0] == 2

    app.dependency_overrides[current_user] = lambda: user2
    response = client.get('owner_transfer/projects_for_owner_candidate')
    assert response.status_code == 200
    assert len(response.json()) == 2

    app.dependency_overrides[current_user] = lambda: user3
    response = client.get('owner_transfer/projects_for_owner_candidate')
    assert response.status_code == 404
    assert response.json()["detail"] == "User is nowhere owner candidate"


def test_put_accept(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.owner_transfer.mail_project_put_old_owner", mock_mail_project_put_old_owner)
    monkeypatch.setattr("app.api.routes.owner_transfer.mail_project_put_new_owner", mock_mail_project_put_new_owner)

    session.execute("SELECT candidate_id FROM public.project2ownercandidate WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == user2.id

    app.dependency_overrides = {}
    app.dependency_overrides[current_verified_user] = lambda: user3
    response = client.put('owner_transfer/accept', data=json.dumps({"name": project["name"],"region": project["region"]}))
    assert response.status_code == 404
    assert response.json()["detail"] == "User not owner candidate for project or project not found"

    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user2
    response = client.put('owner_transfer/accept', data=json.dumps({"name": project["name"],"region": project["region"]}))
    assert response.status_code == 401

    session.execute("SELECT owner_id FROM public.projects WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == user1.id

    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 1

    session.execute("SELECT is_admin FROM public.project2user WHERE name='"+project["name"]+"' AND user_id='"+user2.id+"'")
    assert session.fetchone()[0] == False

    app.dependency_overrides = {}
    app.dependency_overrides[current_verified_user] = lambda: user2
    response = client.put('owner_transfer/accept', data=json.dumps({"name": project["name"],"region": project["region"]}))
    assert response.status_code == 200

    session.execute("SELECT owner_id FROM public.projects WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == user2.id

    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 0

    session.execute("SELECT is_admin FROM public.project2user WHERE name='"+project["name"]+"' AND user_id='"+user2.id+"'")
    assert session.fetchone()[0] == True


def test_delete_candidate_for_project(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.owner_transfer.mail_ot_post", mock_mail_ot_post)
    monkeypatch.setattr("app.api.routes.owner_transfer.mail_project_delete_inform_owner", mock_mail_project_delete_inform_owner)

    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user2
    response = client.post('owner_transfer/', data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user3.email}))    

    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 1

    app.dependency_overrides[current_user] = lambda: user1
    response = client.delete('owner_transfer/candidate_for_project', data=json.dumps({"name": project["name"],"region": project["region"]}))
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found or user not owner"

    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 1

    app.dependency_overrides[current_user] = lambda: user2
    response = client.delete('owner_transfer/candidate_for_project', data=json.dumps({"name": project["name"],"region": project["region"]}))
    assert response.status_code == 200
   
    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 0


def test_delete_project_for_candidate(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.owner_transfer.mail_ot_post", mock_mail_ot_post)
    monkeypatch.setattr("app.api.routes.owner_transfer.mail_project_delete_inform_candidate", mock_mail_project_delete_inform_candidate)

    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user2
    response = client.post('owner_transfer/', data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user3.email}))    

    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 1

    app.dependency_overrides[current_user] = lambda: user1
    response = client.delete('owner_transfer/project_for_candidate', data=json.dumps({"name": project["name"],"region": project["region"]}))   
    assert response.status_code == 404
    assert response.json()["detail"] == "User not owner candidate for project or project not found"

    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 1

    app.dependency_overrides[current_user] = lambda: user3
    response = client.delete('owner_transfer/project_for_candidate', data=json.dumps({"name": "nonsense-project","region": project["region"]})) 
    assert response.status_code == 404
    assert response.json()["detail"] == "User not owner candidate for project or project not found"   

    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 1

    response = client.delete('owner_transfer/project_for_candidate', data=json.dumps({"name": project["name"],"region": project["region"]}))   
    assert response.status_code == 200

    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 0


def test_delete_all_projects_for_candidate(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.user_management.mail_um_post_internal", mock_mail_um_post_internal)
    monkeypatch.setattr("app.api.routes.user_management.mail_um_post_internal_owner", mock_mail_um_post_internal_owner)
    monkeypatch.setattr("app.api.routes.user_management.mail_um_post_external", mock_mail_um_post_external)
    monkeypatch.setattr("app.api.routes.owner_transfer.mail_ot_post", mock_mail_ot_post)
    monkeypatch.setattr("app.api.routes.owner_transfer.mail_project_delete_inform_owner", mock_mail_project_delete_inform_owner)
    monkeypatch.setattr("app.api.routes.owner_transfer.mail_project_delete_inform_candidate", mock_mail_project_delete_inform_candidate)

    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE candidate_id='"+user3.id+"'")
    assert session.fetchone()[0] == 0

    #add user 3 as candidate to project 1
    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user2
    response = client.post('owner_transfer/', data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user3.email})) 


    #add user 3 as candidate to project 2
    app.dependency_overrides[current_user] = lambda: user1
    response = client.delete('owner_transfer/candidate_for_project', data=json.dumps({"name": project2["name"],"region": project2["region"]}))
    response = client.post('project_user_management/', data=json.dumps({"name": project2["name"],"region": project2["region"], "e_mail": user3.email}))
    response = client.post('owner_transfer/', data=json.dumps({"name": project2["name"],"region": project2["region"], "e_mail": user3.email})) 


    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE candidate_id='"+user3.id+"'")
    assert session.fetchone()[0] == 2

    app.dependency_overrides[current_user] = lambda: user3
    response = client.delete('owner_transfer/all_projects_for_candidate')   
    assert response.status_code == 200

    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE candidate_id='"+user3.id+"'")
    assert session.fetchone()[0] == 0

    #clean up
    monkeypatch.setattr("app.api.routes.projects.mail_project_delete", mock_mail_project_delete)
    app.dependency_overrides[current_user] = lambda: user1
    response = client.delete('projects/', data=json.dumps({"name": project["name"], "region": project["region"]}))
    response = client.delete('projects/', data=json.dumps({"name": project2["name"], "region": project2["region"]}))