from fastapi.testclient import TestClient


def test_generate_config_after_two_projects_generated(client: TestClient, monkeypatch):
    test_request_payload = {"email": "tobias.ahsendorf@gmail.com"}

    async def mock_test_mail(email):
        return f"This works, {email}"

    monkeypatch.setattr("app.api.routes.ping.write_test_mail", mock_test_mail)
    
    response = client.get('/ping2/', params=test_request_payload)
    assert response.status_code == 200
    assert response.json()["ping"] == "pong2!"

