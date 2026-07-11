"""Inspectable, local-first long-term memory for Zeus.

Memories are deliberately user-managed facts, decisions, preferences, and
project notes. They are not silently extracted from every chat or tool trace.
"""
from __future__ import annotations

import json
import re
import sqlite3
import time
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

from config import get_memory_db_path


MEMORY_CATEGORIES = {"fact", "preference", "decision", "project", "instruction", "note"}
MAX_MEMORY_CHARS = 4_000


def list_memories(query: str = "", category: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 500))
    with _connection() as conn:
        rows = conn.execute(
            """SELECT id, content, category, source, tags_json, created_at, updated_at, last_used_at
               FROM memories
               WHERE (? = '' OR lower(content) LIKE '%' || lower(?) || '%' OR lower(tags_json) LIKE '%' || lower(?) || '%')
                 AND (? = '' OR category = ?)
               ORDER BY updated_at DESC
               LIMIT ?""",
            (query.strip(), query.strip(), query.strip(), category or "", category or "", limit),
        ).fetchall()
    return [_row_to_memory(row) for row in rows]


def save_memory(
    content: str,
    *,
    category: str = "note",
    source: str = "manual",
    tags: list[str] | None = None,
    memory_id: str | None = None,
) -> dict[str, Any]:
    content = " ".join(content.split())
    if not content:
        raise ValueError("Memory content is required.")
    if len(content) > MAX_MEMORY_CHARS:
        raise ValueError(f"Memory content must be at most {MAX_MEMORY_CHARS} characters.")
    if category not in MEMORY_CATEGORIES:
        raise ValueError(f"Memory category must be one of: {', '.join(sorted(MEMORY_CATEGORIES))}.")

    identifier = memory_id or uuid.uuid4().hex
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", identifier):
        raise ValueError("Invalid memory id.")
    normalized_tags = _normalise_tags(tags or [])
    now = _timestamp()

    with _connection() as conn:
        existing = conn.execute("SELECT created_at FROM memories WHERE id = ?", (identifier,)).fetchone()
        conn.execute(
            """INSERT INTO memories (id, content, category, source, tags_json, created_at, updated_at, last_used_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
               ON CONFLICT(id) DO UPDATE SET
                 content = excluded.content,
                 category = excluded.category,
                 source = excluded.source,
                 tags_json = excluded.tags_json,
                 updated_at = excluded.updated_at""",
            (identifier, content, category, source.strip()[:160] or "manual", json.dumps(normalized_tags), existing[0] if existing else now, now),
        )
        row = conn.execute(
            "SELECT id, content, category, source, tags_json, created_at, updated_at, last_used_at FROM memories WHERE id = ?",
            (identifier,),
        ).fetchone()
    return _row_to_memory(row)


def delete_memory(memory_id: str) -> bool:
    with _connection() as conn:
        result = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    return result.rowcount > 0


def search_memories(query: str, limit: int = 6) -> list[dict[str, Any]]:
    query = query.strip()
    if not query:
        return []
    with _connection() as conn:
        rows = conn.execute(
            "SELECT id, content, category, source, tags_json, created_at, updated_at, last_used_at FROM memories"
        ).fetchall()

    scored = []
    for row in rows:
        memory = _row_to_memory(row)
        score = _cosine_score(query, f"{memory['content']} {' '.join(memory['tags'])} {memory['category']}")
        if score > 0:
            memory["score"] = round(score, 6)
            scored.append(memory)
    scored.sort(key=lambda item: (item["score"], item["updated_at"]), reverse=True)
    matches = scored[:max(1, min(limit, 25))]
    if matches:
        with _connection() as conn:
            conn.executemany("UPDATE memories SET last_used_at = ? WHERE id = ?", [(_timestamp(), item["id"]) for item in matches])
    return matches


def memory_context(query: str, limit: int = 6, max_chars: int = 3_500) -> str:
    lines = []
    remaining = max_chars
    for memory in search_memories(query, limit):
        line = f"[{memory['category']} | {memory['source']}] {memory['content']}"
        if len(line) > remaining:
            line = line[:remaining].rsplit(" ", 1)[0] + "..."
        lines.append(line)
        remaining -= len(line) + 1
        if remaining <= 80:
            break
    return "\n".join(lines)


def memory_status() -> dict[str, Any]:
    path = get_memory_db_path()
    with _connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    return {"storage": "local_sqlite", "path": str(path), "memory_count": count, "categories": sorted(MEMORY_CATEGORIES)}


def _connection() -> sqlite3.Connection:
    path = get_memory_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            category TEXT NOT NULL,
            source TEXT NOT NULL,
            tags_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_used_at TEXT
        )"""
    )
    conn.execute("CREATE INDEX IF NOT EXISTS memories_updated_idx ON memories(updated_at DESC)")
    return conn


def _row_to_memory(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "content": row["content"],
        "category": row["category"],
        "source": row["source"],
        "tags": json.loads(row["tags_json"] or "[]"),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "last_used_at": row["last_used_at"],
    }


def _normalise_tags(tags: list[str]) -> list[str]:
    values = []
    for tag in tags:
        compact = " ".join(str(tag).split()).lower()[:48]
        if compact and compact not in values:
            values.append(compact)
    return values[:12]


def _cosine_score(left: str, right: str) -> float:
    left_counts = Counter(re.findall(r"[a-zA-Z0-9_]+", left.lower()))
    right_counts = Counter(re.findall(r"[a-zA-Z0-9_]+", right.lower()))
    if not left_counts or not right_counts:
        return 0.0
    shared = set(left_counts) & set(right_counts)
    dot = sum(left_counts[token] * right_counts[token] for token in shared)
    left_norm = sum(value * value for value in left_counts.values()) ** 0.5
    right_norm = sum(value * value for value in right_counts.values()) ** 0.5
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


def _timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
