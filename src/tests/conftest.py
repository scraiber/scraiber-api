import pytest
import psycopg2
from typing import Generator
from fastapi.testclient import TestClient

from app.main import app



@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c



@pytest.fixture(scope='function')
def session():
    conn = psycopg2.connect("postgresql://test_user:mypass@psql-postgresql.postgresql.svc.cluster.local:5432/scraiber_db")
    # Create a cursor object
    session = conn.cursor()
    yield session
    # Close the cursor and connection to so the server can allocate
    # bandwidth to other requests
    session.close()
    conn.close()