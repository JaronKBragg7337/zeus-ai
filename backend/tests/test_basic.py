import sys
from pathlib import Path
import asyncio
import json

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import app
from agent import run_agent_task
from tools import execute_tool
from prompts import build_zeus_system_prompt
from zeus_native_client import ZeusNativeClient


def test_health_endpoint_reports_allowed_roots():
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["allowed_roots"]
    assert "shell_enabled" in data
    assert "native_model_enabled" in data


def test_zeus_prompt_names_local_capabilities():
    prompt = build_zeus_system_prompt(tools_enabled=True, rag_enabled=True)

    assert "You are Zeus AI" in prompt
    assert "not a generic hosted chatbot" in prompt
    assert "Do not say you cannot access this computer in blanket terms" in prompt
    assert "local tools" in prompt


def test_native_client_reports_untrained_model(tmp_path, monkeypatch):
    monkeypatch.setenv("ZEUSAI_NATIVE_MODEL_DIR", str(tmp_path / "missing-zeus-tiny"))
    client = ZeusNativeClient()

    async def generate():
        return await client.generate("hello")

    result = asyncio.run(generate())

    assert "Zeus native mode is enabled" in result
    assert "Zeus-Tiny has not been trained yet" in result


def test_file_listing_defaults_to_project_root():
    with TestClient(app) as client:
        response = client.post("/api/files/list", json={"path": "."})

    assert response.status_code == 200
    names = {item["name"] for item in response.json()["files"]}
    assert "backend" in names
    assert "frontend" in names


def test_file_listing_blocks_paths_outside_allowed_roots():
    outside = "C:\\Users" if sys.platform.startswith("win") else "/"
    with TestClient(app) as client:
        response = client.post("/api/files/list", json={"path": outside})

    assert response.status_code == 400
    assert "outside allowed roots" in response.json()["detail"]


def test_local_rag_ingest_and_query():
    with TestClient(app) as client:
        files = {"file": ("smoke.txt", b"Zeus AI smoke fact: the verification code is local-only.", "text/plain")}
        upload = client.post("/api/rag/upload", data={"collection": "pytest_smoke"}, files=files)
        query = client.post(
            "/api/rag/query",
            json={"question": "What is the verification code?", "collection": "pytest_smoke", "top_k": 3},
        )

    assert upload.status_code == 200
    assert upload.json()["status"] in {"success", "already_exists"}
    assert query.status_code == 200
    assert "local-only" in query.json()["context"]


def test_agent_lists_files_without_shell_or_llm_wait():
    async def collect():
        updates = []
        async for update in run_agent_task("List files in the project path.", project_path=".", max_steps=2):
            updates.append(update)
        return updates

    updates = asyncio.run(collect())

    assert any(update["type"] == "tool_call" and update["name"] == "list_files" for update in updates)
    assert updates[-1]["type"] == "complete"
    assert "backend" in updates[-1]["message"]


def test_kill_switch_blocks_tool_execution():
    with TestClient(app) as client:
        killed = client.post("/api/control/kill", params={"reason": "pytest"})
        result = client.post(
            "/api/tools/execute",
            json={"name": "calculate", "parameters": {"expression": "1 + 1"}},
        )
        resumed = client.post("/api/control/resume")

    assert killed.status_code == 200
    assert result.status_code == 200
    assert "Emergency stop" in result.json()["error"]
    assert resumed.json()["stopped"] is False


def test_tool_execution_writes_audit_log(tmp_path, monkeypatch):
    log_path = tmp_path / "actions.jsonl"
    monkeypatch.setenv("ZEUSAI_ACTION_LOG", str(log_path))

    result = execute_tool("calculate", {"expression": "2 + 2"})

    assert result["result"] == "4"
    entries = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert entries[-1]["type"] == "tool"
    assert entries[-1]["name"] == "calculate"
    assert entries[-1]["status"] == "ok"
