"""Authentication blueprint: signup, login, logout, session check, profile updates."""

import re
import sqlite3
from functools import wraps

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LEN = 8


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required", "status": "error"}), 401
        return view(*args, **kwargs)

    return wrapped


def _user_row_to_dict(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "name": row["name"], "email": row["email"]}


def _get_user_by_id(conn: sqlite3.Connection, user_id: int):
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name:
        return jsonify({"error": "Name is required", "status": "error"}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "A valid email is required", "status": "error"}), 400
    if len(password) < MIN_PASSWORD_LEN:
        return jsonify({"error": f"Password must be at least {MIN_PASSWORD_LEN} characters", "status": "error"}), 400

    conn = get_db()
    try:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            return jsonify({"error": "An account with this email already exists", "status": "error"}), 409

        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        conn.commit()
        user = _get_user_by_id(conn, cursor.lastrowid)
        session["user_id"] = user["id"]
        return jsonify({"user": _user_row_to_dict(user), "status": "success"}), 201
    finally:
        conn.close()


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    conn = get_db()
    try:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Invalid email or password", "status": "error"}), 401

        session["user_id"] = user["id"]
        return jsonify({"user": _user_row_to_dict(user), "status": "success"}), 200
    finally:
        conn.close()


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "success"}), 200


@auth_bp.route("/me", methods=["GET"])
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated", "status": "error"}), 401

    conn = get_db()
    try:
        user = _get_user_by_id(conn, user_id)
        if not user:
            session.clear()
            return jsonify({"error": "Not authenticated", "status": "error"}), 401
        return jsonify({"user": _user_row_to_dict(user), "status": "success"}), 200
    finally:
        conn.close()


@auth_bp.route("/profile", methods=["PATCH"])
@login_required
def update_profile():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Name is required", "status": "error"}), 400

    conn = get_db()
    try:
        conn.execute("UPDATE users SET name = ? WHERE id = ?", (name, session["user_id"]))
        conn.commit()
        user = _get_user_by_id(conn, session["user_id"])
        return jsonify({"user": _user_row_to_dict(user), "status": "success"}), 200
    finally:
        conn.close()


def _reauthenticate(conn: sqlite3.Connection, user_id: int, current_password: str):
    user = _get_user_by_id(conn, user_id)
    if not user or not check_password_hash(user["password_hash"], current_password or ""):
        return None
    return user


@auth_bp.route("/email", methods=["PATCH"])
@login_required
def update_email():
    data = request.get_json(silent=True) or {}
    new_email = (data.get("newEmail") or "").strip().lower()
    current_password = data.get("currentPassword") or ""

    if not EMAIL_RE.match(new_email):
        return jsonify({"error": "A valid email is required", "status": "error"}), 400

    conn = get_db()
    try:
        if not _reauthenticate(conn, session["user_id"], current_password):
            return jsonify({"error": "Current password is incorrect", "status": "error"}), 401

        existing = conn.execute(
            "SELECT id FROM users WHERE email = ? AND id != ?", (new_email, session["user_id"])
        ).fetchone()
        if existing:
            return jsonify({"error": "An account with this email already exists", "status": "error"}), 409

        conn.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, session["user_id"]))
        conn.commit()
        user = _get_user_by_id(conn, session["user_id"])
        return jsonify({"user": _user_row_to_dict(user), "status": "success"}), 200
    finally:
        conn.close()


@auth_bp.route("/password", methods=["PATCH"])
@login_required
def update_password():
    data = request.get_json(silent=True) or {}
    new_password = data.get("newPassword") or ""
    current_password = data.get("currentPassword") or ""

    if len(new_password) < MIN_PASSWORD_LEN:
        return jsonify({"error": f"Password must be at least {MIN_PASSWORD_LEN} characters", "status": "error"}), 400

    conn = get_db()
    try:
        if not _reauthenticate(conn, session["user_id"], current_password):
            return jsonify({"error": "Current password is incorrect", "status": "error"}), 401

        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (generate_password_hash(new_password), session["user_id"]),
        )
        conn.commit()
        return jsonify({"status": "success"}), 200
    finally:
        conn.close()
