from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session,sessionmaker

from w1_lab.api import app,get_db
from w1_lab.db import Base

GOOD_LINE = "2026-11-10T09:00:00 10.0.0.1 GET /api/users 200 1234 45.2"

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

    app.dependency_overrides[get_db]=override_get_db  # 用override_get_db代替
    yield TestClient(app)
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