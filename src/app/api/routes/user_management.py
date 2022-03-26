from fastapi import APIRouter, HTTPException, Depends
from asyncpg.exceptions import UniqueViolationError
from typing import List
import uuid

from app.api.kubernetes import users
from app.api.crud import project2external, project2user, project2usercandidate, projects, namespaces
from app.api.models.projects import ProjectPrimaryKeyName, ProjectPrimaryKeyUserID, Project2UserDB, ProjectPrimaryKey
from app.api.models.namespaces import NamespacePrimaryKeyEmail, NamespaceSchema
from app.api.models.auth0 import Auth0User, Auth0UserWithAdmin
from app.auth0 import current_user, check_email_verified
from app.api.auth0.users import get_user_by_email, get_user_by_id, get_user_list_by_id
from app.api.email.user_management import *


router = APIRouter()


@router.post("/", response_model=Project2ExternalDB, status_code=201)
async def invite_user_or_external(primary_key: Project2ExternalDB, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    await project2user.admin_check(ProjectPrimaryKeyUserID(project_id=primary_key.project_id, user_id=user.user_id))

    try:
        user_by_email = await get_user_by_email(primary_key.e_mail)
        user_exists = True
    except HTTPException:
        user_exists = False

    if user_exists:
        try:
            await project2usercandidate.post(Project2UserDB(project_id=primary_key.project_id, user_id=user_by_email.user_id, is_admin=primary_key.is_admin))

            project = await projects.get(primary_key.project_id)
            project_deserialized = ProjectPrimaryKeyName(**project)
            payload = ProjectPrimaryKeyNameEmailAdmin(project_id=primary_key.project_id, name=project_deserialized.name, e_mail=primary_key.e_mail, is_admin=primary_key.is_admin)
            await mail_um_post_internal(payload)

            admins = await project2user.get_admins_by_project(project_deserialized.project_id)
            admin_ids = [Project2UserDB(**admin).user_id for admin in admins]
            auth0_admins = await get_user_list_by_id(admin_ids)
            for auth0_admin in auth0_admins:
                await mail_um_post_internal_admin(payload, EmailStr(auth0_admin.email))
        except:
            raise HTTPException(status_code=403, detail="Item already exists")   
    else:
        try:
            await project2external.post(Project2ExternalDB(project_id=primary_key.project_id, e_mail=primary_key.e_mail, is_admin=primary_key.is_admin))
            project = await projects.get(primary_key.project_id)
            project_deserialized = ProjectPrimaryKeyName(**project)
            payload = ProjectPrimaryKeyNameEmailAdmin(project_id=primary_key.project_id, name=project_deserialized.name, e_mail=primary_key.e_mail, is_admin=primary_key.is_admin)
            await mail_um_post_external(payload)
        except:
            raise HTTPException(status_code=403, detail="Item already exists")            
    return primary_key


@router.post("/accept_user_invitation", status_code=201)
async def accept_invitation(primary_key: ProjectPrimaryKey, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    payload = ProjectPrimaryKeyUserID(project_id=primary_key.project_id, user_id=user.user_id)
    candidate_res = await project2usercandidate.get(payload)
    if not candidate_res:
        raise HTTPException(status_code=404, detail="No invitation found for user and project")

    item = Project2UserDB(**candidate_res)
    await project2user.post(item)
    await project2usercandidate.delete(payload)

    associated_ns_res = await namespaces.get_by_project(primary_key.project_id)
    if associated_ns_res:
        for namespace_item in associated_ns_res:
            namespace_des = NamespaceSchema(**namespace_item)
            try:
                await users.add_user_to_namespace(NamespacePrimaryKeyEmail(name=namespace_des.name, region=namespace_des.region, e_mail=user.email))
            except:
                pass

    project = await projects.get(primary_key.project_id)
    project_deserialized = ProjectPrimaryKeyName(**project)
    payload = ProjectPrimaryKeyNameEmailAdmin(project_id=primary_key.project_id, name=project_deserialized.name, e_mail=user.email, is_admin=item.is_admin)
    await mail_um_post_accept_internal(payload)

    admins = await project2user.get_admins_by_project(project_deserialized.project_id)
    admin_ids = [Project2UserDB(**admin).user_id for admin in admins]
    auth0_admins = await get_user_list_by_id(admin_ids)
    for auth0_admin in auth0_admins:
        await mail_um_post_accept_internal_admin(payload, EmailStr(auth0_admin.email))
    return "Accepted"


@router.get("/externals_by_project", response_model=List[Project2ExternalDB])
async def get_externals_by_project(primary_key: ProjectPrimaryKey, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    await project2user.user_check(ProjectPrimaryKeyUserID(project_id=primary_key.project_id, user_id=user.user_id))
    project2user_res = await project2external.get_by_project(primary_key.project_id)
    if not project2user_res:
        return []
    return project2user_res


@router.get("/invited_users_by_project", response_model=List[Auth0UserWithAdmin])
async def get_invited_users_by_project(primary_key: ProjectPrimaryKey, user: Auth0User = Depends(current_user)) -> List[Auth0UserWithAdmin]:
    await check_email_verified(user)
    await project2user.user_check(ProjectPrimaryKeyUserID(project_id=primary_key.project_id, user_id=user.user_id))
    project2usercandidate_res = await project2usercandidate.get_by_project(primary_key.project_id)
    if not project2usercandidate_res:
        return []

    project2user_res_id = [Project2UserDB(**item).user_id for item in project2usercandidate_res]
    auth0_user_list = await get_user_list_by_id(project2user_res_id)
    if not auth0_user_list:
        return []
    else:
        output_list = []
        project2user_index = 0
        for index in range(len(auth0_user_list)):
            auth0_user = auth0_user_list[index]
            for index2 in range(project2user_index, len(project2usercandidate_res)):
                project2user_item = Project2UserDB(**project2usercandidate_res[index2])
                if auth0_user.user_id == project2user_item.user_id:
                    output_item = Auth0UserWithAdmin(name=auth0_user.username, email=auth0_user.email, user_id=auth0_user.user_id,
                                                     nickname=auth0_user.nickname, is_verified=auth0_user.is_verified, is_admin=project2user_item.is_admin)
                    output_list.append(output_item)
                    project2user_index = index2+1
                    break
        return output_list


@router.get("/users_by_project", response_model=List[Auth0UserWithAdmin])
async def get_users_by_project(primary_key: ProjectPrimaryKey, user: Auth0User = Depends(current_user)) -> List[Auth0UserWithAdmin]:
    await check_email_verified(user)
    await project2user.user_check(ProjectPrimaryKeyUserID(project_id=primary_key.project_id, user_id=user.user_id))

    project2user_res = await project2user.get_by_project(primary_key.project_id)
    if not project2user_res:
        raise HTTPException(status_code=404, detail="No users for project found")
    
    project2user_res_id = [Project2UserDB(**item).user_id for item in project2user_res]
    auth0_user_list = await get_user_list_by_id(project2user_res_id)

    if not auth0_user_list:
        return []
    else:
        output_list = []
        project2user_index = 0
        for index in range(len(auth0_user_list)):
            auth0_user = auth0_user_list[index]
            for index2 in range(project2user_index, len(project2user_res)):
                project2user_item = Project2UserDB(**project2user_res[index2])
                if auth0_user.user_id == project2user_item.user_id:
                    output_item = Auth0UserWithAdmin(name=auth0_user.username, email=auth0_user.email, user_id=auth0_user.user_id, 
                        nickname=auth0_user.nickname, is_verified=auth0_user.is_verified, is_admin=project2user_item.is_admin)
                    output_list.append(output_item)
                    project2user_index = index2+1
                    break
        return output_list


@router.put("/admin_state", response_model=Project2UserDB, status_code=200)
async def update_admin_state(update: Project2UserDB, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    await project2user.admin_check(ProjectPrimaryKeyUserID(project_id=update.project_id, user_id=user.user_id))
    project = await projects.get(update.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_deserialized = ProjectPrimaryKeyName(**project)

    admins = await project2user.get_admins_by_project(update.project_id)
    if len(admins) == 1 and not update.is_admin:
        raise HTTPException(status_code=403, detail="There has to be at least one admin")

    update_res = await project2user.put_admin_state(update)
    if not update_res:
        raise HTTPException(status_code=404, detail="The admin state could not be changed")

    user_res = await get_user_by_id(update.user_id)
    payload = ProjectPrimaryKeyNameEmailAdmin(project_id=update.project_id, name=project_deserialized.name, e_mail=user_res.email, is_admin=update.is_admin)
    await mail_um_put_changed_user(payload)

    admin_ids = [Project2UserDB(**admin).user_id for admin in admins]
    auth0_admins = await get_user_list_by_id(admin_ids)
    for auth0_admin in auth0_admins:
        await mail_um_put_admin(payload, EmailStr(auth0_admin.email))
    return update


@router.delete("/external_from_project")
async def delete_external_from_project(payload: Project2ExternalDB, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    await project2user.admin_check(ProjectPrimaryKeyUserID(project_id=payload.project_id, user_id=user.user_id))

    project = await projects.get(payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_deserialized = ProjectPrimaryKeyName(**project)

    await project2external.delete(payload)

    admins = await project2user.get_admins_by_project(payload.project_id)
    admin_ids = [Project2UserDB(**admin).user_id for admin in admins]
    auth0_admins = await get_user_list_by_id(admin_ids)
    for auth0_admin in auth0_admins:
        await mail_um_delete_external(ProjectPrimaryKeyNameEmail(project_id=payload.project_id, name=project_deserialized.name, e_mail=user.email), EmailStr(auth0_admin.email))
    return "No record remaining"


@router.delete("/all_externals_from_project")
async def delete_all_externals_from_project(primary_key: ProjectPrimaryKey, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    await project2user.admin_check(ProjectPrimaryKeyUserID(project_id=primary_key.project_id, user_id=user.user_id))

    project = await projects.get(primary_key.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_deserialized = ProjectPrimaryKeyName(**project)

    await project2external.delete_by_project(primary_key.project_id)

    admins = await project2user.get_admins_by_project(primary_key.project_id)
    admin_ids = [Project2UserDB(**admin).user_id for admin in admins]
    auth0_admins = await get_user_list_by_id(admin_ids)
    for auth0_admin in auth0_admins:
        await mail_um_delete_all_externals(ProjectPrimaryKeyNameEmail(project_id=primary_key.project_id, name=project_deserialized.name, e_mail=EmailStr(auth0_admin.email)))
    return "No records remaining"


@router.delete("/user_from_project")
async def delete_user_from_project(payload: Project2UserDB, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    if payload.user_id != user.user_id:
        await project2user.admin_check(ProjectPrimaryKeyUserID(project_id=payload.project_id, user_id=user.user_id))

    project = await projects.get(payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_deserialized = ProjectPrimaryKeyName(**project)

    admins = await project2user.get_admins_by_project(payload.project_id)
    admin_ids = [Project2UserDB(**admin).user_id for admin in admins]
    if len(admins) == 1 and admin_ids[0] == payload.user_id:
        raise HTTPException(status_code=403, detail="There has to be at least one admin")

    user_res = await get_user_by_id(payload.user_id)
    await project2user.delete(payload)
    namespaces_project = await namespaces.get_by_project(payload.project_id)
    if namespaces_project:
        for namespaces_project_item in namespaces_project:
            namespace_item = NamespaceSchema(**namespaces_project_item)
            await users.delete_kubernetes_user(NamespacePrimaryKeyEmail(name=namespace_item.name, region=namespace_item.region, e_mail=user_res.email))

    payload_email = ProjectPrimaryKeyNameEmail(project_id=payload.project_id, name=project_deserialized.name, e_mail=user_res.email)
    await mail_um_delete_deleted_user(payload_email)

    auth0_admins = await get_user_list_by_id(admin_ids)
    for auth0_admin in auth0_admins:
        await mail_um_delete_admin(payload_email, EmailStr(auth0_admin.email))
    return "No record remaining"


@router.delete("/user_candidate")
async def decline_invitation(payload: ProjectPrimaryKeyUserID, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    await project2user.admin_check(ProjectPrimaryKeyUserID(project_id=payload.project_id, user_id=user.user_id))

    candidate_res = await project2usercandidate.get(payload)
    if not candidate_res:
        raise HTTPException(status_code=404, detail="No invitation found for user and project")

    await project2usercandidate.delete(payload)

    project = await projects.get(payload.project_id)
    project_deserialized = ProjectPrimaryKeyName(**project)
    payload = ProjectPrimaryKeyNameEmail(project_id=payload.project_id, name=project_deserialized.name, e_mail=user.email)
    await mail_um_delete_accept_internal(payload)

    admins = await project2user.get_admins_by_project(project_deserialized.project_id)
    admin_ids = [Project2UserDB(**admin).user_id for admin in admins]
    auth0_admins = await get_user_list_by_id(admin_ids)
    for auth0_admin in auth0_admins:
        await mail_um_delete_accept_internal_admin(payload, EmailStr(auth0_admin.email))
    return "User candidate deleted"


@router.delete("/decline_user_invitation")
async def decline_invitation(primary_key: ProjectPrimaryKey, user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    payload = ProjectPrimaryKeyUserID(project_id=primary_key.project_id, user_id=user.user_id)
    candidate_res = await project2usercandidate.get(payload)
    if not candidate_res:
        raise HTTPException(status_code=404, detail="No invitation found for user and project")

    await project2usercandidate.delete(payload)

    project = await projects.get(primary_key.project_id)
    project_deserialized = ProjectPrimaryKeyName(**project)
    payload = ProjectPrimaryKeyNameEmail(project_id=primary_key.project_id, name=project_deserialized.name, e_mail=user.email)
    await mail_um_delete_accept_internal(payload)

    admins = await project2user.get_admins_by_project(project_deserialized.project_id)
    admin_ids = [Project2UserDB(**admin).user_id for admin in admins]
    auth0_admins = await get_user_list_by_id(admin_ids)
    for auth0_admin in auth0_admins:
        await mail_um_delete_accept_internal_admin(payload, EmailStr(auth0_admin.email))
    return "Declined"
