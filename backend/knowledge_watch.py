"""Local polling watcher that keeps Zeus Knowledge indexed as files change."""
from __future__ import annotations

import asyncio
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from audit_log import append_action
from config import (
    get_data_dir,
    get_knowledge_watch_interval_seconds,
    is_knowledge_watch_enabled_by_default,
)
from knowledge_index import _iter_source_files, build_knowledge_index, knowledge_status


class KnowledgeWatchService:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._running = False
        self._state: dict[str, Any] = {}
        self._load_state()

    async def start(self) -> None:
        self._load_state()
        if not self._state["enabled"] or self._task:
            return
        self._task = asyncio.create_task(self._loop(), name="zeus-knowledge-watch")

    async def stop(self) -> None:
        if not self._task:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    def status(self) -> dict[str, Any]:
        self._load_state()
        return {
            **self._state,
            "running": self._running,
            "scheduler_active": self._task is not None and not self._task.done(),
        }

    async def configure(self, *, enabled: bool | None = None, interval_seconds: int | None = None) -> dict[str, Any]:
        self._load_state()
        if enabled is not None:
            self._state["enabled"] = bool(enabled)
        if interval_seconds is not None:
            self._state["interval_seconds"] = max(5, min(int(interval_seconds), 3600))
        self._save_state()
        await self.stop()
        if self._state["enabled"]:
            await self.start()
        append_action({"type": "knowledge_watch", "action": "configure", "enabled": self._state["enabled"], "interval_seconds": self._state["interval_seconds"]})
        return self.status()

    async def run_once(self, reason: str = "manual") -> dict[str, Any]:
        async with self._lock:
            self._running = True
            checked_at = _timestamp()
            try:
                signature, source_file_count = await asyncio.to_thread(_source_signature)
                changed = signature != self._state.get("source_signature")
                result: dict[str, Any] = {
                    "checked_at": checked_at,
                    "reason": reason,
                    "changed": changed,
                    "source_file_count": source_file_count,
                    "indexed": False,
                }
                if changed:
                    index = await asyncio.to_thread(build_knowledge_index)
                    result["indexed"] = True
                    result["knowledge_index"] = index
                    self._state["last_indexed_at"] = checked_at
                    self._state["rebuild_count"] = int(self._state.get("rebuild_count", 0)) + 1
                    append_action({
                        "type": "knowledge_watch",
                        "action": "rebuild_index",
                        "reason": reason,
                        "source_file_count": source_file_count,
                        "chunks": index.get("chunks", 0),
                    })
                self._state.update({
                    "source_signature": signature,
                    "last_checked_at": checked_at,
                    "last_error": None,
                })
                self._save_state()
                return result
            except OSError as error:
                self._state.update({"last_checked_at": checked_at, "last_error": str(error)})
                self._save_state()
                raise
            finally:
                self._running = False

    async def _loop(self) -> None:
        try:
            await self.run_once("startup")
            while True:
                await asyncio.sleep(int(self._state["interval_seconds"]))
                if self._state["enabled"]:
                    await self.run_once("timer")
        except asyncio.CancelledError:
            raise

    def _state_path(self) -> Path:
        return get_data_dir() / "knowledge-watch" / "state.json"

    def _load_state(self) -> None:
        defaults = {
            "enabled": is_knowledge_watch_enabled_by_default(),
            "interval_seconds": get_knowledge_watch_interval_seconds(),
            "last_checked_at": None,
            "last_indexed_at": None,
            "last_error": None,
            "rebuild_count": 0,
            "source_signature": None,
        }
        try:
            saved = json.loads(self._state_path().read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            saved = {}
        self._state = {**defaults, **{key: value for key, value in saved.items() if key in defaults}}

    def _save_state(self) -> None:
        path = self._state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._state, indent=2), encoding="utf-8")


def _source_signature() -> tuple[str, int]:
    records = []
    for path in _iter_source_files(knowledge_status_root()):
        stat = path.stat()
        records.append((str(path), stat.st_mtime_ns, stat.st_size))
    encoded = json.dumps(records, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest(), len(records)


def knowledge_status_root() -> Path:
    # Import lazily through the existing status contract to respect runtime overrides.
    return Path(knowledge_status()["knowledge_root"])


def _timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


knowledge_watch = KnowledgeWatchService()
