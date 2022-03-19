import random
import string
import json
import os
from kubernetes import client, config
from pydantic import EmailStr
from typing import List

from app.api.models.projects import ProjectPrimaryKeyEmail, Project2ExternalDB
from app.api.models.auth0 import Auth0User


def generate_user(n=10):
    return Auth0User(
        name=''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=n)),
        email=''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=n))+"@test.com",
        sub="auth0|"+''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=n)),
        email_verified=True,
        nickname=''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=n)),
    )

    
def generate_get_user_by_email(user_list: List[Auth0User]):
    async def output_function(email: EmailStr):
        for user in user_list:
            if user.email == email:
                return user
    return output_function

def generate_get_user_by_id(user_list: List[Auth0User]):
    async def output_function(id: str):
        for user in user_list:
            if user.user_id == id:
                return user
    return output_function

def generate_get_user_list_by_email(user_list: List[Auth0User]):
    async def output_function(email_list: List[EmailStr]) -> List[Auth0User]:
        output_list = []
        for user in user_list:
            if user.email in email_list:
                output_list.append(user)
        return output_list
    return output_function

def generate_get_user_list_by_id(user_list: List[Auth0User]):
    async def output_function(id_list: List[str]) -> List[Auth0User]:
        output_list = []
        for user in user_list:
            if user.user_id in id_list:
                output_list.append(user)
        return output_list
    return output_function


def generate_project(n=10, scale=1):
    return {
        "name": random.choice(string.ascii_lowercase)+''.join(random.choices(string.ascii_lowercase + string.digits+"-", k=n-2))+random.choice(string.ascii_lowercase),
    }


def generate_namespace(n=10, scale=1):
    return {
        "name": random.choice(string.ascii_lowercase)+''.join(random.choices(string.ascii_lowercase + string.digits+"-", k=n-2))+random.choice(string.ascii_lowercase),
        "region": "EU1",
        "max_namespace_cpu": scale*10,
        "max_namespace_mem": scale*512,
        "default_limit_pod_cpu": scale*0.1,
        "default_limit_pod_mem": scale*64
    }


def generate_namespace_blacklist(name, scale=1):
    return {
        "name": name,
        "region": "EU1",
        "max_namespace_cpu": scale*10,
        "max_namespace_mem": scale*512,
        "default_limit_pod_cpu": scale*0.1,
        "default_limit_pod_mem": scale*64
    }

def generate_external(n=10):
    return {
        "e_mail": ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=n))+"@test.com"
    }

def generate_kubernetes_client():
    cluster_name = json.loads(os.environ['CLUSTER_DICT'])["EU1"]["Config-Name"]
    config.load_kube_config("config.yaml", context=cluster_name)
    return client.CoreV1Api()