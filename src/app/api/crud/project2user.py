import uuid
from fastapi import HTTPException

from app.api.models.projects import ProjectPrimaryKey, Project2UserDB
from app.api.models.certificates import Certificate2User
from app.db import project2user, database


async def post(payload: Project2UserDB):
    query = project2user.insert().values(payload)
    return await database.execute(query=query)


async def get(primary_key: Project2UserDB):
    query = project2user.select().where(primary_key.name == project2user.c.name).where(primary_key.region == project2user.c.region).where(primary_key.user_id == project2user.c.user_id)
    return await database.fetch_one(query=query)


async def get_by_project(primary_key: ProjectPrimaryKey):
    query = project2user.select().where(primary_key.name == project2user.c.name).where(primary_key.region == project2user.c.region)
    return await database.fetch_all(query=query)


async def admin_check(primary_key: Project2UserDB):
    query = project2user.select().where(primary_key.name == project2user.c.name).where(primary_key.region == project2user.c.region).where(primary_key.user_id == project2user.c.user_id).where(True == project2user.c.is_admin)
    project2user_admin_res = await database.fetch_one(query=query)
    if not project2user_admin_res:
        raise HTTPException(status_code=401, detail="Project for user not found or user not admin")


async def get_by_user(user_id: uuid):
    query = project2user.select().where(user_id == project2user.c.user_id)
    return await database.fetch_all(query=query)


async def get_by_user_and_region(payload: Certificate2User):
    query = project2user.select().where(payload.user_id == project2user.c.user_id).where(payload.region == project2user.c.region)
    return await database.fetch_all(query=query)


async def put_admin_state(payload: Project2UserDB):
    query = (
        project2user
        .update()
        .where(payload.name == project2user.c.name).where(payload.region == project2user.c.region).where(payload.user_id == project2user.c.user_id)
        .values(is_admin=payload.is_admin)
        .returning(project2user.c.name, project2user.c.region)
    )
    return await database.execute(query=query)


async def delete(payload: Project2UserDB):
    query = project2user.delete().where(payload.name == project2user.c.name).where(payload.region == project2user.c.region).where(payload.user_id == project2user.c.user_id)
    return await database.execute(query=query)


async def delete_by_project(primary_key: ProjectPrimaryKey):
    query = project2user.delete().where(primary_key.name == project2user.c.name).where(primary_key.region == project2user.c.region)
    return await database.execute(query=query)


async def delete_by_user(user_id: uuid):
    query = project2user.delete().where(user_id == project2user.c.user_id)
    return await database.execute(query=query)