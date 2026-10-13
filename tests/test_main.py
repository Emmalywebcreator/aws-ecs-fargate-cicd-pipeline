from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_welcome_message():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from FastAPI on ECS Fargate"}


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_defaults_to_dev(monkeypatch):
    monkeypatch.delenv("APP_VERSION", raising=False)
    response = client.get("/version")
    assert response.json() == {"version": "dev"}


def test_version_reads_app_version_env_var(monkeypatch):
    monkeypatch.setenv("APP_VERSION", "abc123")
    response = client.get("/version")
    assert response.json() == {"version": "abc123"}



def test_unknown_path_returns_404():
    response = client.get("/nope")
    assert response.status_code == 404
