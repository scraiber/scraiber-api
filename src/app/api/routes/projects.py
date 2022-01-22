from typing import List
from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, HTTPException, Depends
from fastapi_users.manager import BaseUserManager
from fastapi_users import models

from app.api.crud import project2user, project2external, project2ownercandidate, projects
from app.api.kubernetes import namespace, users
from app.api.models.projects import (
    ProjectPrimaryKey, 
    ProjectSchema, 
    ProjectSchemaDB, 
    Project2UserDB, 
    PrimaryKeyWithUserID, 
    ProjectPrimaryKeyEmail, 
    ProjectSchemaEmail)
from app.api.models.users import User
from app.api.routes.user_management import get_users_by_project
from app.api.email.projects import *
from app.fastapiusers import current_user, current_verified_user, get_user_manager
from app.kubernetes_setup import clusters

router = APIRouter()


@router.post("/", response_model=ProjectSchemaDB, status_code=201)
async def create_project(payload: ProjectSchema, user: User = Depends(current_verified_user)):
    if payload.name in clusters[payload.region]["blacklist"]:
        raise HTTPException(status_code=403, detail="Project already exists")

    post_project = {
        "name": payload.name,
        "region": payload.region,
        "max_project_cpu": payload.max_project_cpu, 
        "max_project_mem": payload.max_project_mem, 
        "default_limit_pod_cpu": payload.default_limit_pod_cpu, 
        "default_limit_pod_mem": payload.default_limit_pod_mem,
        "owner_id": user.id
    }
    try: 
        await projects.post(post_project)
    except UniqueViolationError:
        raise HTTPException(status_code=403, detail="Project already exists")

    await namespace.create_namespace(payload)

    try: 
        post_user = {
            "name": payload.name,
            "region": payload.region,
            "user_id": user.id,
            "is_admin": True    
        }
        await project2user.post(post_user)
    except UniqueViolationError:
        raise HTTPException(status_code=403, detail="User is already added to project")

    await users.add_user_to_namespace(PrimaryKeyWithUserID(name=payload.name, region=payload.region, candidate_id=user.id))
    await mail_project_post(ProjectPrimaryKeyEmail(name=payload.name, region=payload.region, e_mail=user.email))
    
    return post_project


@router.get("/", response_model=ProjectSchemaDB)
async def get_project(primary_key: ProjectPrimaryKey, user: User = Depends(current_user)):
    project2user_res = await project2user.get(Project2UserDB(name=primary_key.name, region=primary_key.region, user_id=user.id))
    if not project2user_res:
        raise HTTPException(status_code=404, detail="Project for user not found")

    project = await projects.get(primary_key)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.get("/by_user", response_model=List[Project2UserDB])
async def get_project_by_owner(user: User = Depends(current_user)):
    associated_projects = await project2user.get_by_user(user.id)
    if not associated_projects:
        raise HTTPException(status_code=404, detail="User not associated to any project")

    return associated_projects


@router.get("/by_owner", response_model=List[ProjectSchemaDB])
async def get_project_by_owner(user: User = Depends(current_user)):
    project2owner = await projects.get_by_owner(user.id)
    if not project2owner:
        raise HTTPException(status_code=404, detail="No project owned by user")

    return project2owner

'''
@router.get("/all", response_model=List[ProjectSchemaDB])
async def read_all_projects(user: User = Depends(current_user)):
    project2user_res = await project2user.get_by_user(user.id)
    if not project2user_res:
        raise HTTPException(status_code=404, detail="No projects for user found")
    project2user_res_deserialized = [Project2UserDB(**item).dict() for item in project2user_res]
    payload_list = [{"name": item["name"], "region": item["region"]} for item in project2user_res_deserialized]
    return await projects.get_many(payload_list)
'''

@router.put("/update_cpu_memory", response_model=ProjectSchema, status_code=200)
async def update_cpu_memory(update: ProjectSchema, user: User = Depends(current_user), user_manager: BaseUserManager[models.UC, models.UD] = Depends(get_user_manager)):
    await project2user.admin_check(Project2UserDB(name=update.name, region=update.region, user_id=user.id))
    await projects.put_cpu_mem(update)
    await namespace.update_namespace(update)

    users_to_inform = await get_users_by_project(ProjectPrimaryKey(name=update.name, region=update.region), user, user_manager)
    for user_item in users_to_inform:
        await mail_project_put(ProjectSchemaEmail(name=update.name, region=update.region,
            max_project_cpu=update.max_project_cpu, max_project_mem=update.max_project_mem,
            default_limit_pod_cpu=update.default_limit_pod_cpu, default_limit_pod_mem=update.default_limit_pod_mem,
            e_mail=user_item.email))
    return update


@router.delete("/", status_code=200)
async def delete_by_project(primary_key: ProjectPrimaryKey, user: User = Depends(current_user), user_manager: BaseUserManager[models.UC, models.UD] = Depends(get_user_manager)):
    await projects.owner_check(PrimaryKeyWithUserID(name=primary_key.name, region=primary_key.region, candidate_id=user.id))

    users_to_inform = await get_users_by_project(primary_key, user, user_manager)
    for user_item in users_to_inform:
        await mail_project_delete(ProjectPrimaryKeyEmail(name=primary_key.name, region=primary_key.region, e_mail=user_item.email))
        
    await projects.delete(primary_key)
    await namespace.delete_namespace(primary_key)
    await project2external.delete_by_project(primary_key)
    await project2ownercandidate.delete(primary_key)
    await project2user.delete_by_project(primary_key)
    return primary_key
