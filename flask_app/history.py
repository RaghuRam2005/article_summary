"""History blueprint: per-user CRUD for past summarize queries."""

from flask import Blueprint, jsonify, request, session

from auth import login_required
from db import get_db

history_bp = Blueprint("history", __name__, url_prefix="/history")

VALID_TYPES = {"keyword", "url", "content"}


def _row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "query": row["query"],
        "type": row["type"],
        "response": row["response"],
        "timestamp": row["timestamp"],
    }


@history_bp.route("", methods=["GET"])
@login_required
def list_history():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM history WHERE user_id = ? ORDER BY timestamp DESC",
            (session["user_id"],),
        ).fetchall()
        return jsonify({"history": [_row_to_dict(r) for r in rows], "status": "success"}), 200
    finally:
        conn.close()


@history_bp.route("", methods=["POST"])
@login_required
def create_history():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    item_type = data.get("type")
    response_text = data.get("response") or ""

    if not query:
        return jsonify({"error": "Query is required", "status": "error"}), 400
    if item_type not in VALID_TYPES:
        return jsonify({"error": f"Type must be one of {sorted(VALID_TYPES)}", "status": "error"}), 400

    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO history (user_id, query, type, response) VALUES (?, ?, ?, ?)",
            (session["user_id"], query, item_type, response_text),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM history WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return jsonify({"item": _row_to_dict(row), "status": "success"}), 201
    finally:
        conn.close()


@history_bp.route("/<int:item_id>", methods=["DELETE"])
@login_required
def delete_history(item_id: int):
    conn = get_db()
    try:
        cursor = conn.execute(
            "DELETE FROM history WHERE id = ? AND user_id = ?", (item_id, session["user_id"])
        )
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "History item not found", "status": "error"}), 404
        return jsonify({"status": "success"}), 200
    finally:
        conn.close()
