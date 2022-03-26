from typing import List
from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, HTTPException, Depends

from app.api.crud import project2user, projects, namespaces, namespace2projecttransfer
from app.api.kubernetes import namespace, users
from app.api.models.projects import Project2UserDB, ProjectPrimaryKeyUserID, ProjectPrimaryKey
from app.api.models.namespaces import NamespacePrimaryKey, NamespaceSchema, NamespacePrimaryKeyEmail, NamespacePrimaryKeyProjectID
from app.api.models.auth0 import Auth0User
from app.api.auth0.users import get_user_by_id, get_user_list_by_id
from app.api.email.namespaces import *
from app.auth0 import current_user, check_email_verified
from app.kubernetes_setup import clusters

router = APIRouter()


@router.post("/", response_model=NamespaceSchema, status_code=201)
async def create_namespace(payload: NamespaceSchema, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    await project2user.admin_check(ProjectPrimaryKeyUserID(project_id=payload.project_id, user_id=user.user_id))

    if payload.name in clusters[payload.region]["blacklist"]:
        raise HTTPException(status_code=403, detail="Namespace already exists")

    project = await projects.get(payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_deserialized = ProjectPrimaryKeyName(**project)

    try: 
        await namespaces.post(payload)
    except UniqueViolationError:
        raise HTTPException(status_code=403, detail="Namespace already exists")
    await namespace.create_namespace(payload)

    creator = await get_user_by_id(user.user_id)
    users_res = await project2user.get_by_project(payload.project_id)
    user_ids = [Project2UserDB(**user_item).user_id for user_item in users_res]
    auth0_users = await get_user_list_by_id(user_ids)

    for auth0_user in auth0_users:
        await users.add_user_to_namespace(NamespacePrimaryKeyEmail(name=payload.name, region=payload.region, e_mail=auth0_user.email))
        await mail_namespace_post(NamespacePrimaryKeyEmailInfo(name=payload.name, region=payload.region, e_mail=auth0_user.email,
                                                               project_id=payload.project_id, project_name=project_deserialized.name, creator=creator.nickname))
    
    return payload


@router.get("/", response_model=NamespaceSchema)
async def get_namespace(primary_key: NamespacePrimaryKey, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    namespace_res = await namespaces.get(primary_key)
    if not namespace_res:
        raise HTTPException(status_code=404, detail="Namespace not found")
    namespace_item = NamespaceSchema(**namespace_res)

    user_namespace_check = await project2user.get(ProjectPrimaryKeyUserID(project_id=namespace_item.project_id, user_id=user.user_id))
    if not user_namespace_check:
        raise HTTPException(status_code=404, detail="Project/Namespace for user not found")

    return namespace_res


@router.get("/by_project", response_model=List[NamespaceSchema])
async def get_namespaces_by_project(primary_key: ProjectPrimaryKey, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    project2user_res = await project2user.get(ProjectPrimaryKeyUserID(project_id=primary_key.project_id, user_id=user.user_id))
    if not project2user_res:
        raise HTTPException(status_code=404, detail="Project for user not found")

    return await namespaces.get_by_project(primary_key.project_id)


@router.get("/by_user", response_model=List[NamespaceSchema])
async def get_namespaces_by_user(user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    project2user_res = await project2user.get_by_user(user.user_id)
    if not project2user_res:
        raise HTTPException(status_code=404, detail="No Project found for user")

    output_list = []
    for item in project2user_res:
        item_deserialized = Project2UserDB(**item)
        namespace_list_res = await namespaces.get_by_project(item_deserialized.project_id)
        namespace_list = [NamespaceSchema(**ns_item) for ns_item in namespace_list_res]
        output_list.extend(namespace_list)
    return output_list


@router.put("/update_cpu_memory", response_model=NamespaceSchema, status_code=200)
async def update_cpu_memory(update: NamespaceSchema, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    await project2user.admin_check(ProjectPrimaryKeyUserID(project_id=update.project_id, user_id=user.user_id))

    namespace_res = await namespaces.get(update)
    if not namespace_res:
        raise HTTPException(status_code=404, detail="Namespace not found")
    namespace_item = NamespaceSchema(**namespace_res)
    if namespace_item.project_id != update.project_id:
        raise HTTPException(status_code=404, detail="Namespace does not belong to the project outlined")

    await namespaces.put_cpu_mem(update)
    await namespace.update_namespace(update)

    project_res = await projects.get(update.project_id)
    project_info = ProjectPrimaryKeyName(**project_res)

    admins = await project2user.get_admins_by_project(update.project_id)
    admin_ids = [Project2UserDB(**admin).user_id for admin in admins]
    auth0_admins = await get_user_list_by_id(admin_ids)
    for auth0_admin in auth0_admins:
        mail_payload = NamespaceSchemaProjectNameEmailInfo(
            name=update.name, region=update.region,
            max_namespace_cpu=update.max_namespace_cpu, max_namespace_mem=update.max_namespace_mem,
            default_limit_pod_cpu=update.default_limit_pod_cpu, default_limit_pod_mem=update.default_limit_pod_mem,
            project_id=update.project_id, project_name=project_info.name,
            e_mail=auth0_admin.email, creator=user.nickname
        )
        await mail_namespace_put_resources(mail_payload)

    return update


@router.delete("/", status_code=200)
async def delete_namespace(primary_key: NamespacePrimaryKey, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)

    namespace_res = await namespaces.get(primary_key)
    if not namespace_res:
        raise HTTPException(status_code=404, detail="Namespace not found")
    namespace_item = NamespaceSchema(**namespace_res)

    user_namespace_check = await project2user.get(ProjectPrimaryKeyUserID(project_id=namespace_item.project_id, user_id=user.user_id))
    if not user_namespace_check:
        raise HTTPException(status_code=404, detail="Project/Namespace for user not found")

    await project2user.admin_check(ProjectPrimaryKeyUserID(project_id=namespace_item.project_id, user_id=user.user_id))

    namespace_info_res = await namespaces.get(primary_key)
    namespace_info = NamespaceSchema(**namespace_info_res)

    project_res = await projects.get(namespace_item.project_id)
    project_info = ProjectPrimaryKeyName(**project_res)

    await namespace.delete_namespace(primary_key)
    await namespaces.delete(primary_key)
    await namespace2projecttransfer.delete(primary_key)

    admins = await project2user.get_admins_by_project(namespace_info.project_id)
    admin_ids = [Project2UserDB(**admin).user_id for admin in admins]
    auth0_admins = await get_user_list_by_id(admin_ids)
    for auth0_admin in auth0_admins:
        await mail_namespace_delete(NamespacePrimaryKeyEmailInfo(name=primary_key.name, region=primary_key.region, e_mail=auth0_admin.email,
                                                                 project_id=project_info.project_id, project_name=project_info.name, creator=user.nickname))

    return primary_key
