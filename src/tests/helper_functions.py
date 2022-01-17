import random
import string
import json
import os
from kubernetes import client, config

from app.api.models.projects import ProjectPrimaryKeyEmail, ProjectSchemaEmail
from app.api.models.users import UserDB


def generate_user(n=10):
    return UserDB(
        email=''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=n))+"@test.com",
        hashed_password="aaa",
        is_active=True,
        is_verified=False,
        is_superuser=False,
    )

    return {
        "email": ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=n))+"@test.com",
        "password":"asdf1234",
        "user_id": "",
        "token": "",
        "hashed_pw": ""
    }

def generate_user2(n=10):
    return {
        "email": ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=n))+"@test.com",
        "password":"asdf1234",
        "user_id": "",
        "token": "",
        "hashed_pw": ""
    }
    
def generate_project(n=10, scale=1):
    return {
        "name": random.choice(string.ascii_lowercase)+''.join(random.choices(string.ascii_lowercase + string.digits+"-", k=n-2))+random.choice(string.ascii_lowercase),
        "region": "EU1", 
        "max_project_cpu": scale*10, 
        "max_project_mem": scale*512, 
        "default_limit_pod_cpu": scale*0.1, 
        "default_limit_pod_mem": scale*64
    }


async def mock_mail_project_post(payload: ProjectPrimaryKeyEmail):
    return "Mock e-mail"

async def mock_mail_project_put(payload: ProjectSchemaEmail):
    return "Mock e-mail"

async def mock_mail_project_delete(payload: ProjectPrimaryKeyEmail):
    return "Mock e-mail"

async def mock_test_mail(email):
    return "Mock e-mail"


def generate_kubernetes_client():
    cluster_name = json.loads(os.environ['CLUSTER_DICT'])["EU1"]["Config-Name"]
    config.load_kube_config("config.yaml", context=cluster_name)
    return client.CoreV1Api()