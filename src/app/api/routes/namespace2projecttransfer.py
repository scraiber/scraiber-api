from typing import List
from fastapi import APIRouter, HTTPException, Depends

from app.api.crud import project2user, projects, namespaces, namespace2projecttransfer
from app.api.kubernetes import users
from app.api.models.projects import Project2UserDB, ProjectPrimaryKeyUserID, ProjectPrimaryKey
from app.api.models.namespaces import NamespacePrimaryKeyTransfer, NamespacePrimaryKey, NamespaceSchema, \
    NamespacePrimaryKeyEmail, NamespaceResourcesTransferInfo, NamespacePrimaryKeyProjectID
from app.api.models.auth0 import Auth0User
from app.api.auth0.users import get_user_list_by_id
from app.api.email.namespace2projecttransfer import *
from app.auth0 import current_user, check_email_verified

router = APIRouter()


@router.post("/", response_model=NamespacePrimaryKeyTransfer, status_code=201)
async def create_transfer_candidate(payload: NamespacePrimaryKeyTransfer, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    await project2user.admin_check(ProjectPrimaryKeyUserID(project_id=payload.old_project_id, user_id=user.user_id))

    project = await projects.get(payload.old_project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Source project not found")
    old_project = ProjectPrimaryKeyName(**project)

    project = await projects.get(payload.new_project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Target project not found")
    new_project = ProjectPrimaryKeyName(**project)

    namespace_item_res = await namespaces.get(payload)
    if not namespace_item_res:
        raise HTTPException(status_code=404, detail="Namespace not found")
    namespace_item = NamespaceSchema(**namespace_item_res)
    if namespace_item.project_id != payload.old_project_id:
        raise HTTPException(status_code=403, detail="Namespace not associated to source project")

    await namespace2projecttransfer.post(payload)

    users_old_project_res = await project2user.get_by_project(payload.old_project_id)
    user_old_project_ids = [Project2UserDB(**user_item).user_id for user_item in users_old_project_res]
    users_new_project_res = await project2user.get_by_project(payload.new_project_id)
    user_new_project_ids = [Project2UserDB(**user_item).user_id for user_item in users_new_project_res]
    user_ids = list(set(user_old_project_ids).union(set(user_new_project_ids)))

    auth0_users = await get_user_list_by_id(user_ids)
    for auth0_user in auth0_users:
        await mail_post_project_transfer(NamespacePrimaryKeyTransferEmailInfo(name=payload.name, region=payload.region,
                                                                              old_project_id=payload.old_project_id,
                                                                              new_project_id=payload.new_project_id,
                                                                              old_project_name=old_project.name,
                                                                              new_project_name=new_project.name,
                                                                              creator=user.nickname,
                                                                              e_mail=auth0_user.email))

    return payload


@router.post("/accept", response_model=NamespacePrimaryKeyTransfer, status_code=201)
async def accept_transfer(payload: NamespacePrimaryKey, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)

    namespace_res = await namespaces.get(payload)
    if not namespace_res:
        raise HTTPException(status_code=404, detail="Namespace not found")

    namespace2projecttransfer_res = await namespace2projecttransfer.get_by_namespace(payload)
    if not namespace2projecttransfer_res:
        raise HTTPException(status_code=404, detail="Namespace is not transfer candidate")
    namespace2projecttransfer_item = NamespacePrimaryKeyTransfer(**namespace2projecttransfer_res)

    project = await projects.get(namespace2projecttransfer_item.old_project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Source project not found")
    old_project = ProjectPrimaryKeyName(**project)

    project = await projects.get(namespace2projecttransfer_item.new_project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Target project not found")
    new_project = ProjectPrimaryKeyName(**project)

    await project2user.admin_check(
        ProjectPrimaryKeyUserID(project_id=namespace2projecttransfer_item.new_project_id, user_id=user.user_id))

    users_old_project_res = await project2user.get_by_project(namespace2projecttransfer_item.old_project_id)
    users_old_project_list = [Project2UserDB(**item).user_id for item in users_old_project_res]
    users_new_project_res = await project2user.get_by_project(namespace2projecttransfer_item.new_project_id)
    users_new_project_list = [Project2UserDB(**item).user_id for item in users_new_project_res]
    users_to_remove = list(set(users_old_project_list).difference(set(users_new_project_list)))
    users_to_add = list(set(users_new_project_list).difference(set(users_old_project_list)))
    users_to_remove_list = await get_user_list_by_id(users_to_remove, require_200_status_code=True)
    users_to_add_list = await get_user_list_by_id(users_to_add, require_200_status_code=True)

    for user in users_to_remove_list:
        await users.delete_kubernetes_user(
            NamespacePrimaryKeyEmail(name=payload.name, region=payload.region, e_mail=user.email))
    for user in users_to_add_list:
        await users.add_user_to_namespace(
            NamespacePrimaryKeyEmail(name=payload.name, region=payload.region, e_mail=user.email))

    await namespaces.put_project(NamespacePrimaryKeyProjectID(name=payload.name, region=payload.region,
                                                              project_id=namespace2projecttransfer_item.new_project_id))
    await namespace2projecttransfer.delete(payload)

    users_old_project_res = await project2user.get_by_project(namespace2projecttransfer_item.old_project_id)
    user_old_project_ids = [Project2UserDB(**user_item).user_id for user_item in users_old_project_res]
    users_new_project_res = await project2user.get_by_project(namespace2projecttransfer_item.new_project_id)
    user_new_project_ids = [Project2UserDB(**user_item).user_id for user_item in users_new_project_res]
    user_ids = list(set(user_old_project_ids).union(set(user_new_project_ids)))

    auth0_users = await get_user_list_by_id(user_ids)
    for auth0_user in auth0_users:
        await mail_accept_project_transfer(
            NamespacePrimaryKeyTransferEmailInfo(name=payload.name, region=payload.region,
                                                 old_project_id=old_project.project_id,
                                                 new_project_id=new_project.project_id,
                                                 old_project_name=old_project.name, new_project_name=new_project.name,
                                                 creator=user.nickname, e_mail=auth0_user.email))

    return namespace2projecttransfer_item


@router.get("/by_source_project", response_model=List[NamespaceResourcesTransferInfo])
async def get_namespace_transfer_by_source_project(primary_key: ProjectPrimaryKey, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    await project2user.user_check(ProjectPrimaryKeyUserID(project_id=primary_key.project_id, user_id=user.user_id))

    project = await projects.get(primary_key.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Source project not found")
    old_project = ProjectPrimaryKeyName(**project)

    transfer_list = await namespace2projecttransfer.get_by_old_project(primary_key.project_id)
    output_list = []

    for item_res in transfer_list:
        item = NamespacePrimaryKeyTransfer(**item_res)

        project = await projects.get(item.new_project_id)
        if not project:
            continue
        new_project = ProjectPrimaryKeyName(**project)

        namespace_res = await namespaces.get(item)
        if not namespace_res:
            continue
        namespace_item = NamespaceSchema(**namespace_res)

        item_to_add = NamespaceResourcesTransferInfo(name=namespace_item.name, region=namespace_item.region,
                                                     max_namespace_cpu=namespace_item.max_namespace_cpu,
                                                     max_namespace_mem=namespace_item.max_namespace_mem,
                                                     default_limit_pod_cpu=namespace_item.default_limit_pod_cpu,
                                                     default_limit_pod_mem=namespace_item.default_limit_pod_mem,
                                                     old_project_id=old_project.project_id,
                                                     new_project_id=new_project.project_id,
                                                     old_project_name=old_project.name,
                                                     new_project_name=new_project.name)
        output_list.append(item_to_add)

    return output_list


@router.get("/by_target_project", response_model=List[NamespaceResourcesTransferInfo])
async def get_namespace_transfer_by_target_project(primary_key: ProjectPrimaryKey, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    await project2user.user_check(ProjectPrimaryKeyUserID(project_id=primary_key.project_id, user_id=user.user_id))

    project = await projects.get(primary_key.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Source project not found")
    new_project = ProjectPrimaryKeyName(**project)

    transfer_list = await namespace2projecttransfer.get_by_new_project(primary_key.project_id)
    output_list = []

    for item_res in transfer_list:
        item = NamespacePrimaryKeyTransfer(**item_res)

        project = await projects.get(item.old_project_id)
        if not project:
            continue
        old_project = ProjectPrimaryKeyName(**project)

        namespace_res = await namespaces.get(item)
        if not namespace_res:
            continue
        namespace_item = NamespaceSchema(**namespace_res)

        item_to_add = NamespaceResourcesTransferInfo(name=namespace_item.name, region=namespace_item.region,
                                                     max_namespace_cpu=namespace_item.max_namespace_cpu,
                                                     max_namespace_mem=namespace_item.max_namespace_mem,
                                                     default_limit_pod_cpu=namespace_item.default_limit_pod_cpu,
                                                     default_limit_pod_mem=namespace_item.default_limit_pod_mem,
                                                     old_project_id=old_project.project_id,
                                                     new_project_id=new_project.project_id,
                                                     old_project_name=old_project.name,
                                                     new_project_name=new_project.name)
        output_list.append(item_to_add)

    return output_list


@router.get("/", response_model=NamespacePrimaryKeyTransfer, status_code=200)
async def accept_transfer(payload: NamespacePrimaryKey, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)

    namespace_res = await namespaces.get(payload)
    if not namespace_res:
        raise HTTPException(status_code=404, detail="Namespace not found")

    namespace_item = NamespaceSchema(**namespace_res)
    await project2user.user_check(ProjectPrimaryKeyUserID(project_id=namespace_item.project_id, user_id=user.user_id))

    namespace2projecttransfer_res = await namespace2projecttransfer.get_by_namespace(payload)
    if not namespace2projecttransfer_res:
        raise HTTPException(status_code=403, detail="Namespace is not transfer candidate")

    return namespace2projecttransfer_res


@router.delete("/", status_code=200)
async def delete_transfer_candidate(primary_key: NamespacePrimaryKey,
                                              user: Auth0User = Depends(current_user)):
    await check_email_verified(user)

    namespace_res = await namespaces.get(primary_key)
    if not namespace_res:
        raise HTTPException(status_code=404, detail="Namespace not found")

    namespace2projecttransfer_res = await namespace2projecttransfer.get_by_namespace(primary_key)
    if not namespace2projecttransfer_res:
        raise HTTPException(status_code=404, detail="Namespace is not transfer candidate")
    namespace2projecttransfer_item = NamespacePrimaryKeyTransfer(**namespace2projecttransfer_res)

    project = await projects.get(namespace2projecttransfer_item.old_project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Source project not found")
    old_project = ProjectPrimaryKeyName(**project)

    project = await projects.get(namespace2projecttransfer_item.new_project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Target project not found")
    new_project = ProjectPrimaryKeyName(**project)

    try:
        await project2user.admin_check(
            ProjectPrimaryKeyUserID(project_id=namespace2projecttransfer_item.old_project_id, user_id=user.user_id))
    except:
        await project2user.admin_check(
            ProjectPrimaryKeyUserID(project_id=namespace2projecttransfer_item.new_project_id, user_id=user.user_id))

    await namespace2projecttransfer.delete(primary_key)

    users_old_project_res = await project2user.get_by_project(namespace2projecttransfer_item.old_project_id)
    user_old_project_ids = [Project2UserDB(**user_item).user_id for user_item in users_old_project_res]
    users_new_project_res = await project2user.get_by_project(namespace2projecttransfer_item.new_project_id)
    user_new_project_ids = [Project2UserDB(**user_item).user_id for user_item in users_new_project_res]
    user_ids = list(set(user_old_project_ids).union(set(user_new_project_ids)))

    auth0_users = await get_user_list_by_id(user_ids)
    for auth0_user in auth0_users:
        await mail_delete_project_transfer(NamespacePrimaryKeyTransferEmailInfo(name=primary_key.name,
                                                                                region=primary_key.region,
                                                                                old_project_id=namespace2projecttransfer_item.old_project_id,
                                                                                new_project_id=namespace2projecttransfer_item.new_project_id,
                                                                                old_project_name=old_project.name,
                                                                                new_project_name=new_project.name,
                                                                                creator=user.nickname,
                                                                                e_mail=auth0_user.email))

    return "No records remaining"
