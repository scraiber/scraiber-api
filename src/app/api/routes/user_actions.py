
from fastapi import APIRouter, HTTPException, Depends

from app.api.crud import project2user, project2external, project2ownercandidate, projects
from app.api.models.projects import ProjectPrimaryKey, ProjectSchemaDB, Project2UserDB
from app.api.models.auth0 import Auth0User
from app.api.auth0.users import get_user_by_id, delete_user_by_id
from app.api.email.fastapi_user import *
from app.api.email.user_management import mail_um_post_internal, mail_um_post_internal_owner 
from app.api.email.projects import *
from app.auth0 import current_user, check_email_verified

router = APIRouter()



@router.post("/", status_code=201)
async def on_after_email_verification(user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    projects_to_add = await project2external.get_by_email(user.email)
    if projects_to_add:
        projects_to_add_deserialized = [Project2ExternalDB(**item).dict() for item in projects_to_add]
        for item in projects_to_add_deserialized:
            try:
                await project2user.post(Project2UserDB(name=item.name, region=item.region, user_id=user.user_id, is_admin=item.is_admin))

                payload = Project2ExternalDB(name=item.name, region=item.region, e_mail=user.email, is_admin=False)
                await mail_um_post_internal(payload)

                project = await projects.get(ProjectPrimaryKey(name=item.name, region=item.region))
                project_deserialized = ProjectSchemaDB(**project)
                owner_res = await get_user_by_id(project_deserialized.owner_id) 
                owner_email = owner_res.email
                await mail_um_post_internal_owner(payload, owner_email)
            except:
                pass
        await project2external.delete_by_email(user.email)



@router.delete("/", status_code=200)
async def delete_user(user: Auth0User = Depends(current_user)):
    if await projects.get_by_owner(user.user_id):
        raise HTTPException(status_code=403, detail="You still own projects. Please transfer the ownership or delete them.")
    await delete_user_by_id(user.user_id)
    await project2ownercandidate.delete_by_candidate(user.user_id)
    await project2user.delete_by_user(user.user_id)
    await mail_deletion_confirmation(user.email)
