from fastapi import APIRouter, HTTPException, Depends
from asyncpg.exceptions import UniqueViolationError
from typing import List

from app.api.kubernetes import users
from app.api.crud import project2external, project2user, projects
from app.api.models.projects import PrimaryKeyWithUserID, Project2UserDB, ProjectPrimaryKey, ProjectSchemaDB, Project2ExternalDB, ProjectPrimaryKeyEmail
from app.api.models.auth0 import Auth0User
from app.auth0 import current_user
from app.api.auth0.users import get_user_by_email, get_user_by_id, get_user_list_by_id
from app.api.email.user_management import *


router = APIRouter()


@router.post("/", response_model=Project2ExternalDB, status_code=201)
async def add_user_or_invite_external(primary_key: Project2ExternalDB, user: Auth0User = Depends(current_user)):
    await project2user.admin_check(Project2UserDB(name=primary_key.name, region=primary_key.region, user_id=user.user_id))

    try:
        user_by_email = await get_user_by_email(primary_key.e_mail)
        user_exists = True
    except HTTPException:
        user_exists = False

    if user_exists:
        try:
            post_user = {
                "name": primary_key.name,
                "region": primary_key.region,
                "user_id": user_by_email.user_id,
                "is_admin": primary_key.is_admin    
            }
            await project2user.post(post_user)
            await users.add_user_to_namespace(PrimaryKeyWithUserID(name=primary_key.name, region=primary_key.region, candidate_id=user_by_email.user_id))
            await mail_um_post_internal(primary_key)

            project = await projects.get(ProjectPrimaryKey(name=primary_key.name, region=primary_key.region))
            project_deserialized = ProjectSchemaDB(**project)
            try:
                owner_res = await get_user_by_id(project_deserialized.owner_id) 
                owner_email = owner_res.email
                await mail_um_post_internal_owner(primary_key, owner_email)
            except:
                pass
        except:
            raise HTTPException(status_code=403, detail="Item already exists")   
    else:
        try:
            post_user = {
                "name": primary_key.name,
                "region": primary_key.region,
                "e_mail": primary_key.e_mail,
                "is_admin": primary_key.is_admin    
            }
            await project2external.post(post_user)
            await mail_um_post_external(primary_key)
        except:
            raise HTTPException(status_code=403, detail="Item already exists")            
    return primary_key


@router.get("/externals_by_project", response_model=List[Project2ExternalDB])
async def get_externals_by_project(primary_key: ProjectPrimaryKey, user: Auth0User = Depends(current_user)):
    await project2user.admin_check(Project2UserDB(name=primary_key.name, region=primary_key.region, user_id=user.user_id))
    project2user_res = await project2external.get_by_project(primary_key)
    if not project2user_res:
        raise HTTPException(status_code=404, detail="No externals for project found")
    return project2user_res


@router.get("/users_by_project", response_model=List[Auth0User])
async def get_users_by_project(primary_key: ProjectPrimaryKey, user: Auth0User = Depends(current_user)) -> List[Auth0User]:
    await project2user.admin_check(Project2UserDB(name=primary_key.name, region=primary_key.region, user_id=user.user_id))
    project2user_res = await project2user.get_by_project(primary_key)
    if not project2user_res:
        raise HTTPException(status_code=404, detail="No users for project found")
    
    project2user_res_deserialized = [Project2UserDB(**item) for item in project2user_res]
    project2user_res_id = [item.user_id for item in project2user_res_deserialized]

    return await get_user_list_by_id(project2user_res_id)


@router.put("/admin_state", response_model=Project2UserDB, status_code=200)
async def update_admin_state(update: Project2UserDB, user: Auth0User = Depends(current_user)):
    await project2user.admin_check(Project2UserDB(name=update.name, region=update.region, user_id=user.user_id))
    project = await projects.get(ProjectPrimaryKey(name=update.name, region=update.region))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_deserialized = ProjectSchemaDB(**project)
    if project_deserialized.owner_id == update.user_id:
        raise HTTPException(status_code=401, detail="The owner's admin state cannot be changed")

    await project2user.put_admin_state(update)

    user_res = await get_user_by_id(update.user_id) 
    
    try:
        owner_res = await get_user_by_id(project_deserialized.owner_id) 
    except HTTPException:
        raise HTTPException(status_code=404, detail="Owner not found")
        
    payload = Project2ExternalDB(name=update.name, region=update.region, e_mail=user_res.email, is_admin=update.is_admin)
    owner_email = owner_res.email
    changer_email = user.email

    if changer_email != owner_email:
        await mail_um_put_owner(payload, owner_email)
    if changer_email != payload.e_mail:
        await mail_um_put_changed_user(payload)
    return update


@router.delete("/external_from_project")
async def delete_external_from_project(primary_key: Project2ExternalDB, user: Auth0User = Depends(current_user)):
    await project2user.admin_check(Project2UserDB(name=primary_key.name, region=primary_key.region, user_id=user.user_id))

    project = await projects.get(ProjectPrimaryKey(name=primary_key.name, region=primary_key.region))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_deserialized = ProjectSchemaDB(**project)
    try:
        owner_res = await get_user_by_id(project_deserialized.owner_id) 
    except HTTPException:
        raise HTTPException(status_code=404, detail="Owner not found")   
    owner_email = owner_res.email

    await project2external.delete(primary_key)
    await mail_um_delete_external(ProjectPrimaryKeyEmail(name=primary_key.name, region=primary_key.region, e_mail=user.email), owner_email)
    return "No record remaining"


@router.delete("/all_externals_from_project")
async def delete_all_externals_from_project(primary_key: ProjectPrimaryKey, user: Auth0User = Depends(current_user)):
    await project2user.admin_check(Project2UserDB(name=primary_key.name, region=primary_key.region, user_id=user.user_id))

    project = await projects.get(ProjectPrimaryKey(name=primary_key.name, region=primary_key.region))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_deserialized = ProjectSchemaDB(**project)
    try:
        owner_res = await get_user_by_id(project_deserialized.owner_id) 
    except HTTPException:
        raise HTTPException(status_code=404, detail="Owner not found")      
    owner_email = owner_res.email

    await project2external.delete_by_project(primary_key)
    await mail_um_delete_all_externals(ProjectPrimaryKeyEmail(name=primary_key.name, region=primary_key.region, e_mail=owner_email))
    return "No records remaining"


@router.delete("/user_from_project")
async def delete_user_from_project(payload: Project2UserDB, user: Auth0User = Depends(current_user)):
    if payload.user_id != user.user_id:
        await project2user.admin_check(Project2UserDB(name=payload.name, region=payload.region, user_id=user.user_id))

    project = await projects.get(ProjectPrimaryKey(name=payload.name, region=payload.region))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_deserialized = ProjectSchemaDB(**project)
    if project_deserialized.owner_id == payload.user_id:
        raise HTTPException(status_code=401, detail="The owner cannot be deleted")

    await project2user.delete(payload)
    await users.delete_kubernetes_user(PrimaryKeyWithUserID(name=payload.name, region=payload.region, candidate_id=payload.user_id))
        
    user_res = await get_user_by_id(payload.user_id) 
    
    try:
        owner_res = await get_user_by_id(project_deserialized.owner_id) 
    except HTTPException:
        raise HTTPException(status_code=404, detail="Owner not found")
        
    payload_email = Project2ExternalDB(name=payload.name, region=payload.region, e_mail=user_res.email, is_admin=payload.is_admin)
    owner_email = owner_res.email
    changer_email = user.email

    if changer_email != owner_email:
        await mail_um_delete_owner(payload_email, owner_email)
    if changer_email != user_res.email:
        await mail_um_delete_deleted_user(payload_email)

    return "No record remaining"
