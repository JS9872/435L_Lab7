"""Lab 5 user management REST API."""

import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

FIELDS = ("name", "email", "phone", "address", "country")
DB_PATH = Path(os.environ.get("LAB5_DB_PATH", Path(__file__).with_name("database.db")))


def connect_to_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_db_table():
    with connect_to_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                country TEXT NOT NULL
            )
        """)


def get_users():
    with connect_to_db() as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM users ORDER BY user_id")]


def get_user_by_id(user_id):
    with connect_to_db() as connection:
        row = connection.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def insert_user(user):
    with connect_to_db() as connection:
        cursor = connection.execute(
            "INSERT INTO users (name, email, phone, address, country) VALUES (?, ?, ?, ?, ?)",
            tuple(user[field] for field in FIELDS),
        )
        user_id = cursor.lastrowid
    return get_user_by_id(user_id)


def update_user(user):
    with connect_to_db() as connection:
        cursor = connection.execute(
            "UPDATE users SET name = ?, email = ?, phone = ?, address = ?, country = ? WHERE user_id = ?",
            (*[user[field] for field in FIELDS], user["user_id"]),
        )
        if cursor.rowcount == 0:
            return None
    return get_user_by_id(user["user_id"])


def delete_user(user_id):
    with connect_to_db() as connection:
        cursor = connection.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        return cursor.rowcount > 0


def validate_user(data, updating=False):
    if not isinstance(data, dict):
        return "Request body must be a JSON object"
    for field in FIELDS:
        if not isinstance(data.get(field), str) or not data[field].strip():
            return f"{field} must be a nonempty string"
    if updating and (not isinstance(data.get("user_id"), int) or isinstance(data["user_id"], bool) or data["user_id"] < 1):
        return "user_id must be a positive integer"
    return None


app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
create_db_table()


@app.get("/api/users")
def api_get_users():
    return jsonify(get_users())


@app.get("/api/users/<int:user_id>")
def api_get_user(user_id):
    user = get_user_by_id(user_id)
    return (jsonify(user), 200) if user else (jsonify(error="User not found"), 404)


@app.post("/api/users/add")
def api_add_user():
    user = request.get_json(silent=True)
    error = validate_user(user)
    if error:
        return jsonify(error=error), 400
    return jsonify(insert_user(user)), 201


@app.put("/api/users/update")
def api_update_user():
    user = request.get_json(silent=True)
    error = validate_user(user, updating=True)
    if error:
        return jsonify(error=error), 400
    updated = update_user(user)
    return (jsonify(updated), 200) if updated else (jsonify(error="User not found"), 404)


@app.delete("/api/users/delete/<int:user_id>")
def api_delete_user(user_id):
    if not delete_user(user_id):
        return jsonify(error="User not found"), 404
    return jsonify(status="User deleted successfully")


if __name__ == "__main__":
    app.run()
