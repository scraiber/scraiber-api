from typing import List
from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, HTTPException, Depends

from app.api.crud import project2user, project2external, projects, namespaces, namespace2projecttransfer
from app.api.kubernetes import namespace
from app.api.models.projects import (
    Project2UserDB,
    ProjectPrimaryKeyName,
    ProjectPrimaryKeyUserID,
    ProjectPrimaryKey,
    ProjectName,
    Project2ExternalDB,
    ProjectCompleteInfo)
from app.api.models.auth0 import Auth0User
from app.api.models.namespaces import NamespacePrimaryKey, NamespaceSchema, NamespacePrimaryKeyTransfer
from app.api.routes import user_management
from app.api.email.projects import *
from app.auth0 import current_user, check_email_verified

router = APIRouter()


@router.post("/", response_model=ProjectPrimaryKeyName, status_code=201)
async def create_project(payload: ProjectName, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)

    try: 
        project_id = await projects.post(ProjectPrimaryKeyName(name=payload.name))
    except UniqueViolationError:
        raise HTTPException(status_code=403, detail="Project already exists")

    try:
        await project2user.post(Project2UserDB(project_id=project_id, user_id=user.user_id, is_admin=True))
    except UniqueViolationError:
        raise HTTPException(status_code=403, detail="User is already added to project")

    await mail_project_post(ProjectPrimaryKeyNameEmail(project_id=project_id, name=payload.name, e_mail=user.email))
    
    return ProjectPrimaryKeyName(project_id=project_id, name=payload.name)


@router.get("/", response_model=ProjectCompleteInfo)
async def get_project(primary_key: ProjectPrimaryKey, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    await project2user.user_check(ProjectPrimaryKeyUserID(project_id=primary_key.project_id, user_id=user.user_id))

    project = await projects.get(primary_key.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_item = ProjectPrimaryKeyName(**project)

    namespaces_res = await namespaces.get_by_project(primary_key.project_id)
    if not namespaces_res:
        namespaces_list = []
    else:
        namespaces_list = [NamespaceSchema(**item) for item in namespaces_res]
    
    user_list = await user_management.get_users_by_project(primary_key, user)

    user_candidates_list = await user_management.get_invited_users_by_project(primary_key, user)

    external_list_res = await user_management.get_externals_by_project(primary_key, user)
    if not external_list_res:
        external_list = []
    else:
        external_list = [Project2ExternalDB(**item).e_mail for item in external_list_res]

    namespaces_transfer_source_res = await namespace2projecttransfer.get_by_old_project(primary_key.project_id)
    if not namespaces_transfer_source_res:
        namespaces_transfer_source_list = []
    else:
        namespaces_transfer_source_list = [NamespacePrimaryKeyTransfer(**item) for item in namespaces_transfer_source_res]

    namespaces_transfer_target_res = await namespace2projecttransfer.get_by_new_project(primary_key.project_id)
    if not namespaces_transfer_target_res:
        namespaces_transfer_target_list = []
    else:
        namespaces_transfer_target_list = [NamespacePrimaryKeyTransfer(**item) for item in namespaces_transfer_target_res]

    return ProjectCompleteInfo(project_id=primary_key.project_id, name=project_item.name,
                               namespaces=namespaces_list, users=user_list,
                               user_candidates=user_candidates_list, externals=external_list,
                               transfer_source_namespace=namespaces_transfer_source_list,
                               transfer_target_namespace=namespaces_transfer_target_list)


@router.get("/by_user", response_model=List[ProjectCompleteInfo])
async def get_project_by_user(admin_state: bool = False, user: Auth0User = Depends(current_user)) -> List[ProjectCompleteInfo]:
    await check_email_verified(user)
    associated_projects = await project2user.get_by_user(user.user_id)
    if not associated_projects:
        raise HTTPException(status_code=404, detail="User not associated to any project")
    output_list = []
    for item in associated_projects:
        project_item = Project2UserDB(**item)
        if admin_state and not project_item.is_admin:
            continue
        project_id_item = project_item.project_id
        complete_info_item_res = await get_project(ProjectPrimaryKey(project_id=project_id_item), user)
        if complete_info_item_res:
            output_list.append(complete_info_item_res)

    return output_list


@router.put("/name", response_model=ProjectPrimaryKeyName)
async def change_project_name(payload: ProjectPrimaryKeyName, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    await project2user.admin_check(ProjectPrimaryKeyUserID(project_id=payload.project_id, user_id=user.user_id))

    project = await projects.get(payload.project_id)
    project_old_name = ""
    if project:
        project_old_name = ProjectPrimaryKeyName(**project).name

    update_res = await projects.put_name(payload)
    if not update_res:
        raise HTTPException(status_code=404, detail="The name could not be changed")

    users_to_inform = await user_management.get_users_by_project(ProjectPrimaryKey(project_id=payload.project_id), user)
    for user_item in users_to_inform:
        await mail_project_name_put(ProjectPrimaryKeyNameEmail(project_id=payload.project_id, name=project_old_name, e_mail=user_item.email),
                                    new_name=payload.name)
    
    return payload


@router.delete("/", response_model=ProjectPrimaryKey, status_code=200)
async def delete_project(primary_key: ProjectPrimaryKey, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    await project2user.admin_check(ProjectPrimaryKeyUserID(project_id=primary_key.project_id, user_id=user.user_id))

    project = await projects.get(primary_key.project_id)
    project_name = ""
    if project:
        project_name = ProjectPrimaryKeyName(**project).name

    deletion_res = await projects.delete(primary_key.project_id)
    if not deletion_res:
        raise HTTPException(status_code=404, detail="Project could not be deleted")

    users_to_inform = await user_management.get_users_by_project(primary_key, user)
    for user_item in users_to_inform:
        await mail_project_delete(ProjectPrimaryKeyNameEmail(project_id=primary_key.project_id, name=project_name, e_mail=user_item.email))

    await project2external.delete_by_project(primary_key.project_id)
    await project2user.delete_by_project(primary_key.project_id)
    await namespace2projecttransfer.delete_by_old_project(primary_key.project_id)
    await namespace2projecttransfer.delete_by_new_project(primary_key.project_id)

    namespaces_res = await namespaces.get_by_project(primary_key.project_id)
    if namespaces_res:
        for item in namespaces_res:
            namespace_item = NamespaceSchema(**item)
            await namespace.delete_namespace(NamespacePrimaryKey(name=namespace_item.name, region=namespace_item.region))
    await namespaces.delete_by_project(primary_key.project_id)
    return primary_key
