import os
from fastapi import HTTPException
from fastapi_cloudauth.auth0 import Auth0CurrentUser

from app.api.models.auth0 import Auth0User


current_user = Auth0CurrentUser(
    domain=os.environ["AUTH0_DOMAIN"],
    client_id=os.environ["AUTH0_CLIENTID_FRONTEND"]
)

current_user.user_info = Auth0User 


async def check_email_verified(user: Auth0User):
    if not user.is_verified:
        raise HTTPException(status_code=401, detail="User e-mail not verified")
