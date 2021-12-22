import requests
import subprocess
import json
import os


port = os.environ['TEST_PORT']
host = os.environ['TEST_HOST']
cluster_dict = json.loads(os.environ['CLUSTER_DICT'])

user1 = {"email":"ab3@b.com", "password":"asdf1234"}
user_id = ""
token_user1 = ""

project1 = {"name": "ab3", "region": list(cluster_dict.keys())[0], "limits_cpu": 0,  "limits_mem": 10}


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
    no_projects = session.fetchone()[0]
    #Create project
    headers = {
        'Content-Type': 'application/json',
        'Authorization': "Bearer {token}".format(token=token_user1),
    }

    response = requests.post('http://{host}:{port}/projects/'.format(host=host, port=port), headers=headers, data=json.dumps(project1))
    assert response.status_code == 201

    session.execute('SELECT COUNT(*) FROM public.projects')
    assert session.fetchone()[0] == no_projects + 1

    response2 = requests.post('http://{host}:{port}/projects/'.format(host=host, port=port), headers=headers, data=json.dumps(project1))
    assert response2.status_code == 403

