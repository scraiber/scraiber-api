from fastapi import APIRouter, HTTPException, Depends
from fastapi_users.manager import BaseUserManager, UserNotExists
from fastapi_users import models
from asyncpg.exceptions import UniqueViolationError
from typing import List
from pydantic.networks import EmailStr

from app.api.crud import project2external, project2user, projects
from app.api.models.projects import Project2UserDB, ProjectPrimaryKey, ProjectSchemaDB, Project2ExternalDB
from app.api.models.users import User
from app.fastapiusers import current_user, get_user_manager




router = APIRouter()


@router.post("/", response_model=Project2ExternalDB, status_code=201)
async def add_user_or_invite_external(primary_key: Project2ExternalDB, user: User = Depends(current_user), user_manager: BaseUserManager[models.UC, models.UD] = Depends(get_user_manager)):
    await project2user.admin_check(Project2UserDB(name=primary_key.name, region=primary_key.region, user_id=user.id))

    try:
        user_by_email = await user_manager.get_by_email(primary_key.e_mail)
        try:
            await project2user.post(Project2UserDB(name=primary_key.name, region=primary_key.region, user_id=user_by_email.id, is_admin=primary_key.is_admin))
            #TODO: Write e-mail to user
        except UniqueViolationError:
            raise HTTPException(status_code=403, detail="Item already exists")   
    except UserNotExists:
        try:
            await project2external.post(Project2ExternalDB(name=primary_key.name, region=primary_key.region, e_mail=primary_key.e_mail, is_admin=primary_key.is_admin))
            #TODO: Write e-mail to recipient
        except UniqueViolationError:
            raise HTTPException(status_code=403, detail="Item already exists")            
    return primary_key


@router.get("/externals_by_project", response_model=List[Project2ExternalDB])
async def get_externals_by_project(primary_key: ProjectPrimaryKey, user: User = Depends(current_user)):
    await project2user.admin_check(Project2UserDB(name=primary_key.name, region=primary_key.region, user_id=user.id))

    project2user_res = await project2external.get_by_project(primary_key)
    if not project2user_res:
        raise HTTPException(status_code=404, detail="No externals for project found")
    return project2user_res


@router.get("/users_by_project", response_model=List[User])
async def get_externals_by_project(primary_key: ProjectPrimaryKey, user: User = Depends(current_user), user_manager: BaseUserManager[models.UC, models.UD] = Depends(get_user_manager)):
    await project2user.admin_check(Project2UserDB(name=primary_key.name, region=primary_key.region, user_id=user.id))

    project2user_res = await project2user.get_by_project(primary_key)
    if not project2user_res:
        raise HTTPException(status_code=404, detail="No users for users found")
    
    project2user_res_deserialized = [Project2UserDB(**item).dict() for item in project2user_res]
    output = []
    for item in project2user_res_deserialized:
        user_res = await user_manager.get(item.id) 
        if not user_res:
            next
        output.append(user_res)

    return output


@router.put("/admin_state", response_model=ProjectSchemaDB, status_code=200)
async def update_admin_state(update: Project2UserDB, user: User = Depends(current_user)):
    await project2user.admin_check(Project2UserDB(name=update.name, region=update.region, user_id=user.id))
    project = await projects.get(ProjectPrimaryKey(name=update.name, region=update.region))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_deserialized = ProjectSchemaDB(**project)
    if project_deserialized.owner_id == update.user_id:
        raise HTTPException(status_code=401, detail="The owner's admin state cannot be changed")

    update_res = await project2user.put_admin_state(update)
    if not update_res:
        raise HTTPException(status_code=404, detail="Update item not found")
    #TODO: Write e-mail to owner resp. users about the update
    return update


@router.delete("/external_from_project")
async def delete_external_from_project(primary_key: Project2ExternalDB, email_to_delete: EmailStr, user: User = Depends(current_user)):
    await project2user.admin_check(Project2UserDB(name=primary_key.name, region=primary_key.region, user_id=user.id))

    #TODO: Write e-mail to owner and associated users about the deletion
    await project2external.delete(primary_key)
    return "No record remaining"


@router.delete("/all_externals_from_project")
async def delete_all_externals_from_project(primary_key: ProjectPrimaryKey, user: User = Depends(current_user)):
    await project2user.admin_check(Project2UserDB(name=primary_key.name, region=primary_key.region, user_id=user.id))

    #TODO: Write e-mail to owner and associated users about the deletion
    await project2external.delete_by_project(primary_key)
    return "No records remaining"


@router.delete("/user_from_project")
async def delete_user_from_project(primary_key: Project2UserDB, user_to_delete: User, user: User = Depends(current_user)):
    if user_to_delete != user:
        await project2user.admin_check(Project2UserDB(name=primary_key.name, region=primary_key.region, user_id=user.id))

    project = await projects.get(ProjectPrimaryKey(name=primary_key.name, region=primary_key.region))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_deserialized = ProjectSchemaDB(**project)
    if project_deserialized.owner_id == user_to_delete.user_id:
        raise HTTPException(status_code=401, detail="The owner cannot be deleted changed")
    #TODO: Write e-mail to owner and associated users about the deletion
    await project2user.delete(primary_key)
    return "No record remaining"

"""
@router.delete("/all_users_from_project")
async def delete_all_users_from_project(primary_key: ProjectPrimaryKey, user: User = Depends(current_user)):
    await project2user.admin_check(Project2UserDB(name=primary_key.name, region=primary_key.region, user_id=user.id))

    #TODO: Write e-mail to owner and associated users about the deletion
    await project2user.delete_by_project(primary_key)
    return "No records remaining"
"""