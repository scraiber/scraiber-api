import uuid
from typing import List
from fastapi import HTTPException

from app.api.models.projects import ProjectPrimaryKey, ProjectSchemaDB, Project2OwnerCandidateDB
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


async def owner_check(primary_key: Project2OwnerCandidateDB):
    query = projects.select().where(primary_key.name == projects.c.name).where(primary_key.region == projects.c.region)
    project = await database.fetch_one(query=query)
    if not project or ProjectSchemaDB(**project).owner_id != primary_key.id:
        raise HTTPException(status_code=404, detail="Project not found or user not owner")

'''
async def get_many(primary_keys: List[(ProjectPrimaryKey)]):
    print(primary_keys)
    primary_keys_query = [(item["name"], item["region"]) for item in primary_keys]
    query = projects.select().where(tuple_(projects.c.name, projects.c.region).in_(primary_keys_query))
    return await database.fetch_all(query=query)
'''

async def put_cpu_mem(payload: ProjectSchemaDB):
    query = (
        projects
        .update()
        .where(payload.name == projects.c.name).where(payload.region == projects.c.region)
        .values(limits_cpu=payload.limits_cpu, limits_mem=payload.limits_mem)
        .returning(projects.c.name, projects.c.region)
    )
    return await database.execute(query=query)

async def put_owner(payload: Project2OwnerCandidateDB):
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
