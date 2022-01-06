from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


from app.api.models.users import UserDB
from app.fastapiusers import current_user, current_active_user


def test_ping():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"ping": "pong!"}

test_user = UserDB(email="test@email.com", hashed_password="aaa")
app.dependency_overrides[current_user] = lambda: test_user

def test_protected():
    #test_app.dependency_overrides[current_user] = lambda: test_user
    response = client.get("/protected-route")
    assert response.status_code == 200
    assert response.json() == 'Hello, test@email.com'