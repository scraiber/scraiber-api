from pydantic import BaseModel, Field, validator, EmailStr, UUID4
from typing import List, Optional
import uuid
from app.api.models.namespaces import NamespaceSchema, NamespacePrimaryKeyTransfer
from app.api.models.auth0 import Auth0UserWithAdmin
from app.kubernetes_setup import clusters


class ProjectPrimaryKey(BaseModel):
    project_id: UUID4 = Field(default_factory=uuid.uuid4)

class ProjectName(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)

class ProjectPrimaryKeyName(ProjectPrimaryKey):
    name: str = Field(..., min_length=3, max_length=50)



class ProjectPrimaryKeyUserID(ProjectPrimaryKey):
    user_id: str

class Project2UserDB(ProjectPrimaryKeyUserID):
    is_admin: bool = False



class ProjectPrimaryKeyEmail(ProjectPrimaryKey):
    e_mail: EmailStr

class Project2ExternalDB(ProjectPrimaryKeyEmail):
    is_admin: bool = False


class ProjectPrimaryKeyNameEmail(ProjectPrimaryKeyName):
    e_mail: EmailStr

class ProjectPrimaryKeyNameEmailAdmin(ProjectPrimaryKeyNameEmail):
    is_admin: bool

class EmailWithUserID(BaseModel):
    e_mail: EmailStr
    user_id: str



class ProjectCompleteInfo(ProjectPrimaryKeyName):
    namespaces: List[NamespaceSchema]
    users: List[Auth0UserWithAdmin]
    user_candidates: List[Auth0UserWithAdmin]
    externals: List[EmailStr]
    transfer_source_namespace: List[NamespacePrimaryKeyTransfer]
    transfer_target_namespace: List[NamespacePrimaryKeyTransfer]







