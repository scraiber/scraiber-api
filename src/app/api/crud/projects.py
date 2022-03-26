import uuid

from app.api.models.projects import ProjectPrimaryKeyName
from app.db import projects, database


async def post(payload: ProjectPrimaryKeyName):
    query = projects.insert().values(payload.dict()).returning(projects.c.project_id)
    return await database.execute(query=query)


async def get(project_id: uuid):
    query = projects.select().where(project_id == projects.c.project_id)
    return await database.fetch_one(query=query)


async def put_name(payload: ProjectPrimaryKeyName):
    query = (
        projects
        .update()
        .where(payload.project_id == projects.c.project_id)
        .values(name=payload.name)
        .returning(projects.c.name)
    )
    return await database.execute(query=query)


async def delete(project_id: uuid):
    query = projects.delete().where(project_id == projects.c.project_id).returning(projects.c.project_id)
    return await database.execute(query=query)
