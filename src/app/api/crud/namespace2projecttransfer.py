import uuid

from app.api.models.namespaces import NamespacePrimaryKeyTransfer, NamespacePrimaryKey
from app.db import namespace2projecttransfer, database


async def post(payload: NamespacePrimaryKeyTransfer):
    query = namespace2projecttransfer.insert().values(payload.dict())
    return await database.execute(query=query)


async def get_by_namespace(primary_key: NamespacePrimaryKey):
    query = namespace2projecttransfer.select().where(primary_key.name == namespace2projecttransfer.c.name).where(primary_key.region == namespace2projecttransfer.c.region)
    return await database.fetch_one(query=query)


async def get_by_old_project(old_project_id: uuid):
    query = namespace2projecttransfer.select().where(old_project_id == namespace2projecttransfer.c.old_project_id)
    return await database.fetch_all(query=query)


async def get_by_new_project(new_project_id: uuid):
    query = namespace2projecttransfer.select().where(new_project_id == namespace2projecttransfer.c.new_project_id)
    return await database.fetch_all(query=query)


async def delete(payload: NamespacePrimaryKey):
    query = namespace2projecttransfer.delete().where(payload.name == namespace2projecttransfer.c.name).where(payload.region == namespace2projecttransfer.c.region)
    return await database.execute(query=query)


async def delete_by_old_project(old_project_id: uuid):
    query = namespace2projecttransfer.delete().where(old_project_id == namespace2projecttransfer.c.old_project_id)
    return await database.execute(query=query)


async def delete_by_new_project(new_project_id: uuid):
    query = namespace2projecttransfer.delete().where(new_project_id == namespace2projecttransfer.c.new_project_id)
    return await database.execute(query=query)
