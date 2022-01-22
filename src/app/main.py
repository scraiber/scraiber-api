from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every

from app.api.routes import kubernetes, ping, projects, user_management, owner_transfer
from app.db import database, engine, metadata
from app.fastapiusers import fastapi_users, jwt_authentication
from app.api.crud import project2external


 


metadata.create_all(engine)

app = FastAPI()


@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("startup")
@repeat_every(seconds=3600, wait_first=True)
async def periodic():
    await project2external.delete_by_time()






@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()




app.include_router(ping.router)
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(user_management.router, prefix="/project_user_management", tags=["project_user_management"])
app.include_router(owner_transfer.router, prefix="/owner_transfer", tags=["owner_transfer"])
app.include_router(kubernetes.router, prefix="/kubernetes", tags=["kubernetes"])

app.include_router(
    fastapi_users.get_auth_router(jwt_authentication),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(),
    prefix="/users",
    tags=["users"],
)
