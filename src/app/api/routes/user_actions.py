from fastapi import APIRouter, HTTPException, Depends

from app.api.crud import project2usercandidate, project2user, project2external, projects, namespaces
from app.api.models.projects import ProjectPrimaryKeyNameEmailAdmin, Project2UserDB, ProjectPrimaryKeyName
from app.api.models.namespaces import NamespacePrimaryKey, NamespacePrimaryKeyEmail
from app.api.models.auth0 import Auth0User
from app.api.auth0.users import delete_user_by_id, get_user_list_by_id
from app.api.email.user_actions import *
from app.api.kubernetes import users
from app.api.email.user_management import mail_um_post_internal, mail_um_post_internal_admin
from app.auth0 import current_user, check_email_verified

router = APIRouter()


@router.post("/", status_code=201)
async def on_after_email_verification(user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    projects_to_add = await project2external.get_by_email(EmailStr(user.email))
    if projects_to_add:
        projects_to_add_deserialized = [Project2ExternalDB(**item) for item in projects_to_add]
        for item in projects_to_add_deserialized:
            try:
                await project2usercandidate.post(Project2UserDB(project_id=item.project_id, user_id=user.user_id, is_admin=item.is_admin))
                project_res = await projects.get(item.project_id)
                if not project_res:
                    continue

                project = ProjectPrimaryKeyName(**project_res)
                payload = ProjectPrimaryKeyNameEmailAdmin(project_id=item.project_id, name=project.name, e_mail=user.email, is_admin=False)
                await mail_um_post_internal(payload)

                admins = await project2user.get_admins_by_project(item.project_id)
                if not admins:
                    continue

                admin_ids = [Project2UserDB(**admin).user_id for admin in admins]
                auth0_admins = await get_user_list_by_id(admin_ids)
                for auth0_admin in auth0_admins:
                    await mail_um_post_internal_admin(payload, EmailStr(auth0_admin.email))
            except:
                pass
        await project2external.delete_by_email(EmailStr(user.email))


@router.delete("/", status_code=200)
async def delete_user(user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    projects_for_user_res = await project2user.get_by_user(user.user_id)
    if projects_for_user_res:
        projects_des = [Project2UserDB(**projects_for_user_res_item) for projects_for_user_res_item in projects_for_user_res]

        project_ids = [project.project_id for project in projects_des if project.is_admin]
        for project_id in project_ids:
            user_admins_for_project_res = await project2user.get_admins_by_project(project_id)
            if len(user_admins_for_project_res) == 1:
                raise HTTPException(status_code=403, detail="There are projects where you are the only admin. Please add at least another admin per project or delete them.")

        project_ids = [project.project_id for project in projects_des]
        for project_id in project_ids:
            namespaces_list = await namespaces.get_by_project(project_id)
            for namespace_res in namespaces_list:
                namespace_item = NamespacePrimaryKey(**namespace_res)
                await users.delete_kubernetes_user(
                    NamespacePrimaryKeyEmail(name=namespace_item.name, region=namespace_item.region, e_mail=user.email))

    await project2usercandidate.delete_by_user(user.user_id)
    await project2user.delete_by_user(user.user_id)
    await delete_user_by_id(user.user_id)
    await mail_deletion_confirmation(EmailStr(user.email))
