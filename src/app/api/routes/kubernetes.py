from fastapi import APIRouter
from fastapi import Depends, HTTPException
from pydantic import EmailStr

from app.api.models.auth0 import Auth0User
from app.auth0 import current_user, check_email_verified
from app.api.kubernetes.users import create_kubernetes_config
from app.api.email.kubernetes import mail_kubernetes_new_kubeconfig
from app.kubernetes_setup import cluster_info


router = APIRouter()


@router.get("/generate-config", status_code=200)
async def generate_kubernetes_config_for_user(user: Auth0User = Depends(current_user)):
    await check_email_verified(user)
    response = await create_kubernetes_config(user.user_id)
    if len(response) == 0:
        raise HTTPException(status_code=400, detail="Could not create config for user")
    else:
        await mail_kubernetes_new_kubeconfig(e_mail=EmailStr(user.email))
        return {"config": response}


@router.get("/clusters", status_code=200)
async def get_clusters(user: Auth0User = Depends(current_user)):
    await check_email_verified(user)

    return cluster_info
