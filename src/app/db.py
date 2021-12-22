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
from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.dialects.postgresql import UUID

import uuid

from databases import Database

from app.api.models.users import User, UserDB


DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy
engine = create_engine(DATABASE_URL)
metadata = MetaData()
notes = Table(
    "notes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String(50)),
    Column("description", String(50)),
    Column("created_date", DateTime, default=func.now(), nullable=False),
)
projects = Table(
    "projects",
    metadata,
    Column("name", String(50), primary_key=True),
    Column("region", String, primary_key=True),
    Column("limits_cpu", Float),
    Column("limits_mem", Float),
    Column("owner_id", UUID),
    Column("created_date", DateTime, default=func.now(), nullable=False),
)
project2user = Table(
    "project2user",
    metadata,
    Column("name", String(50), primary_key=True),
    Column("region", String, primary_key=True),
    Column("user_id", UUID, primary_key=True),
    Column("is_admin", Boolean, default=False, nullable=False),
    Column("created_date", DateTime, default=func.now(), nullable=False),
)
project2ownercandidate = Table(
    "project2ownercandidate",
    metadata,
    Column("name", String(50), primary_key=True),
    Column("region", String, primary_key=True),
    Column("candidate_id", UUID, primary_key=True),
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


# databases query builder
database = Database(DATABASE_URL)


Base: DeclarativeMeta = declarative_base()

class UserTable(Base, SQLAlchemyBaseUserTable):
    pass

Base.metadata.create_all(engine)

users = UserTable.__table__

async def get_user_db():
    yield SQLAlchemyUserDatabase(UserDB, database, users)
