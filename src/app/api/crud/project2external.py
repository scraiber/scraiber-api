import datetime
import uuid

from pydantic import EmailStr
from app.api.models.projects import Project2ExternalDB
from app.db import project2external, database



async def post(payload: Project2ExternalDB):
    query = project2external.insert().values(payload.dict())
    return await database.execute(query=query)


async def get_by_project(project_id: uuid):
    query = project2external.select().where(project_id == project2external.c.project_id)
    return await database.fetch_all(query=query)

async def get_by_email(e_mail: EmailStr):
    query = project2external.select().where(e_mail == project2external.c.e_mail)
    return await database.fetch_all(query=query)


async def delete_by_project(project_id: uuid):
    query = project2external.delete().where(project_id == project2external.c.project_id)
    return await database.execute(query=query)

async def delete_by_email(e_mail: EmailStr):
    query = project2external.delete().where(e_mail == project2external.c.e_mail)
    return await database.execute(query=query)

async def delete(primary_key: Project2ExternalDB):
    query = project2external.delete().where(primary_key.project_id == project2external.c.project_id).where(primary_key.e_mail == project2external.c.e_mail)
    return await database.execute(query=query)

async def delete_by_time(days: int=2):
    too_old = datetime.datetime.today() - datetime.timedelta(days=days)
    query = project2external.delete().where(project2external.c.created_date <= too_old)
    return await database.execute(query=query)