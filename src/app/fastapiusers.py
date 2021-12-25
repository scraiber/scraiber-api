from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication
import os

from app.api.models.users import User, UserCreate, UserUpdate, UserDB
from app.usermanager import get_user_manager


SECRET = os.getenv("SCRAIBER_API_SECRET")

jwt_authentication = JWTAuthentication(secret=SECRET, lifetime_seconds=3600)

fastapi_users = FastAPIUsers(
    get_user_manager,
    [jwt_authentication],
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)

current_user = fastapi_users.current_user()
current_active_user = fastapi_users.current_user(verified=True)