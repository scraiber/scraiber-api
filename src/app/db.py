import os

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
    Column("name", String(50), primary_key=True),
    Column("region", String, primary_key=True),
    Column("max_project_cpu", Float),
    Column("max_project_mem", Float),
    Column("default_limit_pod_cpu", Float),
    Column("default_limit_pod_mem", Float),
    Column("owner_id", String),
    Column("created_date", DateTime, default=func.now(), nullable=False),
)
project2user = Table(
    "project2user",
    metadata,
    Column("name", String(50), primary_key=True),
    Column("region", String, primary_key=True),
    Column("user_id", String, primary_key=True),
    Column("is_admin", Boolean, default=False, nullable=False),
    Column("created_date", DateTime, default=func.now(), nullable=False),
)
project2ownercandidate = Table(
    "project2ownercandidate",
    metadata,
    Column("name", String(50), primary_key=True),
    Column("region", String, primary_key=True),
    Column("candidate_id", String),
    Column("created_date", DateTime, default=func.now(), nullable=False),
)
project2external = Table(
    "project2external",
    metadata,
    Column("name", String(50), primary_key=True),
    Column("region", String, primary_key=True),
    Column("e_mail", String(320), primary_key=True),
    Column("is_admin", Boolean, default=False, nullable=False),
    Column("created_date", DateTime, default=func.now(), nullable=False),
)
certificate2user = Table(
    "certificate2user",
    metadata,
    Column("region", String, primary_key=True),
    Column("user_id", String, primary_key=True),
    Column("certificate_no", Integer, nullable=False),
    Column("created_date", DateTime, default=func.now(), nullable=False),
)

# databases query builder
database = Database(DATABASE_URL)


Base: DeclarativeMeta = declarative_base()

Base.metadata.create_all(engine)
