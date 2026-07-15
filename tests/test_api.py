from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """The health endpoint should confirm the server is running."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_home_page_loads():
    """The home page should load successfully."""
    response = client.get("/")
    assert response.status_code == 200

def test_extract_rejects_unsupported_file_type():
    """Uploading a disallowed file type should return a 400 error."""
    response = client.post(
        "/extract",
        files={"file": ("test.txt", b"hello world", "text/plain")}
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]

def test_extract_rejects_empty_file():
    """Uploading an empty file should return a 400 error."""
    response = client.post(
        "/extract",
        files={"file": ("empty.png", b"", "image/png")}
    )
    assert response.status_code == 400