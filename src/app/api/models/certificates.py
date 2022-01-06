from pydantic import BaseModel, Field, UUID4


class Certificate2User(BaseModel):
    region: str
    user_id: UUID4


class Certificate2UserDB(Certificate2User):
    certificate_no: int = Field(..., ge=1)