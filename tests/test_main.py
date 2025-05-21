from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}

def test_about():
    response = client.get("/about")
    assert response.status_code == 200
    assert response.json() == {"message": "This is the about page."}

def test_add_msg():
    response = client.post("/messages/test_message/")
    assert response.status_code == 200
    assert "msg_id" in response.json()["message"]

def test_message_items():
    response = client.get("/messages")
    assert response.status_code == 200
    assert "messages:" in response.json()