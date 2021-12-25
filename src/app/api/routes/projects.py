from typing import List
from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, HTTPException, Depends

from app.api.crud import project2user, project2external, project2ownercandidate, projects
from app.api.models.projects import ProjectPrimaryKey, ProjectSchema, ProjectSchemaDB, Project2UserDB, Project2OwnerCandidateDB
from app.api.models.users import User
from app.fastapiusers import current_user, current_active_user

router = APIRouter()


@router.post("/", response_model=ProjectSchemaDB, status_code=201)
async def create_project(payload: ProjectSchema, user: User = Depends(current_active_user)):
    post_project = {
        "name": payload.name,
        "region": payload.region,
        "limits_cpu": payload.limits_cpu,
        "limits_mem": payload.limits_mem,
        "owner_id": user.id
    }
    try: 
        await projects.post(post_project)
    except UniqueViolationError:
        raise HTTPException(status_code=403, detail="Project already exists")

    try: 
        await project2user.post(Project2UserDB(name=payload.name, region=payload.region, user_id=user.id, is_admin=True))
    except UniqueViolationError:
        raise HTTPException(status_code=403, detail="User is already added to project")
    #TODO: Write e-mail to owner
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
    print(project2user_res)
    if not project2user_res:
        raise HTTPException(status_code=404, detail="No projects for user found")
    project2user_res_deserialized = [Project2UserDB(**item).dict() for item in project2user_res]
    payload_list = [{"name": item["name"], "region": item["region"]} for item in project2user_res_deserialized]
    return await projects.get_many(payload_list)
'''

@router.put("/update_cpu_memory", response_model=ProjectSchemaDB, status_code=200)
async def update_cpu_memory(update: ProjectSchema, user: User = Depends(current_user)):
    await project2user.admin_check(Project2UserDB(name=update.name, region=update.region, user_id=user.id))
    project = await projects.get(ProjectPrimaryKey(name=update.name, region=update.region))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_schema = ProjectSchemaDB(**project)
    update_payload = ProjectSchemaDB(name=update.name, region=update.region, limits_cpu=update.limits_cpu, limits_mem=update.limits_mem, owner_id=project_schema.owner_id)
    await projects.put_cpu_mem(update_payload)
    #TODO: Write e-mail to owner resp. users about the update
    return update_payload


@router.delete("/", status_code=200)
async def delete_by_project(primary_key: ProjectPrimaryKey, user: User = Depends(current_user)):
    await projects.owner_check(Project2OwnerCandidateDB(name=primary_key.name, region=primary_key.region, candidate_id=user.id))

    #TODO: Write e-mail to owner and associated users about the deletion
    await projects.delete(primary_key)
    await project2external.delete_by_project(primary_key)
    await project2ownercandidate.delete(primary_key)
    await project2user.delete_by_project(primary_key)
    return "No record remaining"
