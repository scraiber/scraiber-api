from fastapi import APIRouter, HTTPException, Depends
from fastapi_users.manager import BaseUserManager
from fastapi_users import models
from asyncpg.exceptions import UniqueViolationError
from typing import List

from app.api.crud import project2user, projects, project2ownercandidate
from app.api.models.projects import Project2UserDB, ProjectPrimaryKey, ProjectPrimaryKeyEmail, PrimaryKeyWithUserID, ProjectSchemaDB
from app.api.models.users import User, UserDB
from app.api.routes.projects import get_project
from app.fastapiusers import current_user, current_verified_user, get_user_manager
from app.api.email.owner_transfer import *




router = APIRouter()


@router.post("/", response_model=PrimaryKeyWithUserID, status_code=201)
async def add_owner_candidate(primary_key: ProjectPrimaryKeyEmail, user: User = Depends(current_user), user_manager: BaseUserManager[models.UC, models.UD] = Depends(get_user_manager)):
    await projects.owner_check(PrimaryKeyWithUserID(name=primary_key.name, region=primary_key.region, candidate_id=user.id))
    
    candidate_existence_check = await project2ownercandidate.get_by_project(ProjectPrimaryKey(name=primary_key.name, region=primary_key.region))
    if candidate_existence_check:
        raise HTTPException(status_code=401, detail="Please delete the already existent candidate first")

    try:
        user_by_email = await user_manager.get_by_email(primary_key.e_mail)
    except:
        raise HTTPException(status_code=404, detail="User not found")

#    if user_by_email.is_verified == False:
#        raise HTTPException(status_code=403, detail="User e-mail of new owner candidate is not verified")

    if not await project2user.get(Project2UserDB(name=primary_key.name, region=primary_key.region, user_id=user_by_email.id)):
        raise HTTPException(status_code=403, detail="User not assigned to project")

    try:
        payload = {
            "name": primary_key.name,
            "region": primary_key.region,
            "candidate_id": user_by_email.id
        }
        await project2ownercandidate.post(payload)
        await mail_ot_post(primary_key)
    except UniqueViolationError:
        raise HTTPException(status_code=403, detail="Item already exists")            
    return payload


@router.get("/owner_candidate_by_project", response_model=UserDB)
async def get_owner_candidate_by_project(primary_key: ProjectPrimaryKey, user: User = Depends(current_user), user_manager: BaseUserManager[models.UC, models.UD] = Depends(get_user_manager)):
    await projects.owner_check(PrimaryKeyWithUserID(name=primary_key.name, region=primary_key.region, candidate_id=user.id))

    project2candidate_res = await project2ownercandidate.get_by_project(primary_key)
    if not project2candidate_res:
        raise HTTPException(status_code=404, detail="No associated owner candidate found")
    
    project2candidate_res_deserialized = PrimaryKeyWithUserID(**project2candidate_res)
    return await user_manager.get(project2candidate_res_deserialized.candidate_id) 


@router.get("/projects_for_owner_candidate", response_model=List[PrimaryKeyWithUserID])
async def get_projects_for_owner_candidate(user: User = Depends(current_user)):
    project2user_res = await project2ownercandidate.get_by_candidate(user.id)
    if not project2user_res:
        raise HTTPException(status_code=404, detail="User is nowhere owner candidate")
    return project2user_res


@router.put("/accept", response_model=PrimaryKeyWithUserID, status_code=200)
async def accept(primary_key: ProjectPrimaryKey, user: User = Depends(current_verified_user), user_manager: BaseUserManager[models.UC, models.UD] = Depends(get_user_manager)):
    change_model = PrimaryKeyWithUserID(name=primary_key.name, region=primary_key.region, candidate_id=user.id)
    project2user_res = await project2ownercandidate.get_by_project_and_candidate(change_model)
    if not project2user_res:
        raise HTTPException(status_code=404, detail="User not owner candidate for project or project not found")

    project = await projects.get(ProjectPrimaryKey(name=primary_key.name, region=primary_key.region))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_deserialized = ProjectSchemaDB(**project)

    owner_res = await user_manager.get(project_deserialized.owner_id) 
    if not owner_res:
        raise HTTPException(status_code=404, detail="Owner not found")        

    await projects.put_owner(change_model)
    await project2ownercandidate.delete(primary_key)
    await project2user.put_admin_state(Project2UserDB(name=primary_key.name, region=primary_key.region, user_id=user.id, is_admin=True))

    await mail_project_put_old_owner(ProjectPrimaryKeyEmail(name=primary_key.name, region=primary_key.region, e_mail=owner_res.email))
    await mail_project_put_new_owner(ProjectPrimaryKeyEmail(name=primary_key.name, region=primary_key.region, e_mail=user.email))

    return change_model


@router.delete("/candidate_for_project")
async def delete_candidate_for_project(primary_key: ProjectPrimaryKey, user: User = Depends(current_user), user_manager: BaseUserManager[models.UC, models.UD] = Depends(get_user_manager)):
    await projects.owner_check(PrimaryKeyWithUserID(name=primary_key.name, region=primary_key.region, candidate_id=user.id))

    project_candidate = await project2ownercandidate.get_by_project(primary_key)
    if not project_candidate:
        raise HTTPException(status_code=404, detail="No owner candidate for project")
    project_candidate_deserialized = PrimaryKeyWithUserID(**project_candidate)

    await project2ownercandidate.delete(primary_key)

    candidate_res = await user_manager.get(project_candidate_deserialized.candidate_id) 
    if not candidate_res:
        raise HTTPException(status_code=404, detail="Candidate not found")   
    await mail_project_delete_inform_candidate(ProjectPrimaryKeyEmail(name=primary_key.name, region=primary_key.region, e_mail=candidate_res.email))

    return "No record remaining"


@router.delete("/project_for_candidate")
async def delete_project_for_candidate(primary_key: ProjectPrimaryKey, user: User = Depends(current_user), user_manager: BaseUserManager[models.UC, models.UD] = Depends(get_user_manager)):
    if not await project2ownercandidate.get_by_project_and_candidate(PrimaryKeyWithUserID(name=primary_key.name, region=primary_key.region, candidate_id=user.id)):
        raise HTTPException(status_code=404, detail="User not owner candidate for project or project not found")

    await project2ownercandidate.delete(primary_key)

    project = await projects.get(ProjectPrimaryKey(name=primary_key.name, region=primary_key.region))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_deserialized = ProjectSchemaDB(**project)

    owner_res = await user_manager.get(project_deserialized.owner_id) 
    if not owner_res:
        raise HTTPException(status_code=404, detail="Owner not found")
    await mail_project_delete_inform_owner(ProjectPrimaryKeyEmail(name=primary_key.name, region=primary_key.region, e_mail=owner_res.email))

    return "No record remaining"


@router.delete("/all_projects_for_candidate")
async def delete_all_projects_for_candidate(user: User = Depends(current_user), user_manager: BaseUserManager[models.UC, models.UD] = Depends(get_user_manager)):
    projects4candidate = await get_projects_for_owner_candidate(user)

    for project2candidate_item in projects4candidate:
        try:
            project_item = await projects.get(ProjectPrimaryKey(name=project2candidate_item.name, region=project2candidate_item.region))
            if not project_item:
                raise HTTPException(status_code=404, detail="Project not found")
            project_deserialized = ProjectSchemaDB(**project_item)

            owner_res = await user_manager.get(project_deserialized.owner_id) 
            if not owner_res:
                raise HTTPException(status_code=404, detail="Owner not found")
            await mail_project_delete_inform_owner(ProjectPrimaryKeyEmail(name=project2candidate_item.name, region=project2candidate_item.region, e_mail=owner_res.email))
        except:
            pass 

    await project2ownercandidate.delete_by_candidate(user.id)
    return "No records remaining"