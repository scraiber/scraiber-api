from fastapi.testclient import TestClient
import json
from typing import List
from pydantic import EmailStr
from fastapi import HTTPException

from app.api.models.auth0 import Auth0User
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
    mock_mail_registration_confirmation,
    generate_get_user_by_email,
    generate_get_user_by_id
)
from app.main import app
from app.auth0 import current_user


user1 = generate_user()
user2 = generate_user()
user3 = generate_user()
user4 = generate_user()
user_list1 = [user1, user2, user3]
user_list2 = [user4]


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
    monkeypatch.setattr("app.api.routes.owner_transfer.mail_ot_post", mock_mail_ot_post)
    monkeypatch.setattr("app.api.routes.owner_transfer.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)

    #create project
    app.dependency_overrides[current_user] = lambda: user1.copy(update={"is_verified": True})
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
    assert response.json()["detail"] == "User could not be retrieved"

    response = client.post('owner_transfer/',
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user3.email}))
    assert response.status_code == 403
    assert response.json()["detail"] == "User not assigned to project"

 #   response = client.post('owner_transfer/',
 #       data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user2.email}))
 #   assert response.status_code == 403
 #   assert response.json()["detail"] == "User e-mail of new owner candidate is not verified"
#
 #   session.execute("UPDATE public.user a SET is_verified = true WHERE id = '"+str(user2.user_id)+"'")

    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 0  

    response = client.post('owner_transfer/',
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user2.email}))
    assert response.status_code == 201
    assert response.json() == {"name": project["name"],"region": project["region"], "candidate_id": user2.user_id}
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
    assert session.fetchone()[0] == user2.user_id


def test_get_owner_candidate_by_project(client: TestClient, monkeypatch):
    monkeypatch.setattr("app.api.routes.owner_transfer.get_user_by_id", get_user_by_id)

    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    response = client.get('owner_transfer/owner_candidate_by_project',
        data=json.dumps({"name": project["name"],"region": project["region"]}))
    assert response.status_code == 200
    assert response.json()["sub"] == user2.user_id

    app.dependency_overrides[current_user] = lambda: user2
    response = client.get('owner_transfer/owner_candidate_by_project',
        data=json.dumps({"name": project["name"],"region": project["region"]}))
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found or user not owner"

    monkeypatch.setattr("app.api.routes.projects.mail_project_post", mock_mail_project_post)
    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1.copy(update={"is_verified": True})
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
    monkeypatch.setattr("app.api.routes.owner_transfer.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)

    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE candidate_id='"+user2.user_id+"'")
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

    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE candidate_id='"+user2.user_id+"'")
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
    monkeypatch.setattr("app.api.routes.owner_transfer.get_user_by_id", get_user_by_id)

    session.execute("SELECT candidate_id FROM public.project2ownercandidate WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == user2.user_id

    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user3.copy(update={"is_verified": True})
    response = client.put('owner_transfer/accept', data=json.dumps({"name": project["name"],"region": project["region"]}))
    assert response.status_code == 404
    assert response.json()["detail"] == "User not owner candidate for project or project not found"

    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user2
    response = client.put('owner_transfer/accept', data=json.dumps({"name": project["name"],"region": project["region"]}))
    assert response.status_code == 401

    session.execute("SELECT owner_id FROM public.projects WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == user1.user_id

    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 1

    session.execute("SELECT is_admin FROM public.project2user WHERE name='"+project["name"]+"' AND user_id='"+user2.user_id+"'")
    assert session.fetchone()[0] == False

    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user2.copy(update={"is_verified": True})
    response = client.put('owner_transfer/accept', data=json.dumps({"name": project["name"],"region": project["region"]}))
    assert response.status_code == 200

    session.execute("SELECT owner_id FROM public.projects WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == user2.user_id

    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE name='"+project["name"]+"'")
    assert session.fetchone()[0] == 0

    session.execute("SELECT is_admin FROM public.project2user WHERE name='"+project["name"]+"' AND user_id='"+user2.user_id+"'")
    assert session.fetchone()[0] == True


def test_delete_candidate_for_project(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.owner_transfer.mail_ot_post", mock_mail_ot_post)
    monkeypatch.setattr("app.api.routes.owner_transfer.mail_project_delete_inform_owner", mock_mail_project_delete_inform_owner)
    monkeypatch.setattr("app.api.routes.owner_transfer.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.owner_transfer.get_user_by_id", get_user_by_id)

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
    monkeypatch.setattr("app.api.routes.owner_transfer.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.owner_transfer.get_user_by_id", get_user_by_id)

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
    monkeypatch.setattr("app.api.routes.owner_transfer.get_user_by_id", get_user_by_id)
    monkeypatch.setattr("app.api.routes.owner_transfer.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_email", get_user_by_email)
    monkeypatch.setattr("app.api.routes.user_management.get_user_by_id", get_user_by_id)

    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE candidate_id='"+user3.user_id+"'")
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


    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE candidate_id='"+user3.user_id+"'")
    assert session.fetchone()[0] == 2

    app.dependency_overrides[current_user] = lambda: user3
    response = client.delete('owner_transfer/all_projects_for_candidate')   
    assert response.status_code == 200

    session.execute("SELECT COUNT(*) FROM public.project2ownercandidate WHERE candidate_id='"+user3.user_id+"'")
    assert session.fetchone()[0] == 0

    #clean up
    monkeypatch.setattr("app.api.routes.projects.mail_project_delete", mock_mail_project_delete)
    app.dependency_overrides[current_user] = lambda: user1
    response = client.delete('projects/', data=json.dumps({"name": project["name"], "region": project["region"]}))
    response = client.delete('projects/', data=json.dumps({"name": project2["name"], "region": project2["region"]}))