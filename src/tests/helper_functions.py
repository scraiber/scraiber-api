import random
import string
import json
import os
from kubernetes import client, config
from pydantic import EmailStr

from app.api.models.projects import ProjectPrimaryKeyEmail, ProjectSchemaEmail, RegionEmail, Project2ExternalDB
from app.api.models.users import UserDB


def generate_user(n=10):
    return UserDB(
        email=''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=n))+"@test.com",
        hashed_password="aaa",
        is_active=True,
        is_verified=False,
        is_superuser=False,
    )
    
def generate_project(n=10, scale=1):
    return {
        "name": random.choice(string.ascii_lowercase)+''.join(random.choices(string.ascii_lowercase + string.digits+"-", k=n-2))+random.choice(string.ascii_lowercase),
        "region": "EU1", 
        "max_project_cpu": scale*10, 
        "max_project_mem": scale*512, 
        "default_limit_pod_cpu": scale*0.1, 
        "default_limit_pod_mem": scale*64
    }

def generate_project_blacklist(name, scale=1):
    return {
        "name": name,
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



async def mock_mail_kubernetes_new_kubeconfig(payload: RegionEmail):
    return "Mock e-mail"



async def mock_mail_um_post_internal(payload: Project2ExternalDB):
    return "Mock e-mail"

async def mock_mail_um_post_internal_owner(payload: Project2ExternalDB, owner_email: EmailStr):
    return "Mock e-mail"

async def mock_mail_um_post_external(payload: Project2ExternalDB):
    return "Mock e-mail"

async def mock_mail_um_put_owner(payload: Project2ExternalDB, owner_email: EmailStr):
    return "Mock e-mail"

async def mock_mail_um_put_changed_user(payload: Project2ExternalDB):
    return "Mock e-mail"

async def mock_mail_um_delete_external(payload: ProjectPrimaryKeyEmail, owner_email: EmailStr):
    return "Mock e-mail"

async def mock_mail_um_delete_all_externals(payload: ProjectPrimaryKeyEmail):
    return "Mock e-mail"

async def mock_mail_um_delete_owner(payload: Project2ExternalDB, owner_email: EmailStr):
    return "Mock e-mail"

async def mock_mail_um_delete_deleted_user(payload: Project2ExternalDB):
    return "Mock e-mail"



async def mock_mail_ot_post(payload: ProjectPrimaryKeyEmail):
    return "Mock e-mail"

async def mock_mail_project_put_old_owner(payload: ProjectPrimaryKeyEmail):
    return "Mock e-mail"   

async def mock_mail_project_put_new_owner(payload: ProjectPrimaryKeyEmail):
    return "Mock e-mail"  

async def mock_mail_project_delete_inform_owner(payload: ProjectPrimaryKeyEmail):
    return "Mock e-mail"

async def mock_mail_project_delete_inform_candidate(payload: ProjectPrimaryKeyEmail):
    return "Mock e-mail"



async def mock_mail_registration_confirmation(email: EmailStr):
    return "Mock e-mail"



async def mock_test_mail(email):
    return "Mock e-mail"




def generate_kubernetes_client():
    cluster_name = json.loads(os.environ['CLUSTER_DICT'])["EU1"]["Config-Name"]
    config.load_kube_config("config.yaml", context=cluster_name)
    return client.CoreV1Api()