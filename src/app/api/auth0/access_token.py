import os
import requests


async def get_access_token():
    # Get an Access Token from Auth0
    payload =  { 
    'grant_type': 'client_credentials',
    'client_id': os.environ["AUTH0_CLIENTID_BACKEND"],
    'client_secret': os.environ["AUTH0_CLIENT_SECRET_BACKEND"],
    'audience': os.environ["AUTH0_AUDIENCE"]
    }

    response = requests.post('https://{domain}/oauth/token'.format(domain = os.environ["AUTH0_DOMAIN"]), data=payload)
    response.status_code
    if response.status_code != 200:
        return {"status_code": response.status_code, "access_token": ""}

    oauth = response.json()
    return {"status_code": 200, "access_token": oauth.get('access_token')}