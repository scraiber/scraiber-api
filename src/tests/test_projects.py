import requests
import subprocess
import json
import os


port = os.environ['TEST_PORT']
host = os.environ['TEST_HOST']
cluster_dict = json.loads(os.environ['CLUSTER_DICT'])

user1 = {"email":"a2@b.com", "password":"asdf1234"}
user_id = ""
token_user1 = ""

project1 = {"name": "ab2", "region": list(cluster_dict.keys())[0], "limits_cpu": 0,  "limits_mem": 10}


def test_ping():
    r =requests.get('http://{host}:{port}/ping'.format(host=host, port=port))
    assert r.status_code == 200
    assert r.json()["ping"] == "pong!"


def test_auth():
    #Create user 1
    r =requests.post('http://{host}:{port}/auth/register'.format(host=host, port=port), data=json.dumps(user1), headers={"Content-Type": "application/json"})
    assert r.status_code == 201
    global user_id
    user_id = r.json()["id"]
    assert r.json()["email"] == user1["email"]


def test_project_create(session):
    #get token
    result = subprocess.check_output('curl -H "Content-Type: multipart/form-data" -X POST -F "username={user}" -F "password={pw}" http://{host}:{port}/auth/jwt/login'
            .format(host=host, port=port, user=user1["email"], pw=user1["password"]), shell=True)
    global token_user1
    token_user1 = json.loads(result)["access_token"]

    session.execute('SELECT COUNT(*) FROM public.projects')
    assert session.fetchone()[0] == 0

    #Create project
    headers = {
        'Content-Type': 'application/json',
        'Authorization': "Bearer {token}".format(token=token_user1),
    }
    response = requests.post('http://{host}:{port}/projects/'.format(host=host, port=port), headers=headers, data=json.dumps(project1))
    assert response.status_code == 201
    session.execute('SELECT COUNT(*) FROM public.projects')
    assert session.fetchone()[0] == 1

    response2 = requests.post('http://{host}:{port}/projects/'.format(host=host, port=port), headers=headers, data=json.dumps(project1))
    assert response2.status_code == 403
    session.execute('SELECT COUNT(*) FROM public.projects')
    assert session.fetchone()[0] == 1

    #Create project
    headers = {
        'Content-Type': 'application/json',
        'Authorization': "Bearer a{token}".format(token=token_user1),
    }
    response = requests.post('http://{host}:{port}/projects/'.format(host=host, port=port), headers=headers, data=json.dumps(project1))
    assert response.status_code == 401
    assert response.json() == {"detail":"Unauthorized"}
    session.execute('SELECT COUNT(*) FROM public.projects')
    assert session.fetchone()[0] == 1


def test_project_get():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': "Bearer {token}".format(token=token_user1),
    }
    data = {"name": project1["name"], "region": project1["region"]}
    response = requests.get('http://{host}:{port}/projects/'.format(host=host, port=port), headers=headers, data=json.dumps(data))
    assert response.status_code == 200
    test_json = project1.copy()
    test_json.update({"owner_id": user_id})
    assert response.json() == test_json

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': "Bearer a{token}".format(token=token_user1),
    }
    response = requests.get('http://{host}:{port}/projects/'.format(host=host, port=port), headers=headers, data=json.dumps(data))
    assert response.status_code == 401
    assert response.json() == {"detail":"Unauthorized"}


def test_project_get_by_owner():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': "Bearer {token}".format(token=token_user1),
    }
    response = requests.get('http://{host}:{port}/projects/by_owner/'.format(host=host, port=port), headers=headers)
    assert response.status_code == 200
    test_json = project1.copy()
    test_json.update({"owner_id": user_id})
    assert response.json()[0] == test_json
    assert len(response.json()) == 1

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': "Bearer a{token}".format(token=token_user1),
    }
    response = requests.get('http://{host}:{port}/projects/by_owner/'.format(host=host, port=port), headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail":"Unauthorized"}


def test_project_update_cpu_memory():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': "Bearer {token}".format(token=token_user1),
    }
    data = {"name": project1["name"], "region": project1["region"], "limits_cpu": 10,  "limits_mem": 20}
    response = requests.put('http://{host}:{port}/projects/update_cpu_memory/'.format(host=host, port=port), headers=headers, data=json.dumps(data))
    assert response.status_code == 200
    test_json = project1.copy()
    test_json.update({"owner_id": user_id, "limits_cpu": 10,  "limits_mem": 20})
    assert response.json() == test_json

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': "Bearer a{token}".format(token=token_user1),
    }
    response = requests.put('http://{host}:{port}/projects/update_cpu_memory/'.format(host=host, port=port), headers=headers, data=json.dumps(data))
    assert response.status_code == 401
    assert response.json() == {"detail":"Unauthorized"}


def test_delete(session):
    session.execute('SELECT COUNT(*) FROM public.projects')
    assert session.fetchone()[0] == 1

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': "Bearer {token}".format(token=token_user1),
    }
    data = {"name": project1["name"], "region": project1["region"]}
    response = requests.delete('http://{host}:{port}/projects/'.format(host=host, port=port), headers=headers, data=json.dumps(data))
    assert response.status_code == 200
    assert response.json() == 'No record remaining'

    session.execute('SELECT COUNT(*) FROM public.projects')
    assert session.fetchone()[0] == 0

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': "Bearer a{token}".format(token=token_user1),
    }
    response = requests.delete('http://{host}:{port}/projects/'.format(host=host, port=port), headers=headers, data=json.dumps(data))
    assert response.status_code == 401
    assert response.json() == {"detail":"Unauthorized"}    