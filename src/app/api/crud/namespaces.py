import uuid

from app.api.models.namespaces import NamespacePrimaryKey, NamespaceSchema, NamespaceResources, NamespacePrimaryKeyProjectID
from app.db import namespaces, database


async def post(payload: NamespaceSchema):
    query = namespaces.insert().values(payload.dict())
    return await database.execute(query=query)


async def get(primary_key: NamespacePrimaryKey):
    query = namespaces.select().where(primary_key.name == namespaces.c.name).where(primary_key.region == namespaces.c.region)
    return await database.fetch_one(query=query)


async def get_by_project(project_id: uuid):
    query = namespaces.select().where(project_id == namespaces.c.project_id)
    return await database.fetch_all(query=query)


async def put_cpu_mem(payload: NamespaceResources):
    query = (
        namespaces
        .update()
        .where(payload.name == namespaces.c.name).where(payload.region == namespaces.c.region)
        .values(max_namespace_cpu=payload.max_namespace_cpu,
                max_namespace_mem=payload.max_namespace_mem,
                default_limit_pod_cpu=payload.default_limit_pod_cpu,
                default_limit_pod_mem=payload.default_limit_pod_mem)
        .returning(namespaces.c.name, namespaces.c.region)
    )
    return await database.execute(query=query)


async def put_project(payload: NamespacePrimaryKeyProjectID):
    query = (
        namespaces
        .update()
        .where(payload.name == namespaces.c.name).where(payload.region == namespaces.c.region)
        .values(project_id=payload.project_id)
        .returning(namespaces.c.name, namespaces.c.region)
    )
    return await database.execute(query=query)


async def delete(payload: NamespacePrimaryKey):
    query = namespaces.delete().where(payload.name == namespaces.c.name).where(payload.region == namespaces.c.region)
    return await database.execute(query=query)


async def delete_by_project(project_id: uuid):
    query = namespaces.delete().where(project_id == namespaces.c.project_id)
    return await database.execute(query=query)
