from fastapi import FastAPI

from app.api.routes import ping, notes, project2user_management, projects
from app.db import database, engine, metadata
from app.fastapiusers import fastapi_users, jwt_authentication
from fastapi_utils.tasks import repeat_every




metadata.create_all(engine)

app = FastAPI()


@app.on_event("startup")
async def startup():
    await database.connect()

'''
counter = 0
@app.on_event("startup")
@repeat_every(seconds=1, wait_first=True)
def periodic():
    global counter
    print('counter is', counter)
    counter += 1
'''

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()




app.include_router(ping.router)
app.include_router(notes.router, prefix="/notes", tags=["notes"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(project2user_management.router, prefix="/project2external", tags=["project2external"])
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
