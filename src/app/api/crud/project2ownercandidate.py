import uuid
import datetime
from app.api.models.projects import Project2OwnerCandidateDB, ProjectPrimaryKey
from app.db import project2ownercandidate, database


async def post(payload: Project2OwnerCandidateDB):
    query = project2ownercandidate.insert().values(payload)
    return await database.execute(query=query)


async def get(primary_key: ProjectPrimaryKey):
    query = project2ownercandidate.select().where(primary_key.name == project2ownercandidate.c.name).where(primary_key.region == project2ownercandidate.c.region)
    return await database.fetch_one(query=query)


async def get_by_candidate(candidate_id: uuid):
    query = project2ownercandidate.select().where(candidate_id == project2ownercandidate.c.candidate_id)
    return await database.fetch_all(query=query)


async def delete(primary_key: ProjectPrimaryKey):
    query = project2ownercandidate.delete().where(primary_key.name == project2ownercandidate.c.name).where(primary_key.region == project2ownercandidate.c.region)
    return await database.execute(query=query)


async def delete_by_candidate(candidate_id: uuid):
    query = project2ownercandidate.delete().where(candidate_id == project2ownercandidate.c.candidate_id)
    return await database.execute(query=query)