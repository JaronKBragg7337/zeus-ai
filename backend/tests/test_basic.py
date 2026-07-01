import sys
from pathlib import Path
import asyncio
import json

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import app
from agent import run_agent_task
from tools import execute_tool
from prompts import build_zeus_system_prompt
from zeus_native_client import ZeusNativeClient
from config import get_data_dir


@pytest.fixture(autouse=True)
def isolate_training_capture(tmp_path, monkeypatch):
    monkeypatch.setenv("ZEUSAI_DATA_DIR", str(tmp_path / "zeus-data"))


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


def test_desktop_data_dir_uses_local_app_data(tmp_path, monkeypatch):
    monkeypatch.delenv("ZEUSAI_DATA_DIR", raising=False)
    monkeypatch.setenv("ZEUSAI_DESKTOP", "1")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert get_data_dir() == tmp_path / "Zeus AI" / "data"


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


def test_tool_execution_captures_training_examples(tmp_path, monkeypatch):
    data_dir = tmp_path / "training-data"
    monkeypatch.setenv("ZEUSAI_DATA_DIR", str(data_dir))

    result = execute_tool("calculate", {"expression": "3 + 5"})

    assert result["result"] == "8"
    tool_trace = data_dir / "tool_traces" / "tool_calls.jsonl"
    candidates = data_dir / "instruction_examples" / "candidates.jsonl"
    assert tool_trace.exists()
    assert candidates.exists()
    assert '"tool": "calculate"' in tool_trace.read_text(encoding="utf-8")
    candidate_text = candidates.read_text(encoding="utf-8")
    assert "Use Zeus tool `calculate`" in candidate_text
    assert '"review_status": "pending"' in candidate_text


def test_training_candidate_review_approves_example(tmp_path, monkeypatch):
    data_dir = tmp_path / "training-data"
    monkeypatch.setenv("ZEUSAI_DATA_DIR", str(data_dir))

    execute_tool("calculate", {"expression": "10 - 3"})
    with TestClient(app) as client:
        candidates = client.get("/api/training/candidates").json()["candidates"]
        response = client.post(
            "/api/training/review",
            json={
                "candidate_id": candidates[-1]["id"],
                "approved": True,
                "reviewer": "pytest",
                "label": "success",
                "notes": "Good arithmetic tool example.",
            },
        )

    assert response.status_code == 200
    assert response.json()["approved"] is True
    approved = data_dir / "instruction_examples" / "approved.jsonl"
    reviews = data_dir / "instruction_examples" / "reviews.jsonl"
    assert approved.exists()
    assert reviews.exists()
    assert "10 - 3" in approved.read_text(encoding="utf-8")
    assert "Good arithmetic tool example" in reviews.read_text(encoding="utf-8")


def test_training_correction_endpoint_captures_instruction_example(tmp_path, monkeypatch):
    data_dir = tmp_path / "training-data"
    monkeypatch.setenv("ZEUSAI_DATA_DIR", str(data_dir))

    with TestClient(app) as client:
        response = client.post(
            "/api/training/correction",
            json={
                "original": "Zeus should expose Qwen as the main identity.",
                "correction": "Zeus should treat Qwen only as temporary infrastructure.",
                "context": "identity correction",
            },
        )

    assert response.status_code == 200
    assert response.json()["captured"] is True
    assert response.json()["candidate_id"]
    correction_log = data_dir / "tool_traces" / "user_corrections.jsonl"
    candidates = data_dir / "instruction_examples" / "candidates.jsonl"
    assert correction_log.exists()
    assert candidates.exists()
    assert "temporary infrastructure" in candidates.read_text(encoding="utf-8")
    assert '"status": "user_corrected"' in candidates.read_text(encoding="utf-8")
