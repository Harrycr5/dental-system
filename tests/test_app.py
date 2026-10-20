from fastapi import APIRouter
from pydantic import BaseModel

from app.core.errors import NotFoundError
from app.core.logging import redact
from app.main import create_app


def test_health_endpoints(client):
    assert client.get("/health").json() == {"status": "ok"}
    body = client.get("/api/v1/health").json()
    assert body["status"] == "ok" and body["timezone"] == "America/Lima"


def test_request_id_generated_and_safe_echo(client):
    assert client.get("/health").headers["X-Request-ID"]
    assert client.get("/health", headers={"X-Request-ID": "abc-123"}).headers["X-Request-ID"] == "abc-123"
    bad = client.get("/health", headers={"X-Request-ID": "bad id\t!"}).headers["X-Request-ID"]
    assert bad != "bad id\t!"


def test_error_format(settings):
    from fastapi.testclient import TestClient

    app = create_app(settings)
    r = APIRouter()

    class Body(BaseModel):
        n: int

    @r.get("/_nf")
    def nf():
        raise NotFoundError("Paciente no encontrado")

    @r.get("/_boom")
    def boom():
        raise RuntimeError("secreto interno")

    @r.post("/_val")
    def val(b: Body):
        return b

    app.include_router(r)
    c = TestClient(app, raise_server_exceptions=False)

    e = c.get("/_nf")
    assert e.status_code == 404 and e.json()["error"]["code"] == "not_found"

    v = c.post("/_val", json={"n": "hola-secreto"})
    assert v.status_code == 422
    assert "hola-secreto" not in v.text

    b = c.get("/_boom")
    assert b.status_code == 500 and "secreto interno" not in b.text


def test_log_redaction():
    out = redact({"password": "x", "nested": {"access_token": "y", "ok": 1}})
    assert out == {"password": "***", "nested": {"access_token": "***", "ok": 1}}
