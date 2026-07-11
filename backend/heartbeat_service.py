"""Local, inspectable activity loop for Zeus while the backend is running."""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any

from audit_log import append_action
from config import (
    format_allowed_roots,
    get_data_dir,
    get_heartbeat_interval_seconds,
    is_full_computer_access_enabled,
    is_heartbeat_enabled_by_default,
)
from knowledge_index import knowledge_status
from memory_store import memory_status
from ollama_client import ollama
from tools import get_tool_definitions


class HeartbeatService:
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
        self._task = asyncio.create_task(self._loop(), name="zeus-heartbeat")

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
            "workspace": str(self._root()),
        }

    async def configure(self, *, enabled: bool | None = None, interval_seconds: int | None = None) -> dict[str, Any]:
        self._load_state()
        if enabled is not None:
            self._state["enabled"] = bool(enabled)
        if interval_seconds is not None:
            self._state["interval_seconds"] = max(60, min(int(interval_seconds), 86_400))
        self._save_state()
        await self.stop()
        if self._state["enabled"]:
            await self.start()
        append_action({"type": "heartbeat", "action": "configure", "enabled": self._state["enabled"], "interval_seconds": self._state["interval_seconds"]})
        return self.status()

    async def run_once(self, reason: str = "manual") -> dict[str, Any]:
        async with self._lock:
            self._running = True
            started = _timestamp()
            root = self._root()
            for name in ("observations", "tasks", "reports"):
                (root / name).mkdir(parents=True, exist_ok=True)

            try:
                model_names = await _model_names()
                observation = {
                    "id": f"heartbeat-{int(time.time())}",
                    "observed_at": started,
                    "reason": reason,
                    "capabilities": {
                        "models": model_names,
                        "tool_count": len(get_tool_definitions()),
                        "full_computer_access": is_full_computer_access_enabled(),
                        "allowed_roots": format_allowed_roots(),
                    },
                    "memory": memory_status(),
                    "knowledge": knowledge_status(),
                }
                tasks = _curiosity_tasks(observation)
                observation["curiosity_tasks"] = tasks
                stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
                (root / "observations" / f"{stamp}.json").write_text(json.dumps(observation, indent=2), encoding="utf-8")
                (root / "tasks" / f"{stamp}.json").write_text(json.dumps({"created_at": started, "tasks": tasks}, indent=2), encoding="utf-8")

                self._state.update({
                    "last_run_at": started,
                    "last_reason": reason,
                    "last_observation_id": observation["id"],
                    "last_task_count": len(tasks),
                    "run_count": int(self._state.get("run_count", 0)) + 1,
                })
                self._save_state()
                append_action({
                    "type": "heartbeat",
                    "action": "observe",
                    "reason": reason,
                    "models": model_names,
                    "tool_count": observation["capabilities"]["tool_count"],
                    "task_count": len(tasks),
                })
                return observation
            finally:
                self._running = False

    def activity(self, limit: int = 20) -> list[dict[str, Any]]:
        paths = sorted((self._root() / "observations").glob("*.json"), reverse=True)[:max(1, min(limit, 100))]
        records = []
        for path in paths:
            try:
                records.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
        return records

    async def _loop(self) -> None:
        try:
            await self.run_once("startup")
            while True:
                await asyncio.sleep(int(self._state["interval_seconds"]))
                if self._state["enabled"]:
                    await self.run_once("timer")
        except asyncio.CancelledError:
            raise

    def _root(self) -> Path:
        return get_data_dir() / "heartbeat"

    def _state_path(self) -> Path:
        return self._root() / "state.json"

    def _load_state(self) -> None:
        defaults = {
            "enabled": is_heartbeat_enabled_by_default(),
            "interval_seconds": get_heartbeat_interval_seconds(),
            "last_run_at": None,
            "last_reason": None,
            "last_observation_id": None,
            "last_task_count": 0,
            "run_count": 0,
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


async def _model_names() -> list[str]:
    try:
        return [str(model.get("name", "unknown")) for model in await ollama.list_models()]
    except Exception:
        return []


def _curiosity_tasks(observation: dict[str, Any]) -> list[dict[str, str]]:
    tasks = []
    capabilities = observation["capabilities"]
    knowledge = observation["knowledge"]
    memory = observation["memory"]
    if not capabilities["models"]:
        tasks.append({"kind": "runtime", "task": "No local model was observed. Start Ollama and install a tool-capable model."})
    else:
        tasks.append({"kind": "runtime", "task": "Review the available local models and run a focused capability test for the next task."})
    if not knowledge["indexed"] or not knowledge["source_file_count"]:
        tasks.append({"kind": "knowledge", "task": "Choose local manuals, project docs, or research to add to Zeus Knowledge, then rebuild the index."})
    if not memory["memory_count"]:
        tasks.append({"kind": "memory", "task": "Add an inspectable preference, decision, or active project note to Zeus Memory."})
    if capabilities["full_computer_access"]:
        tasks.append({"kind": "desktop", "task": "Inspect the current desktop task context before taking actions; save screenshots only when a reviewable artifact is useful."})
    tasks.append({"kind": "sources", "task": "Check the source-adapter queue and select one evidence source to normalize with provenance."})
    return tasks


def _timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


heartbeat = HeartbeatService()
