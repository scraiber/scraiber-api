from fastapi import APIRouter, HTTPException, Depends
from fastapi_users.manager import BaseUserManager
from fastapi_users import models
from asyncpg.exceptions import UniqueViolationError
from typing import List

from pydantic.networks import EmailStr

from app.api.crud import project2external, project2user, projects, project2ownercandidate
from app.api.models.projects import Project2UserDB, ProjectPrimaryKey, ProjectSchemaDB, Project2ExternalDB, Project2OwnerCandidateDB
from app.api.models.users import User
from app.fastapiusers import current_user, current_active_user, get_user_manager




router = APIRouter()


@router.post("/", response_model=Project2OwnerCandidateDB, status_code=201)
async def add_owner_candidate(primary_key: Project2ExternalDB, user: User = Depends(current_user), user_manager: BaseUserManager[models.UC, models.UD] = Depends(get_user_manager)):
    await projects.owner_check(Project2OwnerCandidateDB(name=primary_key.name, region=primary_key.region, candidate_id=user.id))
    
    candidate_existence_check = await project2ownercandidate.get(ProjectPrimaryKey(name=primary_key.name, region=primary_key.region))
    if candidate_existence_check:
        raise HTTPException(status_code=401, detail="Please delete the already existent candidate first")

    user_by_email = await user_manager.get_by_email(primary_key.e_mail)
    if not  user_by_email:
        raise HTTPException(status_code=404, detail="User not found")
    if user_by_email.is_verified == False:
        raise HTTPException(status_code=401, detail="User e-mail of new owner candidate is not verified")

    try:
        payload = {
            "name": primary_key.name,
            "region": primary_key.region,
            "user_id": user_by_email.id
        }
        await project2ownercandidate.post(payload)
        #TODO: Write e-mail to user
    except UniqueViolationError:
        raise HTTPException(status_code=403, detail="Item already exists")            
    return primary_key


@router.get("/owner_candidate_by_project", response_model=List[Project2UserDB])
async def get_owner_candidates_by_project(primary_key: ProjectPrimaryKey, user: User = Depends(current_user), user_manager: BaseUserManager[models.UC, models.UD] = Depends(get_user_manager)):
    await projects.owner_check(Project2OwnerCandidateDB(name=primary_key.name, region=primary_key.region, candidate_id=user.id))

    project2candidate_res = await project2ownercandidate.get(primary_key)
    if not project2candidate_res:
        raise HTTPException(status_code=404, detail="No associated owner candidate found")
    
    project2candidate_res_deserialized = Project2OwnerCandidateDB(**project2candidate_res).dict()
    return await user_manager.get(project2candidate_res_deserialized.id) 


@router.get("/projects_for_owner_candidate", response_model=List[Project2UserDB])
async def get_projects_for_owner_candidate(user: User = Depends(current_user)):
    project2user_res = await project2ownercandidate.get_by_candidate(user.id)
    if not project2user_res:
        raise HTTPException(status_code=404, detail="User is nowhere owner candidate")
    return project2user_res


@router.put("/accept", response_model=Project2OwnerCandidateDB, status_code=200)
async def accept(primary_key: ProjectPrimaryKey, user: User = Depends(current_active_user)):
    change_model = Project2OwnerCandidateDB(name=primary_key.name, region=primary_key.region, candidate_id=user.id)
    project2user_res = await project2ownercandidate.get(change_model)
    if not project2user_res:
        raise HTTPException(status_code=404, detail="User not owner candidate for project or project not found")

    project = await projects.get(ProjectPrimaryKey(name=primary_key.name, region=primary_key.region))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await projects.put_owner(change_model)
    await project2ownercandidate.delete(primary_key)
    await project2user.put_admin_state(Project2UserDB(name=primary_key.name, region=primary_key.region, user_id=user.id, is_admin=True))
    #TODO: Write e-mail to owner resp. users about the update
    return change_model


@router.delete("/candidate_for_project")
async def delete_candidate_for_project(primary_key: Project2ExternalDB, user: User = Depends(current_user)):
    await projects.owner_check(Project2OwnerCandidateDB(name=primary_key.name, region=primary_key.region, candidate_id=user.id))

    if not await project2ownercandidate.get(primary_key):
        raise HTTPException(status_code=404, detail="No owner candidate for project")
    #TODO: Write e-mail to owner and associated users about the deletion
    await project2ownercandidate.delete(primary_key)
    return "No record remaining"


@router.delete("/project_for_candidate")
async def delete_project_for_candidate(primary_key: ProjectPrimaryKey, user: User = Depends(current_user)):
    if not await project2ownercandidate.get(Project2OwnerCandidateDB(name=primary_key.name, region=primary_key.region, candidate_id=user.id)):
        raise HTTPException(status_code=404, detail="User not owner candidate for project or project not found")

    #TODO: Write e-mail to owner and associated users about the deletion
    await project2ownercandidate.delete(primary_key)
    return "No record remaining"


@router.delete("/all_projects_for_candidate")
async def delete_all_projects_for_candidate(user: User = Depends(current_user)):

    #TODO: Write e-mail to owner and associated users about the deletion
    await project2ownercandidate.delete_by_candidate(user.id)
    return "No records remaining"