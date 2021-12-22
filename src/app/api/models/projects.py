import uuid
from pydantic import BaseModel, Field, UUID4, validator, EmailStr
from app.api.models.users import User
import os
import json

cluster_dict = json.loads(os.environ['CLUSTER_DICT'])


class ProjectPrimaryKey(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    region: str
    
    @validator('region')
    def region_must_be_in_list(cls, field_value):
        if field_value not in cluster_dict.keys():
            raise ValueError('must be in the regions offered')
        return field_value

class ProjectSchema(ProjectPrimaryKey):
    limits_cpu: float = Field(..., ge=0)
    limits_mem: float = Field(..., ge=0)

class ProjectSchemaDB(ProjectSchema):
    owner_id: UUID4

class Project2UserDB(ProjectPrimaryKey):
    user_id: UUID4
    is_admin: bool = False

class Project2OwnerCandidateDB(ProjectPrimaryKey):
    candidate_id: UUID4

class Project2ExternalDB(ProjectPrimaryKey):
    e_mail: EmailStr
    is_admin: bool = False