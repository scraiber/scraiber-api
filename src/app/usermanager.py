from typing import Optional
import os
from asyncpg.exceptions import UniqueViolationError
from fastapi import Depends, Request, HTTPException
from fastapi_users import BaseUserManager, models

from .db import get_user_db
from app.api.models.users import UserCreate, UserDB
from app.api.crud import project2external, project2ownercandidate, project2user, projects
from app.api.models.projects import ProjectPrimaryKey, Project2ExternalDB, Project2UserDB, ProjectSchemaDB
from app.api.email.user_management import mail_um_post_internal, mail_um_post_internal_owner 
from app.api.email.fastapi_user import *

scraiber_api_secret = os.getenv("SCRAIBER_API_SECRET")



class UserManager(BaseUserManager[UserCreate, UserDB]):

    user_db_model = UserDB
    reset_password_token_secret = scraiber_api_secret
    verification_token_secret = scraiber_api_secret



    async def on_after_register(self, user: UserDB, request: Optional[Request] = None):
        await mail_registration_confirmation(user.email)
        projects_to_add = await project2external.get_by_email(user.email)
        if projects_to_add:
            projects_to_add_deserialized = [Project2ExternalDB(**item).dict() for item in projects_to_add]
            for item in projects_to_add_deserialized:
                try:
                    await project2user.post(Project2UserDB(name=item.name, region=item.region, user_id=user.id, is_admin=item.is_admin))

                    project = await projects.get(ProjectPrimaryKey(name=item.name, region=item.region))
                    project_deserialized = ProjectSchemaDB(**project)
                    owner_res = await self.get(project_deserialized.owner_id) 
                        
                    payload = Project2ExternalDB(name=item.name, region=item.region, e_mail=user.email, is_admin=False)
                    owner_email = owner_res.email

                    await mail_um_post_internal(payload)
                    await mail_um_post_internal_owner(payload, owner_email)
                except UniqueViolationError:
                    pass
            await project2external.delete_by_email(user.email)
        print(f"User {user.id} has registered.")
        await self.request_verify(user, request)



    async def on_after_forgot_password(self, user: UserDB, token: str, request: Optional[Request] = None):
        await mail_password_reset(user.email, token)
        print(f"User {user.id} has forgot his password. Reset token: {token}")



    async def on_after_reset_password(self, user: models.UD, request: Optional[Request] = None):
        await mail_password_reset_confirmation(user.email)
        print(f"User {user.id} has reset his password.")



    async def on_after_request_verify(self, user: UserDB, token: str, request: Optional[Request] = None):
        await mail_verify_account(user.email, token)
        print(f"Verification requested for user {user.id}. Verification token: {token}")



    async def on_after_verify(self, user: models.UD, request: Optional[Request] = None):
        await mail_verification_confirmation(user.email)
        print(f"Verification for user {user.id} successful")



    async def delete(self, user: UserDB) -> None:
        """
        Delete a user.

        :param user: The user to delete.
        """
        if await projects.get_by_owner(user.id):
            raise HTTPException(status_code=403, detail="You still own projects. Please transfer the ownership or delete them.")
        await project2ownercandidate.delete_by_candidate(user.id)
        await project2user.delete_by_user(user.id)
        await mail_deletion_confirmation(user.email)
        await self.user_db.delete(user)
        return


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)
