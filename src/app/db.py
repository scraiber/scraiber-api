import os
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    Float,
    MetaData,
    String,
    Boolean,
    Table,
    create_engine
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base

from databases import Database


DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy
engine = create_engine(DATABASE_URL)
metadata = MetaData()


projects = Table(
    "projects",
    metadata,
    Column("project_id", UUID, primary_key=True, default=uuid.uuid4()),
    Column("name", String(50)),
    Column("created_date", DateTime, default=func.now(), nullable=False),
)
namespaces = Table(
    "namespaces",
    metadata,
    Column("name", String(50), primary_key=True),
    Column("region", String, primary_key=True),
    Column("max_namespace_cpu", Float),
    Column("max_namespace_mem", Float),
    Column("default_limit_pod_cpu", Float),
    Column("default_limit_pod_mem", Float),
    Column("project_id", UUID),
    Column("created_date", DateTime, default=func.now(), nullable=False),
)
namespace2projecttransfer = Table(
    "namespace2projecttransfer",
    metadata,
    Column("name", String(50), primary_key=True),
    Column("region", String, primary_key=True),
    Column("old_project_id", UUID),
    Column("new_project_id", UUID),
    Column("created_date", DateTime, default=func.now(), nullable=False),
)
project2user = Table(
    "project2user",
    metadata,
    Column("project_id", UUID, primary_key=True),
    Column("user_id", String, primary_key=True),
    Column("is_admin", Boolean, default=False, nullable=False),
    Column("created_date", DateTime, default=func.now(), nullable=False),
)
project2usercandidate = Table(
    "project2usercandidate",
    metadata,
    Column("project_id", UUID, primary_key=True),
    Column("user_id", String, primary_key=True),
    Column("is_admin", Boolean, default=False, nullable=False),
    Column("created_date", DateTime, default=func.now(), nullable=False),
)
project2external = Table(
    "project2external",
    metadata,
    Column("project_id", UUID, primary_key=True),
    Column("e_mail", String(320), primary_key=True),
    Column("is_admin", Boolean, default=False, nullable=False),
    Column("created_date", DateTime, default=func.now(), nullable=False),
)

# databases query builder
database = Database(DATABASE_URL)


Base: DeclarativeMeta = declarative_base()

Base.metadata.create_all(engine)
