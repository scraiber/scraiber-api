from typing import Optional
import os
from asyncpg.exceptions import UniqueViolationError
from fastapi import Depends, Request, params, HTTPException
from fastapi_users import BaseUserManager

from .db import get_user_db
from app.api.models.users import UserCreate, UserDB
from app.api.crud import project2external, project2ownercandidate, project2user, projects
from app.api.models.projects import Project2ExternalDB, Project2UserDB


import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException


configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = os.getenv("SENDINBLUE_API_KEY")

api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


SECRET = os.getenv("SCRAIBER_API_SECRET")



class UserManager(BaseUserManager[UserCreate, UserDB]):

    user_db_model = UserDB

    reset_password_token_secret = SECRET

    verification_token_secret = SECRET



    async def on_after_register(self, user: UserDB, request: Optional[Request] = None):
        projects_to_add = await project2external.get_by_email(user.email)
        if projects_to_add:
            projects_to_add_deserialized = [Project2ExternalDB(**item).dict() for item in projects_to_add]
            for item in projects_to_add_deserialized:
                try:
                    await project2user.post(Project2UserDB(name=item.name, region=item.region, user_id=user.id, is_admin=item.is_admin))
                except UniqueViolationError:
                    pass
            await project2external.delete_by_email(user.email)
            #TODO: Write e-mail to user resp. owners
        print(f"User {user.id} has registered.")
        await self.request_verify(user, request)


    async def on_after_forgot_password(self, user: UserDB, token: str, request: Optional[Request] = None):

        print(f"User {user.id} has forgot their password. Reset token: {token}")


    async def delete(self, user: UserDB) -> None:
        """
        Delete a user.

        :param user: The user to delete.
        """
        if await projects.get_by_owner(user.id):
            raise HTTPException(status_code=403, detail="You still own projects. Please transfer the ownership or delte them.")
        await project2ownercandidate.delete_by_candidate(user.id)
        await project2user.delete_by_user(user.id)
        #TODO: Write e-mail for confirming deletion
        await self.user_db.delete(user)


    async def on_after_request_verify(self, user: UserDB, token: str, request: Optional[Request] = None):
        """
        print(f"Verification requested for user {user.id}. Verification token: {token}")
        subject = "Scraiber registration"
        html_content = "<html><body><h1>Please use to verify e-mail {0}</h1></body></html>".format(token)
        sender = {"name":"Scraiber","email":"no-reply@scraiber.com"}
        to = [{"email":user.email,"name":"Tobi"}]
        #cc = [{"email":"example2@example2.com","name":"Janice Doe"}]
        #bcc = [{"name":"John Doe","email":"example@example.com"}]
        reply_to = {"name":"Scraiber","email":"no-reply@scraiber.com"}
        headers = {"Some-Custom-Name":"unique-id-1234"}
        params = {"link": "https://www.bbc.com/"}
        #params = {"parameter":"My param value","subject":"New Subject"}
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(to=to, reply_to=reply_to, headers=headers, html_content=html_content, sender=sender, subject=subject)


        try:
            api_response = api_instance.send_transac_email(send_smtp_email)
            print(api_response)
        except ApiException as e:
            print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)
        """



async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)
