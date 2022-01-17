from fastapi import HTTPException

from app.api.models.certificates import Certificate2User, Certificate2UserDB
from app.db import certificate2user, database


async def post(payload: Certificate2User):
    query = certificate2user.insert().values(region=payload.region, user_id=payload.user_id, certificate_no=1)
    return await database.execute(query=query)


async def get(payload: Certificate2User):
    query = certificate2user.select().where(payload.region == certificate2user.c.region).where(payload.user_id == certificate2user.c.user_id)
    return await database.fetch_one(query=query)


async def get_certificate_number(payload: Certificate2User):
    cert2user_respponse = await get(payload)
    if not cert2user_respponse:
        raise HTTPException(status_code=404, detail="No Certifcate for cluster and user found") 
    return Certificate2UserDB(**cert2user_respponse).certificate_no


async def put(payload: Certificate2UserDB):
    query = (
        certificate2user
        .update()
        .where(payload.region == certificate2user.c.region).where(payload.user_id == certificate2user.c.user_id)
        .values(certificate_no=payload.certificate_no)
        .returning(certificate2user.c.region, certificate2user.c.user_id, certificate2user.c.certificate_no)
    )
    return await database.execute(query=query)


async def create_or_increment(payload: Certificate2User):
    response = await get(payload)
    if not response:
        await post(payload)
        return Certificate2UserDB(region=payload.region, user_id=payload.user_id, certificate_no=1)
    else:
        update_model = Certificate2UserDB(**response)
        update_model.certificate_no = update_model.certificate_no+1
        await put(update_model)
        return update_model


async def delete(payload: Certificate2User):
    query = certificate2user.delete().where(payload.region == certificate2user.c.region).where(payload.user_id == certificate2user.c.user_id)
    return await database.execute(query=query)
