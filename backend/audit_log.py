"""Append-only local action audit log for Zeus AI."""
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

from config import get_action_log_path


MAX_FIELD_CHARS = 2000
SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "password",
    "secret",
    "token",
    "bot_token",
    "app_token",
    "access_token",
    "client_secret",
    "signing_secret",
}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            if key.lower().replace("-", "_") in SENSITIVE_KEYS:
                redacted[key] = "[REDACTED]"
            elif key == "content" and isinstance(item, str):
                redacted[key] = f"[{len(item)} chars]"
            else:
                redacted[key] = _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value[:100]]
    if isinstance(value, str) and len(value) > MAX_FIELD_CHARS:
        return value[:MAX_FIELD_CHARS] + "...[truncated]"
    return value


def append_action(event: Dict[str, Any]) -> Dict[str, Any]:
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **_redact(event),
    }
    path = get_action_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def read_recent_actions(limit: int = 100) -> List[Dict[str, Any]]:
    path = get_action_log_path()
    if not path.exists():
        return []

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    records = []
    for line in lines[-max(1, min(limit, 1000)):]:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records
