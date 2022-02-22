from fastapi import APIRouter
from fastapi import Depends, HTTPException

from app.api.models.auth0 import Auth0User
from app.api.models.certificates import Certificate2User
from app.api.models.projects import RegionEmail
from app.auth0 import current_user
from app.api.kubernetes.users import create_kubernetes_config
from app.api.email.kubernetes import mail_kubernetes_new_kubeconfig
from app.kubernetes_setup import cluster_info


router = APIRouter()

@router.get("/generate-config", status_code=201)
async def generate_kubernetes_config_for_user(region: str, user: Auth0User = Depends(current_user)):
    response = await create_kubernetes_config(Certificate2User(region=region, user_id=user.user_id))
    if not response:
        raise HTTPException(status_code=400, detail="Could not create config for user")
    else:
        await mail_kubernetes_new_kubeconfig(RegionEmail(region=region, e_mail=user.email))
        return {"config": response}


@router.get("/clusters", status_code=200)
async def get_clusters(user: Auth0User = Depends(current_user)):
    return cluster_info
