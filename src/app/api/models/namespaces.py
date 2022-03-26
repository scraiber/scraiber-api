from pydantic import BaseModel, Field, validator, root_validator, EmailStr, UUID4
from typing import Dict, Any

from app.kubernetes_setup import clusters


class NamespacePrimaryKey(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    region: str

    @validator('region')
    def region_must_be_in_list(cls, field_value):
        if field_value not in clusters.keys():
            raise ValueError('must be in the regions offered')
        return field_value


class NamespaceResources(NamespacePrimaryKey):
    max_namespace_cpu: float = Field(..., ge=0)
    max_namespace_mem: float = Field(..., ge=0)
    default_limit_pod_cpu: float = Field(..., ge=0)
    default_limit_pod_mem: float = Field(..., ge=0)

    @root_validator()
    def validate_cpu(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get('max_namespace_cpu')<values.get('default_limit_pod_cpu'):
            raise ValueError('The CPU maximum for the project must not be smaller than the default CPU for a pod')
        return values

    @root_validator()
    def validate_mem(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get('max_namespace_mem')<values.get('default_limit_pod_mem'):
            raise ValueError('The memory maximum for the project must not be smaller than the default memory for a pod')
        return values
    
class NamespaceSchema(NamespaceResources):
    project_id: UUID4

class NamespaceSchemaProjectNameEmailInfo(NamespaceSchema):
    project_name: str
    e_mail: EmailStr
    creator: str

class NamespacePrimaryKeyProjectID(NamespacePrimaryKey):
    project_id: UUID4

class NamespacePrimaryKeyEmail(NamespacePrimaryKey):
    e_mail: EmailStr

class NamespacePrimaryKeyEmailInfo(NamespacePrimaryKeyEmail):
    project_id: UUID4
    project_name: str
    creator: str


class NamespacePrimaryKeyUserID(NamespacePrimaryKey):
    user_id: str


class NamespacePrimaryKeyTransfer(NamespacePrimaryKey):
    old_project_id: UUID4
    new_project_id: UUID4

    @root_validator()
    def validate_ids(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get('old_project_id') == values.get('new_project_id'):
            raise ValueError('The source and target project must be different')
        return values


class NamespacePrimaryKeyTransferEmailInfo(NamespacePrimaryKeyTransfer):
    old_project_name: str
    new_project_name: str
    creator: str
    e_mail: EmailStr


class NamespaceResourcesTransferInfo(NamespaceResources):
    old_project_id: UUID4
    new_project_id: UUID4
    old_project_name: str
    new_project_name: str
