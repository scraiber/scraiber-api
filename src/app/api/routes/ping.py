from fastapi import APIRouter
from fastapi import Depends
from kubernetes import client
import pprint

from app.api.models.users import User
from app.fastapiusers import current_user
from app.kubernetes_setup import clusters
from app.api.models.projects import ProjectSchema, ProjectPrimaryKey, PrimaryKeyWithUserID
from app.api.kubernetes.namespace import create_namespace, update_namespace, delete_namespace
from app.api.kubernetes.users import add_user_to_namespace, patch_kubernetes_user, delete_role_bindings_for_user, create_kubernetes_config


router = APIRouter()

@router.get("/ping")
async def pong():
    # some async operation could happen here
    # example: `notes = await get_all_notes()`
    return {"ping": "pong!"}

@router.get("/protected-route")
def protected_route(user: User = Depends(current_user)):
    return f"Hello, {user.email}"


@router.get("/create-namespace")
async def create_namespace_here(payload: ProjectSchema):
    return await create_namespace(payload)

@router.get("/update-namespace")
async def update_namespace_here(payload: ProjectSchema):
    return await update_namespace(payload)

@router.get("/delete-namespace")
async def delete_namespace_here(payload: ProjectPrimaryKey):
    return await delete_namespace(payload)

@router.get("/create-user")
async def create_user_here(payload: PrimaryKeyWithUserID):
    return await add_user_to_namespace(payload)

@router.get("/patch-user")
async def delete_user_here(payload: PrimaryKeyWithUserID):
    return await patch_kubernetes_user(payload)

@router.get("/delete-user")
async def delete_user_here(payload: PrimaryKeyWithUserID):
    return await delete_role_bindings_for_user(payload)

@router.get("/retrieve-user")
async def retrieve_user_here(payload: PrimaryKeyWithUserID):
    return await create_kubernetes_config(payload)