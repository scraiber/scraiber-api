import os
import requests
from pydantic import EmailStr
from typing import List
from fastapi import HTTPException

from app.api.models.auth0 import Auth0User


async def get_user_by_email(email: EmailStr) -> Auth0User:

    headers = {'Authorization': 'Bearer '+os.environ["ACCESS_TOKEN"]}
    params = {'email': email, 'fields': 'email,email_verified,nickname,name,user_id'}

    response = requests.get('https://scraiber.eu.auth0.com/api/v2/users-by-email', headers=headers, params=params)
    
    if response.status_code != 200 or len(response.json())==0:
        raise HTTPException(status_code=404, detail="User could not be retrieved")

    user_response = response.json()[0]
    return Auth0User(**user_response)



async def get_user_by_id(id: str) -> Auth0User:

    headers = {'Authorization': 'Bearer '+os.environ["ACCESS_TOKEN"]}
    params = {'fields': 'email,email_verified,nickname,name,user_id'}

    response = requests.get('https://scraiber.eu.auth0.com/api/v2/users/'+id, headers=headers, params=params)

    if response.status_code != 200 or len(response.json())==0:
        raise HTTPException(status_code=404, detail="User could not be retrieved")

    user_response = response.json()
    return Auth0User(**user_response)



async def get_user_list_by_email(email_list: List[EmailStr], require_200_status_code: bool = False) -> List[Auth0User]:
    output_list = []

    for email in email_list:
        if require_200_status_code:
            user = await get_user_by_email(email)
            if user:
                output_list.append(user) 
        else:          
            try:
                user = await get_user_by_email(email)
                if user:
                    output_list.append(user)
            except:
                continue
    
    return output_list



async def get_user_list_by_id(id_list: List[str], require_200_status_code: bool = False) -> List[Auth0User]:
    output_list = []

    for id in id_list:
        if require_200_status_code:
            user = await get_user_by_id(id)
            if user:
                output_list.append(user)
        else:
            try:
                user = await get_user_by_id(id)
                if user:
                    output_list.append(user)
            except:
                continue
    return output_list



async def delete_user_by_id(id: str) -> bool:

    headers = {'Authorization': 'Bearer '+os.environ["ACCESS_TOKEN"]}

    response = requests.delete('https://scraiber.eu.auth0.com/api/v2/users/'+id, headers=headers)

    if response.status_code == 204:
        return True
    else:
        raise HTTPException(status_code=404, detail="User could not be deleted")