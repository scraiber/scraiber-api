from fastapi import APIRouter, HTTPException, Depends
from fastapi_users.manager import BaseUserManager, UserNotExists
from fastapi_users import models
from asyncpg.exceptions import UniqueViolationError
from typing import List

from app.api.crud import project2external, project2user, projects
from app.api.models.projects import Project2UserDB, ProjectPrimaryKey, ProjectSchemaDB, Project2ExternalDB
from app.api.models.users import User
from app.fastapiusers import current_user, get_user_manager




router = APIRouter()


@router.post("/", response_model=Project2ExternalDB, status_code=201)
async def add_user_or_invite_eternal(primary_key: Project2ExternalDB, user: User = Depends(current_user), user_manager: BaseUserManager[models.UC, models.UD] = Depends(get_user_manager)):
    project = await projects.get(primary_key)
    if not project or ProjectSchemaDB(**project).owner_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found or user not owner")

    try:
        user_by_email = await user_manager.get_by_email(primary_key.e_mail)
        try:
            payload = {
                "name": primary_key.name,
                "region": primary_key.region,
                "user_id": user_by_email.id
            }
            await project2user.post(payload)
            #TODO: Write e-mail to user
        except UniqueViolationError:
            raise HTTPException(status_code=403, detail="Item already exists")   
    except UserNotExists:
        try:
            payload = {
                "name": primary_key.name,
                "region": primary_key.region,
                "e_mail": primary_key.e_mail
            }
            await project2external.post(payload)
            #TODO: Write e-mail to recipient
        except UniqueViolationError:
            raise HTTPException(status_code=403, detail="Item already exists")            
    return primary_key


@router.get("/externals_by_project", response_model=List[Project2ExternalDB])
async def get_externals_by_project(primary_key: ProjectPrimaryKey, user: User = Depends(current_user)):
    project = await projects.get(primary_key)
    if not project or ProjectSchemaDB(**project).owner_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found or user not owner")

    project2user_res = await project2external.get_by_project(primary_key)
    if not project2user_res:
        raise HTTPException(status_code=404, detail="Project for user not found")
    return project2user_res


@router.get("/users_by_project", response_model=List[Project2UserDB])
async def get_externals_by_project(primary_key: ProjectPrimaryKey, user: User = Depends(current_user)):
    project = await projects.get(primary_key)
    if not project or ProjectSchemaDB(**project).owner_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found or user not owner")

    project2user_res = await project2user.get_by_project(primary_key)
    if not project2user_res:
        raise HTTPException(status_code=404, detail="Project for user not found")
    return project2user_res


@router.delete("/external_from_project")
async def delete_external_from_project(primary_key: Project2ExternalDB, user: User = Depends(current_user)):
    project = await projects.get(primary_key)
    if not project or ProjectSchemaDB(**project).owner_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found or user not owner")

    #TODO: Write e-mail to owner and associated users about the deletion
    await project2external.delete(primary_key)
    return "No record remaining"


@router.delete("/externals_from_project")
async def delete_externals_from_project(primary_key: ProjectPrimaryKey, user: User = Depends(current_user)):
    project = await projects.get(primary_key)
    if not project or ProjectSchemaDB(**project).owner_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found or user not owner")

    #TODO: Write e-mail to owner and associated users about the deletion
    await project2external.delete_by_project(primary_key)
    return "No records remaining"


@router.delete("/user_from_project")
async def delete_user_from_project(primary_key: Project2UserDB, user: User = Depends(current_user)):
    project = await projects.get(primary_key)
    if not project or ProjectSchemaDB(**project).owner_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found or user not owner")

    #TODO: Write e-mail to owner and associated users about the deletion
    await project2user.delete(primary_key)
    return "No record remaining"


@router.delete("/users_from_project")
async def delete_users_from_project(primary_key: ProjectPrimaryKey, user: User = Depends(current_user)):
    project = await projects.get(primary_key)
    if not project or ProjectSchemaDB(**project).owner_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found or user not owner")

    #TODO: Write e-mail to owner and associated users about the deletion
    await project2user.delete_by_project(primary_key)
    return "No records remaining"