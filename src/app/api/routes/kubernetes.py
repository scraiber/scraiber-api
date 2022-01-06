from fastapi import APIRouter
from fastapi import Depends, HTTPException

from app.api.models.users import User
from app.api.models.certificates import Certificate2User
from app.fastapiusers import current_user
from app.api.kubernetes.users import create_kubernetes_config


router = APIRouter()

@router.get("/generate-config", status_code=201)
async def generate_kubernetes_config_for_user(region: str, user: User = Depends(current_user)):
    response = await create_kubernetes_config(Certificate2User(region=region, user_id=user.id))
    if not response:
        raise HTTPException(status_code=400, detail="Could not create config for user")
    else:
        return {"config": response}
