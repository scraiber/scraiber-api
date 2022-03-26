import uuid

from fastapi import HTTPException

from app.api.models.projects import Project2UserDB, ProjectPrimaryKeyUserID
from app.db import project2user, database


async def post(payload: Project2UserDB):
    query = project2user.insert().values(payload.dict())
    return await database.execute(query=query)


async def get(primary_key: ProjectPrimaryKeyUserID):
    query = project2user.select().where(primary_key.project_id == project2user.c.project_id).where(primary_key.user_id == project2user.c.user_id)
    return await database.fetch_one(query=query)


async def user_check(primary_key: ProjectPrimaryKeyUserID):
    associated_projects = await get(primary_key)
    if not associated_projects:
        raise HTTPException(status_code=404, detail="Project for user not found")


async def get_by_project(project_id: uuid):
    query = project2user.select().where(project_id == project2user.c.project_id)
    return await database.fetch_all(query=query)


async def get_admins_by_project(project_id: uuid):
    query = project2user.select().where(project_id == project2user.c.project_id).where(project2user.c.is_admin == True)
    return await database.fetch_all(query=query)


async def admin_check(primary_key: ProjectPrimaryKeyUserID):
    query = project2user.select().where(primary_key.project_id == project2user.c.project_id).where(primary_key.user_id == project2user.c.user_id).where(project2user.c.is_admin == True)
    project2user_admin_res = await database.fetch_one(query=query)
    if not project2user_admin_res:
        raise HTTPException(status_code=401, detail="Project for user not found or user not admin")


async def get_by_user(user_id: str):
    query = project2user.select().where(user_id == project2user.c.user_id)
    return await database.fetch_all(query=query)


async def put_admin_state(payload: Project2UserDB):
    proj2user_response = await get(payload)
    if not proj2user_response:
        raise HTTPException(status_code=404, detail="Update item not found")
    if Project2UserDB(**proj2user_response).is_admin == payload.is_admin:
        raise HTTPException(status_code=403, detail="Admin state would not change") 
    query = (
        project2user
        .update()
        .where(payload.project_id == project2user.c.project_id).where(payload.user_id == project2user.c.user_id)
        .values(is_admin=payload.is_admin)
        .returning(project2user.c.project_id)
    )
    return await database.execute(query=query)


async def delete(payload: Project2UserDB):
    query = project2user.delete().where(payload.project_id == project2user.c.project_id).where(payload.user_id == project2user.c.user_id)
    return await database.execute(query=query)


async def delete_by_project(project_id: uuid):
    query = project2user.delete().where(project_id == project2user.c.project_id)
    return await database.execute(query=query)


async def delete_by_user(user_id: str):
    query = project2user.delete().where(user_id == project2user.c.user_id)
    return await database.execute(query=query)