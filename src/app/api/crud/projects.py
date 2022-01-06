import uuid
from typing import List
from fastapi import HTTPException

from app.api.models.projects import ProjectPrimaryKey, ProjectSchema, ProjectSchemaDB, PrimaryKeyWithUserID
from app.db import projects, database

#from sqlalchemy import tuple_


async def post(payload: ProjectSchemaDB):
    query = projects.insert().values(payload)
    return await database.execute(query=query)


async def get(primary_key: ProjectPrimaryKey):
    query = projects.select().where(primary_key.name == projects.c.name).where(primary_key.region == projects.c.region)
    return await database.fetch_one(query=query)


async def get_by_owner(owner_id: uuid):
    query = projects.select().where(owner_id == projects.c.owner_id)
    return await database.fetch_all(query=query)


async def owner_check(primary_key: PrimaryKeyWithUserID):
    query = projects.select().where(primary_key.name == projects.c.name).where(primary_key.region == projects.c.region)
    project = await database.fetch_one(query=query)
    if not project or ProjectSchemaDB(**project).owner_id != primary_key.candidate_id:
        raise HTTPException(status_code=404, detail="Project not found or user not owner")

'''
async def get_many(primary_keys: List[(ProjectPrimaryKey)]):
    print(primary_keys)
    primary_keys_query = [(item["name"], item["region"]) for item in primary_keys]
    query = projects.select().where(tuple_(projects.c.name, projects.c.region).in_(primary_keys_query))
    return await database.fetch_all(query=query)
'''

async def put_cpu_mem(payload: ProjectSchema):
    query = (
        projects
        .update()
        .where(payload.name == projects.c.name).where(payload.region == projects.c.region)
        .values(max_project_cpu=payload.max_project_cpu, max_project_mem=payload.max_project_mem,
            default_limit_pod_cpu=payload.default_limit_pod_cpu, default_limit_pod_mem=payload.default_limit_pod_mem)
        .returning(projects.c.name, projects.c.region)
    )
    return await database.execute(query=query)

async def put_owner(payload: PrimaryKeyWithUserID):
    query = (
        projects
        .update()
        .where(payload.name == projects.c.name).where(payload.region == projects.c.region)
        .values(owner_id=payload.candidate_id)
        .returning(projects.c.name, projects.c.region)
    )
    return await database.execute(query=query)

async def delete(payload: ProjectPrimaryKey):
    query = projects.delete().where(payload.name == projects.c.name).where(payload.region == projects.c.region)
    return await database.execute(query=query)
