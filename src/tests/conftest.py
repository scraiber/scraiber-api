import pytest
import psycopg2
import os
"""
from app.api.models.projects import ProjectPrimaryKey, ProjectSchemaDB, Project2OwnerCandidateDB
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from databases import Database


engine = create_engine('postgresql://hello_fastapi:hello_fastapi@db/hello_fastapi_dev')
Session = sessionmaker()

@pytest.fixture(scope='module')
def connection():
    connection = engine.connect()
    yield connection
    connection.close()

@pytest.fixture(scope='function')
def session(connection):
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
"""
db_host = os.environ['DB_HOST']

@pytest.fixture(scope='function')
def session():
    conn = psycopg2.connect(host=db_host, database="hello_fastapi_dev", user="hello_fastapi", password="hello_fastapi")
    # Create a cursor object
    session = conn.cursor()
    yield session
    # Close the cursor and connection to so the server can allocate
    # bandwidth to other requests
    session.close()
    conn.close()

"""
@pytest.fixture(scope='function')
def session():
    DATABASE_URL='postgresql://hello_fastapi:hello_fastapi@db/hello_fastapi_dev'
    database = Database(DATABASE_URL)
    database.connect()
    yield database
    database.disconnect()
"""