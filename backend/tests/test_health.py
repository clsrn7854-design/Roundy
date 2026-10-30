"""/health 테스트. 실제 DB 대신 가짜 연결 객체를 넣는다."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


class FakeConnections:
    def __init__(self, failing: set[str] | None = None):
        self.failing = failing or set()

    async def _probe(self, name: str) -> None:
        if name in self.failing:
            raise ConnectionError(name)

    async def check_postgres(self) -> None:
        await self._probe("postgres")

    async def check_neo4j(self) -> None:
        await self._probe("neo4j")

    async def check_redis(self) -> None:
        await self._probe("redis")


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_all_ok(client):
    client.app.state.connections = FakeConnections()

    res = client.get("/health")

    assert res.status_code == 200
    assert res.json() == {
        "status": "ok",
        "services": {"postgres": "ok", "neo4j": "ok", "redis": "ok"},
    }


def test_health_reports_failed_service(client):
    client.app.state.connections = FakeConnections(failing={"neo4j"})

    body = client.get("/health").json()

    assert body["status"] == "degraded"
    assert body["services"]["neo4j"] == "error: ConnectionError"
    assert body["services"]["postgres"] == "ok"
