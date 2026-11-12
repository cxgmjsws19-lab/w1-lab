from collections.abc import Iterator
from pathlib import Path
from w1_lab import cache

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session,sessionmaker

from w1_lab.api import app,get_db
from w1_lab.db import Base

GOOD_LINE = "2026-11-10T09:00:00 10.0.0.1 GET /api/users 200 1234 45.2"

@pytest.fixture(autouse=True)
def _clear_cache() -> Iterator[None]:
    cache.clear()
    yield
    cache.clear()

@pytest.fixture
def client(tmp_path:Path) -> Iterator[TestClient]:
    engine=create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread":False},
    )
    Base.metadata.create_all(engine)
    TestSession=sessionmaker(bind=engine,expire_on_commit=False)

    def override_get_db()->Iterator[Session]:
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    test_client = TestClient(app)
    register = test_client.post(
        "/register", json={"username": "tester", "password": "pw123"}
    )
    test_client.headers["Authorization"] = (
        f"Bearer {register.json()['access_token']}"
    )

    yield test_client
    app.dependency_overrides.clear()

def test_health(client:TestClient)->None:
    response=client.get("/health")
    assert response.status_code==200
    assert response.json()=={"status":"ok"}

def test_create_entry_returns_201(client:TestClient)->None:
    response=client.post("/entries",json={"line":GOOD_LINE})
    assert response.status_code==201
    assert response.json()["status"]==200

def test_create_entry_rejects_bad_line(client:TestClient)->None:
    response =client.post("/entries",json={"line":"bad line"})
    assert response.status_code==422
    assert "期望" in response.json()["detail"]

def test_stats_starts_empty(client:TestClient)->None:
    assert client.get("/entries/stats").json()["total"]==0

def test_stats_counts_after_writes(client:TestClient)->None:
    client.post("/entries",json={"line":GOOD_LINE})
    client.post("/entries",json={"line":GOOD_LINE})
    assert client.get("/entries/stats").json()["total"]==2

def test_old_routes_are_gone(client:TestClient)->None:
    assert client.post("/parse",json={"line":GOOD_LINE}).status_code==404
    assert client.get("/stats").status_code==404

def test_entries_requires_token(client: TestClient) -> None:
    fresh = TestClient(app)
    response = fresh.post("/entries", json={"line": GOOD_LINE})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_stats_cache_hit(client: TestClient) -> None:
    first = client.get("/entries/stats")
    assert first.headers["x-cache"] == "MISS"
    second = client.get("/entries/stats")
    assert second.headers["x-cache"] == "HIT"


def test_write_invalidates_cache(client: TestClient) -> None:
    client.get("/entries/stats")
    assert client.get("/entries/stats").headers["x-cache"] == "HIT"

    client.post("/entries", json={"line": GOOD_LINE})

    assert client.get("/entries/stats").headers["x-cache"] == "MISS"