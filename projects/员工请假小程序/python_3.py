from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_leave_request():
    response = client.post("/requests/", json={"employee_id": 1, "reason": "Sick leave", "start_date": "2023-11-01T10:00:00", "end_date": "2023-11-05T10:00:00"})
    assert response.status_code == 200
    assert response.json()["reason"] == "Sick leave"

def test_read_leave_request():
    response = client.get("/requests/1")
    assert response.status_code == 200
