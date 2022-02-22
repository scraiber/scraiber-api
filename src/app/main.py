from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
import os

from app.api.routes import kubernetes, ping, projects, user_actions, user_management, owner_transfer
from app.db import database, engine, metadata
from app.api.crud import project2external
from app.api.auth0 import access_token


 


metadata.create_all(engine)

app = FastAPI()


@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("startup")
@repeat_every(seconds=3600, wait_first=True)
async def periodic_external_delte():
    await project2external.delete_by_time()


@app.on_event("startup")
@repeat_every(seconds=3600)
async def periodic_access_token():
    access_token_candidate = await access_token.get_access_token()
    if access_token_candidate:
        if access_token_candidate["status_code"] == 200:
            os.environ["ACCESS_TOKEN"] = access_token_candidate["access_token"]



@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()




app.include_router(ping.router)
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(user_management.router, prefix="/project_user_management", tags=["project_user_management"])
app.include_router(owner_transfer.router, prefix="/owner_transfer", tags=["owner_transfer"])
app.include_router(kubernetes.router, prefix="/kubernetes", tags=["kubernetes"])
app.include_router(user_actions.router, prefix="/user_actions", tags=["user_actions"])