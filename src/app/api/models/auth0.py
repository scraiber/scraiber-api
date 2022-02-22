from pydantic import Field
from fastapi_cloudauth.auth0 import Auth0Claims


class Auth0User(Auth0Claims):
    user_id: str = Field(alias="sub")
    nickname: str = Field(None, alias="nickname")
    is_verified: bool = Field(alias="email_verified")

    class Config:
        allow_population_by_field_name = True