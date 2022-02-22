from fastapi import APIRouter
from fastapi import Depends

from app.api.email.ping import write_test_mail

router = APIRouter()

@router.get("/ping")
async def pong():
    return {"ping": "pong!"}

@router.get("/ping2")
async def pong2(email: str):
    await write_test_mail(email)
    return {"ping": "pong2!"}