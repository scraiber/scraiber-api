import uuid

from fastapi import HTTPException

from app.api.models.projects import Project2UserDB, ProjectPrimaryKeyUserID
from app.db import project2usercandidate, database


async def post(payload: Project2UserDB):
    query = project2usercandidate.insert().values(payload.dict())
    return await database.execute(query=query)


async def get(primary_key: ProjectPrimaryKeyUserID):
    query = project2usercandidate.select().where(primary_key.project_id == project2usercandidate.c.project_id).where(primary_key.user_id == project2usercandidate.c.user_id)
    return await database.fetch_one(query=query)


async def get_by_project(project_id: uuid):
    query = project2usercandidate.select().where(project_id == project2usercandidate.c.project_id)
    return await database.fetch_all(query=query)


async def get_by_user(user_id: str):
    query = project2usercandidate.select().where(user_id == project2usercandidate.c.user_id)
    return await database.fetch_all(query=query)


async def put_admin_state(payload: Project2UserDB):
    proj2user_respponse = await get(payload)
    if not proj2user_respponse:
        raise HTTPException(status_code=404, detail="Update item not found")
    if Project2UserDB(**proj2user_respponse).is_admin == payload.is_admin:
        raise HTTPException(status_code=403, detail="Admin state would not change") 
    query = (
        project2usercandidate
        .update()
        .where(payload.project_id == project2usercandidate.c.project_id).where(payload.user_id == project2usercandidate.c.user_id)
        .values(is_admin=payload.is_admin)
        .returning(project2usercandidate.c.project_id)
    )
    return await database.execute(query=query)


async def delete(payload: ProjectPrimaryKeyUserID):
    query = project2usercandidate.delete().where(payload.project_id == project2usercandidate.c.project_id).where(payload.user_id == project2usercandidate.c.user_id)
    return await database.execute(query=query)


async def delete_by_project(project_id: uuid):
    query = project2usercandidate.delete().where(project_id == project2usercandidate.c.project_id)
    return await database.execute(query=query)


async def delete_by_user(user_id: str):
    query = project2usercandidate.delete().where(user_id == project2usercandidate.c.user_id)
    return await database.execute(query=query)