from pydantic import BaseModel, Field, validator, EmailStr, root_validator
from typing import Dict, Any

from app.kubernetes_setup import clusters


class ProjectPrimaryKey(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    region: str
    
    @validator('region')
    def region_must_be_in_list(cls, field_value):
        if field_value not in clusters.keys():
            raise ValueError('must be in the regions offered')
        return field_value



class ProjectPrimaryKeyEmail(ProjectPrimaryKey):
    e_mail: EmailStr

class Project2ExternalDB(ProjectPrimaryKeyEmail):
    is_admin: bool = False



class PrimaryKeyWithUserID(ProjectPrimaryKey):
    candidate_id: str

class PrimaryKeyWithUserIDAndCertNo(PrimaryKeyWithUserID):
    certificate_no: int = Field(..., ge=1)



class Project2UserDB(ProjectPrimaryKey):
    user_id: str
    is_admin: bool = False

    

class ProjectSchema(ProjectPrimaryKey):
    max_project_cpu: float = Field(..., ge=0)
    max_project_mem: float = Field(..., ge=0)
    default_limit_pod_cpu: float = Field(..., ge=0)
    default_limit_pod_mem: float = Field(..., ge=0)

    @root_validator()
    def validate_cpu(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get('max_project_cpu')<values.get('default_limit_pod_cpu'):
            raise ValueError('The CPU maximum for the project must not be smaller than the default CPU for a pod')
        return values

    @root_validator()
    def validate_mem(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get('max_project_mem')<values.get('default_limit_pod_mem'):
            raise ValueError('The memory maximum for the project must not be smaller than the default memory for a pod')
        return values

class ProjectSchemaDB(ProjectSchema):
    owner_id: str

class ProjectSchemaEmail(ProjectSchema):
    e_mail: EmailStr


class RegionEmail(BaseModel):
    region: str
    e_mail: EmailStr
    
    @validator('region')
    def region_must_be_in_list(cls, field_value):
        if field_value not in clusters.keys():
            raise ValueError('must be in the regions offered')
        return field_value

