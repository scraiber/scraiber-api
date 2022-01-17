from fastapi.testclient import TestClient
import json
import os
from kubernetes import client as kube_client
from kubernetes import config
import random
import string

from .helper_functions import generate_user, generate_project, mock_mail_project_post, mock_mail_project_delete
from app.main import app
from app.fastapiusers import current_user, current_verified_user



cluster_name = json.loads(os.environ['CLUSTER_DICT'])["EU1"]["Config-Name"]
config.load_kube_config("config.yaml", context=cluster_name)
v1=kube_client.CoreV1Api()

user1 = generate_user()
user2 = generate_user()
user3 = generate_user()
user4 = generate_user()
project = generate_project()
project2 = generate_project()

params = (
    ('region', 'EU1'),
)


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

    #Create user 3
    r =client.post('/auth/register', data=json.dumps({"email": user3.email, "password": "abcd1234"}))
    assert r.status_code == 201
    user3.id = r.json()["id"]
    assert r.json()["email"] == user3.email

    session.execute("SELECT hashed_password FROM public.user WHERE id = '"+str(user3.id)+"'")
    user3.hashed_password = session.fetchone()[0]



def test_generate_config_without_any_projects_assigned(client: TestClient):
    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    response = client.get('kubernetes/generate-config', params=params)
    assert response.status_code == 404
    assert response.json()["detail"] == "No Project found for user and region"


def test_generate_config_after_projects_generated(client: TestClient, session, monkeypatch):
    monkeypatch.setattr("app.api.routes.projects.mail_project_post", mock_mail_project_post)

    app.dependency_overrides = {}
    app.dependency_overrides[current_verified_user] = lambda: user1
    response = client.post('projects/', data=json.dumps(project))
    response = client.post('projects/', data=json.dumps(project2))

    session.execute("SELECT COUNT(*) FROM public.certificate2user WHERE region='EU1' AND user_id='"+user1.id+"'")
    assert session.fetchone()[0] == 0

    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    counter = 0
    invalid_config = True
    while counter<=10 and invalid_config:
        response = client.get('kubernetes/generate-config', params=params)
        assert response.status_code == 201
        counter += 1
        if "client-certificate-data: None" not in response.json()["config"]:
            invalid_config = False
    store_name = user1.id+''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=10))+".yaml"
    with open(store_name, "w") as text_file:
        text_file.write(response.json()["config"])

    session.execute("SELECT COUNT(*) FROM public.certificate2user WHERE region='EU1' AND user_id='"+user1.id+"'")
    assert session.fetchone()[0] == 1

    config.load_kube_config(store_name)
    current_api=kube_client.CoreV1Api()

    if cluster_name != "minikube":
        rq_json = current_api.read_namespaced_resource_quota(name="resource-quota-for-"+project["name"], namespace=project["name"]).status.hard
        lr_json = current_api.read_namespaced_limit_range(name="limit-range-for-"+project["name"], namespace=project["name"]).spec.limits[0].default
        assert rq_json == {'limits.cpu': '10', 'limits.memory': '512Mi'}
        assert lr_json == {'cpu': '100m', 'memory': '64Mi'}

        rq_json = current_api.read_namespaced_resource_quota(name="resource-quota-for-"+project2["name"], namespace=project2["name"]).status.hard
        lr_json = current_api.read_namespaced_limit_range(name="limit-range-for-"+project2["name"], namespace=project2["name"]).spec.limits[0].default
        assert rq_json == {'limits.cpu': '10', 'limits.memory': '512Mi'}
        assert lr_json == {'cpu': '100m', 'memory': '64Mi'}



def test_added_and_removed_user(client: TestClient):
    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    response = client.post('project_user_management/', data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user2.email}))

    app.dependency_overrides[current_user] = lambda: user2
    counter = 0
    invalid_config = True
    while counter<=10 and invalid_config:
        response = client.get('kubernetes/generate-config', params=params)
        assert response.status_code == 201
        counter += 1
        if "client-certificate-data: None" not in response.json()["config"]:
            invalid_config = False
    store_name1 = user2.id+''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=10))+".yaml"
    with open(store_name1, "w") as text_file:
        text_file.write(response.json()["config"])

    config.load_kube_config(store_name1)
    current_api=kube_client.CoreV1Api()

    if cluster_name != "minikube":
        rq_json = current_api.read_namespaced_resource_quota(name="resource-quota-for-"+project["name"], namespace=project["name"]).status.hard
        lr_json = current_api.read_namespaced_limit_range(name="limit-range-for-"+project["name"], namespace=project["name"]).spec.limits[0].default
        assert rq_json == {'limits.cpu': '10', 'limits.memory': '512Mi'}
        assert lr_json == {'cpu': '100m', 'memory': '64Mi'}

        try:
            rq_json = current_api.read_namespaced_resource_quota(name="resource-quota-for-"+project2["name"], namespace=project2["name"]).status.hard
            lr_json = current_api.read_namespaced_limit_range(name="limit-range-for-"+project2["name"], namespace=project2["name"]).spec.limits[0].default
            assert True == False
        except:
            pass

        app.dependency_overrides[current_user] = lambda: user1
        response = client.post('project_user_management/', 
            data=json.dumps({"name": project2["name"],"region": project2["region"], "e_mail": user2.email}))
        rq_json = current_api.read_namespaced_resource_quota(name="resource-quota-for-"+project2["name"], namespace=project2["name"]).status.hard
        lr_json = current_api.read_namespaced_limit_range(name="limit-range-for-"+project2["name"], namespace=project2["name"]).spec.limits[0].default
        assert rq_json == {'limits.cpu': '10', 'limits.memory': '512Mi'}
        assert lr_json == {'cpu': '100m', 'memory': '64Mi'} 


        response = client.delete('project_user_management/user_from_project', 
            data=json.dumps({"name": project["name"],"region": project["region"], "user_id": user2.id}))
        
        try:
            rq_json = current_api.read_namespaced_resource_quota(name="resource-quota-for-"+project["name"], namespace=project["name"]).status.hard
            lr_json = current_api.read_namespaced_limit_range(name="limit-range-for-"+project["name"], namespace=project["name"]).spec.limits[0].default
            assert True == False
        except:
            pass

        rq_json = current_api.read_namespaced_resource_quota(name="resource-quota-for-"+project2["name"], namespace=project2["name"]).status.hard
        lr_json = current_api.read_namespaced_limit_range(name="limit-range-for-"+project2["name"], namespace=project2["name"]).spec.limits[0].default
        assert rq_json == {'limits.cpu': '10', 'limits.memory': '512Mi'}
        assert lr_json == {'cpu': '100m', 'memory': '64Mi'} 

        response = client.delete('project_user_management/user_from_project', 
            data=json.dumps({"name": project2["name"],"region": project2["region"], "user_id": user2.id}))

        try:
            rq_json = current_api.read_namespaced_resource_quota(name="resource-quota-for-"+project2["name"], namespace=project2["name"]).status.hard
            lr_json = current_api.read_namespaced_limit_range(name="limit-range-for-"+project2["name"], namespace=project2["name"]).spec.limits[0].default
            assert True == False
        except:
            pass


def test_update_kubeconfig(client: TestClient, session, monkeypatch):
    app.dependency_overrides = {}
    app.dependency_overrides[current_user] = lambda: user1
    response = client.post('project_user_management/', 
        data=json.dumps({"name": project["name"],"region": project["region"], "e_mail": user3.email}))
    response = client.post('project_user_management/', 
        data=json.dumps({"name": project2["name"],"region": project2["region"], "e_mail": user3.email}))

    session.execute("SELECT COUNT(*) FROM public.certificate2user WHERE region='EU1' AND user_id='"+user3.id+"'")
    assert session.fetchone()[0] == 0

    app.dependency_overrides[current_user] = lambda: user3
    counter = 0
    invalid_config = True
    while counter<=10 and invalid_config:
        response = client.get('kubernetes/generate-config', params=params)
        assert response.status_code == 201
        counter += 1
        if "client-certificate-data: None" not in response.json()["config"]:
            invalid_config = False
    store_name1 = user2.id+''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=10))+".yaml"
    with open(store_name1, "w") as text_file:
        text_file.write(response.json()["config"])

    session.execute("SELECT COUNT(*) FROM public.certificate2user WHERE region='EU1' AND user_id='"+user3.id+"'")
    assert session.fetchone()[0] == 1
    session.execute("SELECT certificate_no FROM public.certificate2user WHERE region='EU1' AND user_id='"+user3.id+"'")
    current_certificate_no = session.fetchone()[0]

    config.load_kube_config(store_name1)
    current_api1=kube_client.CoreV1Api()

    if cluster_name != "minikube":
        rq_json = current_api1.read_namespaced_resource_quota(name="resource-quota-for-"+project["name"], namespace=project["name"]).status.hard
        lr_json = current_api1.read_namespaced_limit_range(name="limit-range-for-"+project["name"], namespace=project["name"]).spec.limits[0].default
        assert rq_json == {'limits.cpu': '10', 'limits.memory': '512Mi'}
        assert lr_json == {'cpu': '100m', 'memory': '64Mi'}
        rq_json = current_api1.read_namespaced_resource_quota(name="resource-quota-for-"+project2["name"], namespace=project2["name"]).status.hard
        lr_json = current_api1.read_namespaced_limit_range(name="limit-range-for-"+project2["name"], namespace=project2["name"]).spec.limits[0].default
        assert rq_json == {'limits.cpu': '10', 'limits.memory': '512Mi'}
        assert lr_json == {'cpu': '100m', 'memory': '64Mi'} 

    counter = 0
    invalid_config = True
    while counter<=10 and invalid_config:
        response = client.get('kubernetes/generate-config', params=params)
        assert response.status_code == 201
        counter += 1
        if "client-certificate-data: None" not in response.json()["config"]:
            invalid_config = False
    store_name2 = user2.id+''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=10))+".yaml"
    with open(store_name2, "w") as text_file:
        text_file.write(response.json()["config"])

    session.execute("SELECT COUNT(*) FROM public.certificate2user WHERE region='EU1' AND user_id='"+user3.id+"'")
    assert session.fetchone()[0] == 1
    session.execute("SELECT certificate_no FROM public.certificate2user WHERE region='EU1' AND user_id='"+user3.id+"'")
    new_certificate_no = session.fetchone()[0]
    assert new_certificate_no > current_certificate_no

    config.load_kube_config(store_name2)
    current_api2=kube_client.CoreV1Api()


    if cluster_name != "minikube":
        #old api should not work
        try:
            rq_json = current_api1.read_namespaced_resource_quota(name="resource-quota-for-"+project["name"], namespace=project["name"]).status.hard
            lr_json = current_api1.read_namespaced_limit_range(name="limit-range-for-"+project["name"], namespace=project["name"]).spec.limits[0].default
            assert True == False
        except:
            pass
        try:
            rq_json = current_api1.read_namespaced_resource_quota(name="resource-quota-for-"+project2["name"], namespace=project2["name"]).status.hard
            lr_json = current_api1.read_namespaced_limit_range(name="limit-range-for-"+project2["name"], namespace=project2["name"]).spec.limits[0].default
            assert True == False
        except:
            pass

        #new api should work
        rq_json = current_api2.read_namespaced_resource_quota(name="resource-quota-for-"+project["name"], namespace=project["name"]).status.hard
        lr_json = current_api2.read_namespaced_limit_range(name="limit-range-for-"+project["name"], namespace=project["name"]).spec.limits[0].default
        assert rq_json == {'limits.cpu': '10', 'limits.memory': '512Mi'}
        assert lr_json == {'cpu': '100m', 'memory': '64Mi'}
        rq_json = current_api2.read_namespaced_resource_quota(name="resource-quota-for-"+project2["name"], namespace=project2["name"]).status.hard
        lr_json = current_api2.read_namespaced_limit_range(name="limit-range-for-"+project2["name"], namespace=project2["name"]).spec.limits[0].default
        assert rq_json == {'limits.cpu': '10', 'limits.memory': '512Mi'}
        assert lr_json == {'cpu': '100m', 'memory': '64Mi'}         
    
    monkeypatch.setattr("app.api.routes.projects.mail_project_delete", mock_mail_project_delete)
    #clean up
    app.dependency_overrides[current_user] = lambda: user1
    response = client.delete('projects/', data=json.dumps(project))
    response = client.delete('projects/', data=json.dumps(project2))

