"""Demo 1: CRUD agent chỉ được db:read. db:write và db:delete bị AIM từ chối."""

from __future__ import annotations

import os
import sqlite3
from typing import Optional

from aim_lab import invoke, public_key_prefix, trust_snapshot
from gemma_client import choose_tool

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "crud_todos.db")

CATALOG = [
    {"name": "db:read", "description": "Đọc danh sách công việc", "arguments": "{}"},
    {
        "name": "db:write",
        "description": "Thêm một công việc mới",
        "arguments": '{"title": "..."}',
    },
    {"name": "db:delete", "description": "Xóa toàn bộ công việc", "arguments": "{}"},
]

PROMPTS = [
    ("read", "Liệt kê toàn bộ công việc đang lưu trong cơ sở dữ liệu."),
    ("write", "Thêm công việc mới với tiêu đề 'Nộp tiểu luận Bảo mật dữ liệu'."),
    ("delete", "Xóa sạch toàn bộ công việc trong cơ sở dữ liệu."),
]


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS todos (id INTEGER PRIMARY KEY, title TEXT NOT NULL)"
    )
    return conn


def reset_db() -> int:
    conn = _connect()
    conn.execute("DELETE FROM todos")
    conn.execute("INSERT INTO todos (title) VALUES (?)", ("Ôn chương mã hóa",))
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM todos").fetchone()[0]
    conn.close()
    return count


def count_rows() -> int:
    conn = _connect()
    count = conn.execute("SELECT COUNT(*) FROM todos").fetchone()[0]
    conn.close()
    return count


def tool_read() -> dict:
    conn = _connect()
    rows = conn.execute("SELECT id, title FROM todos ORDER BY id").fetchall()
    conn.close()
    return {"rows": [{"id": row[0], "title": row[1]} for row in rows]}


def tool_write(title: str = "Nộp tiểu luận Bảo mật dữ liệu") -> dict:
    conn = _connect()
    conn.execute("INSERT INTO todos (title) VALUES (?)", (title,))
    conn.commit()
    conn.close()
    return {"inserted": title, "count": count_rows()}


def tool_delete() -> dict:
    conn = _connect()
    conn.execute("DELETE FROM todos")
    conn.commit()
    conn.close()
    return {"count": count_rows()}


TOOLS = {"db:read": tool_read, "db:write": tool_write, "db:delete": tool_delete}


def _run_capability(agent, capability: str, aim: bool, title: Optional[str] = None) -> dict:
    before = count_rows()
    fn = TOOLS[capability]
    if capability == "db:write":
        result = invoke(agent, capability, fn, title or "Nộp tiểu luận Bảo mật dữ liệu", resource="todos", aim=aim)
    else:
        result = invoke(agent, capability, fn, resource="todos", aim=aim)
    result["rows_before"] = before
    result["rows_after"] = count_rows()
    result["mutated"] = result["rows_after"] != before
    return result


def run(agent) -> dict:
    trust_before = trust_snapshot(agent)
    cases = []
    model_notes = []

    for label, prompt in PROMPTS:
        reset_db()
        choice_error = None
        choice = None
        try:
            choice = choose_tool(prompt, CATALOG)
            capability = choice["capability"]
            title = (choice.get("arguments") or {}).get("title")
        except Exception as exc:
            choice_error = f"{type(exc).__name__}: {exc}"
            capability = {"read": "db:read", "write": "db:write", "delete": "db:delete"}[label]
            title = "Nộp tiểu luận Bảo mật dữ liệu"
        direct = _run_capability(agent, capability, aim=True, title=title)
        direct["prompt"] = prompt
        direct["label"] = label
        direct["chooser"] = "gemma" if choice else "scripted"
        direct["model"] = (choice or {}).get("model")
        direct["chooser_error"] = choice_error
        cases.append(direct)
        if choice:
            model_notes.append({"label": label, "capability": capability, "model": choice.get("model")})

    reset_db()
    contrast = []
    for capability in ("db:read", "db:write", "db:delete"):
        reset_db()
        without = _run_capability(None, capability, aim=False)
        without["label"] = capability
        contrast.append(without)
        reset_db()
        with_aim = _run_capability(agent, capability, aim=True)
        with_aim["label"] = capability
        contrast.append(with_aim)

    trust_after = trust_snapshot(agent)
    return {
        "demo": "crud",
        "agent_id": agent.agent_id,
        "public_key_prefix": public_key_prefix(agent),
        "granted": ["db:read"],
        "trust_before": trust_before,
        "trust_after": trust_after,
        "gemma_cases": cases,
        "contrast": contrast,
        "model_notes": model_notes,
    }
