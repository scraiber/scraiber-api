from pydantic import BaseModel, Field


class Certificate2User(BaseModel):
    region: str
    user_id: str


class Certificate2UserDB(Certificate2User):
    certificate_no: int = Field(..., ge=1)