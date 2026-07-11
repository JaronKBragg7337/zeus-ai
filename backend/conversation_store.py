"""Local persistent conversation storage for the Zeus chat workspace."""
from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

from config import get_data_dir


_CONVERSATION_ID = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")


def list_conversations(limit: int = 200) -> list[dict[str, Any]]:
    records = []
    for path in _conversations_dir().glob("*.json"):
        record = _read(path)
        if not record:
            continue
        records.append({
            "id": record["id"],
            "title": record["title"],
            "created_at": record["created_at"],
            "updated_at": record["updated_at"],
            "message_count": len(record.get("messages", [])),
        })
    records.sort(key=lambda item: item["updated_at"], reverse=True)
    return records[:max(1, min(limit, 500))]


def get_conversation(conversation_id: str) -> dict[str, Any] | None:
    return _read(_conversation_path(conversation_id))


def save_conversation(
    conversation_id: str | None,
    title: str | None,
    messages: list[dict[str, Any]],
) -> dict[str, Any]:
    identifier = conversation_id or uuid.uuid4().hex
    path = _conversation_path(identifier)
    current = _read(path) or {}
    now = _timestamp()
    normalized_messages = [
        {
            "role": str(message.get("role", "assistant")),
            "content": str(message.get("content", "")),
            "timestamp": str(message.get("timestamp", now)),
        }
        for message in messages[-1000:]
    ]
    record = {
        "id": identifier,
        "title": _title(title or current.get("title") or _infer_title(normalized_messages)),
        "created_at": current.get("created_at", now),
        "updated_at": now,
        "messages": normalized_messages,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def _conversations_dir() -> Path:
    return get_data_dir() / "conversations"


def _conversation_path(conversation_id: str) -> Path:
    if not _CONVERSATION_ID.fullmatch(conversation_id or ""):
        raise ValueError("Invalid conversation id")
    return _conversations_dir() / f"{conversation_id}.json"


def _read(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return record if isinstance(record, dict) and record.get("id") else None


def _infer_title(messages: list[dict[str, Any]]) -> str:
    for message in messages:
        if message["role"] == "user" and message["content"].strip():
            return _title(message["content"])
    return "New conversation"


def _title(value: str) -> str:
    compact = " ".join(value.split())
    return (compact[:72] + "...") if len(compact) > 75 else (compact or "New conversation")


def _timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
