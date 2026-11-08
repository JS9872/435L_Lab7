"""Lab 7 tests for the Lab 5 user database and Flask API."""

import sqlite3
import os
import subprocess
import sys
from pathlib import Path

import pytest

import app as user_app


@pytest.fixture
def isolated_app(tmp_path, monkeypatch):
    """Give every test a newly created database without touching the local one."""
    db_path = tmp_path / "users.db"
    monkeypatch.setattr(user_app, "DB_PATH", db_path)
    user_app.create_db_table()
    user_app.app.config.update(TESTING=True)
    yield user_app
    user_app.app.config.update(TESTING=False)


@pytest.fixture
def client(isolated_app):
    return isolated_app.app.test_client()


@pytest.fixture
def sample_user():
    return {
        "name": "John Doe",
        "email": "jondoe@gmail.com",
        "phone": "067765434567",
        "address": "John Doe Street, Innsbruck",
        "country": "Austria",
    }


def test_database_created_on_first_run(tmp_path, monkeypatch):
    db_path = tmp_path / "first_run.db"
    assert not db_path.exists()
    env = {**os.environ, "LAB5_DB_PATH": str(db_path)}
    subprocess.run(
        [sys.executable, "-c", "import app"],
        cwd=Path(__file__).parent,
        env=env,
        check=True,
    )
    assert db_path.is_file()
    with sqlite3.connect(db_path) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(users)")]
    assert columns == ["user_id", "name", "email", "phone", "address", "country"]
    monkeypatch.setattr(user_app, "DB_PATH", db_path)
    assert user_app.get_users() == []
    user_app.create_db_table()


def test_insert_user(isolated_app, sample_user):
    inserted = isolated_app.insert_user(sample_user)
    assert inserted["user_id"] == 1
    assert {key: inserted[key] for key in sample_user} == sample_user
    assert isolated_app.get_user_by_id(1) == inserted


def test_get_users(isolated_app, sample_user):
    first = isolated_app.insert_user(sample_user)
    second = isolated_app.insert_user({**sample_user, "name": "Jane Doe"})
    assert isolated_app.get_users() == [first, second]


def test_get_user_by_id(isolated_app, sample_user):
    inserted = isolated_app.insert_user(sample_user)
    assert isolated_app.get_user_by_id(inserted["user_id"]) == inserted
    assert isolated_app.get_user_by_id(999) is None


def test_update_user(isolated_app, sample_user):
    inserted = isolated_app.insert_user(sample_user)
    updated = {**inserted, "name": "Jane Doe", "country": "Germany"}
    assert isolated_app.update_user(updated) == updated
    assert isolated_app.get_user_by_id(inserted["user_id"]) == updated
    assert isolated_app.update_user({**updated, "user_id": 999}) is None


def test_delete_user(isolated_app, sample_user):
    inserted = isolated_app.insert_user(sample_user)
    assert isolated_app.delete_user(inserted["user_id"]) is True
    assert isolated_app.get_users() == []
    assert isolated_app.delete_user(inserted["user_id"]) is False


def test_api_get_users(client, isolated_app, sample_user):
    inserted = isolated_app.insert_user(sample_user)
    response = client.get("/api/users")
    assert response.status_code == 200
    assert response.get_json() == [inserted]


def test_api_get_user(client, isolated_app, sample_user):
    inserted = isolated_app.insert_user(sample_user)
    response = client.get(f"/api/users/{inserted['user_id']}")
    assert response.status_code == 200
    assert response.get_json() == inserted
    missing = client.get("/api/users/999")
    assert missing.status_code == 404
    assert missing.get_json() == {"error": "User not found"}


def test_api_add_user(client, isolated_app, sample_user):
    response = client.post("/api/users/add", json=sample_user)
    assert response.status_code == 201
    assert response.get_json() == {"user_id": 1, **sample_user}
    assert isolated_app.get_users() == [response.get_json()]
    invalid = client.post("/api/users/add", json={"name": "Incomplete"})
    assert invalid.status_code == 400
    assert "error" in invalid.get_json()
    assert len(isolated_app.get_users()) == 1


def test_api_update_user(client, isolated_app, sample_user):
    inserted = isolated_app.insert_user(sample_user)
    updated = {**inserted, "name": "Jane Doe"}
    response = client.put("/api/users/update", json=updated)
    assert response.status_code == 200
    assert response.get_json() == updated
    assert isolated_app.get_user_by_id(inserted["user_id"]) == updated
    missing = client.put("/api/users/update", json={**updated, "user_id": 999})
    assert missing.status_code == 404
    assert missing.get_json() == {"error": "User not found"}
    invalid = client.put("/api/users/update", json={**updated, "user_id": "bad"})
    assert invalid.status_code == 400


def test_api_delete_user(client, isolated_app, sample_user):
    inserted = isolated_app.insert_user(sample_user)
    url = f"/api/users/delete/{inserted['user_id']}"
    response = client.delete(url)
    assert response.status_code == 200
    assert response.get_json() == {"status": "User deleted successfully"}
    assert isolated_app.get_user_by_id(inserted["user_id"]) is None
    missing = client.delete(url)
    assert missing.status_code == 404
    assert missing.get_json() == {"error": "User not found"}
