import datetime

from pydantic import EmailStr
from app.api.models.projects import Project2ExternalDB, ProjectPrimaryKey
from app.db import project2external, database



async def post(payload: Project2ExternalDB):
    query = project2external.insert().values(payload)
    return await database.execute(query=query)

"""
async def get(primary_key: Project2ExternalDB):
    query = project2external.select().where(primary_key.name == project2external.c.name).where(primary_key.region == project2external.c.region).where(primary_key.e_mail == project2external.c.e_mail)
    return await database.fetch_one(query=query)
"""

async def get_by_project(primary_key: ProjectPrimaryKey):
    query = project2external.select().where(primary_key.name == project2external.c.name).where(primary_key.region == project2external.c.region)
    return await database.fetch_all(query=query)



"""
async def delete(primary_key: ProjectPrimaryKey):
    query = project2external.delete().where(primary_key.name == project2external.c.name).where(primary_key.region == project2external.c.region).where(primary_key.e_mail == project2external.c.e_mail)
    return await database.execute(query=query)
"""

async def delete_by_project(primary_key: ProjectPrimaryKey):
    query = project2external.delete().where(primary_key.name == project2external.c.name).where(primary_key.region == project2external.c.region)
    return await database.execute(query=query)


async def delete(primary_key: Project2ExternalDB):
    query = project2external.delete().where(primary_key.name == project2external.c.name).where(primary_key.region == project2external.c.region).where(primary_key.e_mail == project2external.c.e_mail)
    return await database.execute(query=query)


async def delete_by_time(days: int=2):
    too_old = datetime.datetime.today() - datetime.timedelta(days=days)
    query = project2external.delete().where(project2external.c.created_date <= too_old)
    return await database.execute(query=query)