import sys
import os
from pathlib import Path
import asyncio
import json

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import app
from agent import run_agent_task, _assistant_tool_message, _extract_native_tool_call
from tools import execute_tool
from tools import get_tool_definitions
from prompts import build_zeus_system_prompt
from zeus_native_client import ZeusNativeClient
from config import get_data_dir, get_evaluator_model_dir, get_knowledge_dir
from conversation_store import get_conversation, list_conversations, save_conversation
from memory_store import delete_memory, memory_context, memory_status, save_memory, search_memories


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


def test_full_computer_mode_registers_desktop_tools(monkeypatch):
    monkeypatch.setenv("ZEUSAI_FULL_COMPUTER_ACCESS", "1")

    names = {tool["function"]["name"] for tool in get_tool_definitions()}

    assert {"get_screen_info", "list_windows", "capture_screen", "click_mouse", "press_keys"} <= names


def test_conversations_persist_and_can_be_loaded(tmp_path, monkeypatch):
    monkeypatch.setenv("ZEUSAI_DATA_DIR", str(tmp_path / "zeus-data"))

    saved = save_conversation(None, None, [
        {"role": "user", "content": "Remember this project", "timestamp": "2026-07-11T12:00:00Z"},
        {"role": "assistant", "content": "I will.", "timestamp": "2026-07-11T12:00:01Z"},
    ])

    assert get_conversation(saved["id"])["messages"][0]["content"] == "Remember this project"
    assert list_conversations()[0]["title"] == "Remember this project"


def test_memory_is_local_searchable_and_deletable(tmp_path, monkeypatch):
    monkeypatch.setenv("ZEUSAI_DATA_DIR", str(tmp_path / "zeus-data"))
    saved = save_memory(
        "Jaron prefers Zeus to keep an inspectable project memory.",
        category="preference",
        tags=["memory", "zeus"],
    )

    assert memory_status()["storage"] == "local_sqlite"
    assert search_memories("inspectable project")[0]["id"] == saved["id"]
    assert "Jaron prefers" in memory_context("project memory")
    assert delete_memory(saved["id"]) is True


def test_chat_endpoint_accepts_memory_toggle():
    with TestClient(app) as client:
        response = client.post(
            "/api/memory",
            json={"content": "The memory toggle should remain user-controlled.", "category": "instruction"},
        )

    assert response.status_code == 200


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


@pytest.mark.skipif(os.name != "nt", reason="Packaged desktop app-data paths are Windows-specific.")
def test_desktop_data_dir_uses_local_app_data(tmp_path, monkeypatch):
    monkeypatch.delenv("ZEUSAI_DATA_DIR", raising=False)
    monkeypatch.setenv("ZEUSAI_DESKTOP", "1")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert get_data_dir() == tmp_path / "Zeus AI" / "data"


@pytest.mark.skipif(os.name != "nt", reason="Packaged desktop app-data paths are Windows-specific.")
def test_desktop_knowledge_dir_uses_local_app_data(tmp_path, monkeypatch):
    monkeypatch.delenv("ZEUSAI_KNOWLEDGE_DIR", raising=False)
    monkeypatch.setenv("ZEUSAI_DESKTOP", "1")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert get_knowledge_dir() == tmp_path / "Zeus AI" / "knowledge"


@pytest.mark.skipif(os.name != "nt", reason="Packaged desktop app-data paths are Windows-specific.")
def test_desktop_evaluator_model_dir_uses_local_app_data(tmp_path, monkeypatch):
    monkeypatch.delenv("ZEUSAI_EVALUATOR_MODEL_DIR", raising=False)
    monkeypatch.setenv("ZEUSAI_DESKTOP", "1")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert get_evaluator_model_dir() == tmp_path / "Zeus AI" / "models" / "zeus-evaluator-v1"


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


def test_knowledge_index_builds_and_searches(tmp_path, monkeypatch):
    knowledge_root = tmp_path / "knowledge"
    manual_dir = knowledge_root / "manuals"
    manual_dir.mkdir(parents=True)
    (manual_dir / "zeus-manual.md").write_text(
        "Zeus Knowledge fact: approved examples should train behavior, while manuals should feed retrieval.",
        encoding="utf-8",
    )
    monkeypatch.setenv("ZEUSAI_KNOWLEDGE_DIR", str(knowledge_root))

    with TestClient(app) as client:
        status_before = client.get("/api/knowledge/status")
        built = client.post("/api/knowledge/index")
        search = client.post("/api/knowledge/search", json={"query": "What should manuals feed?", "top_k": 3})

    assert status_before.status_code == 200
    assert status_before.json()["source_file_count"] == 1
    assert built.status_code == 200
    assert built.json()["files_indexed"] == 1
    assert built.json()["chunks"] == 1
    assert search.status_code == 200
    assert "manuals should feed retrieval" in search.json()["context"]


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


def test_extract_native_tool_call_reads_ollama_tool_calls():
    message = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {"id": "call_1", "function": {"name": "calculate", "arguments": {"expression": "17*23"}}}
        ],
    }

    call = _extract_native_tool_call(message)

    assert call == {"name": "calculate", "parameters": {"expression": "17*23"}}


def test_extract_native_tool_call_parses_string_arguments():
    message = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {"function": {"name": "list_files", "arguments": "{\"path\": \".\"}"}}
        ],
    }

    call = _extract_native_tool_call(message)

    assert call == {"name": "list_files", "parameters": {"path": "."}}


def test_extract_native_tool_call_handles_missing_tool_calls():
    assert _extract_native_tool_call({"role": "assistant", "content": "done"}) is None


def test_agent_preserves_native_tool_call_envelope():
    message = {
        "role": "assistant",
        "content": "",
        "thinking": "Need a tool.",
        "tool_calls": [{"function": {"name": "list_windows", "arguments": {}}}],
    }

    assistant = _assistant_tool_message(message)

    assert assistant["role"] == "assistant"
    assert assistant["tool_calls"] == message["tool_calls"]
    assert assistant["thinking"] == "Need a tool."


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


def test_training_evaluate_scores_candidate_with_local_evaluator(tmp_path, monkeypatch):
    data_dir = tmp_path / "training-data"
    model_dir = tmp_path / "evaluator-model"
    monkeypatch.setenv("ZEUSAI_DATA_DIR", str(data_dir))
    monkeypatch.setenv("ZEUSAI_EVALUATOR_MODEL_DIR", str(model_dir))
    model_dir.mkdir(parents=True)
    (model_dir / "evaluator.json").write_text(
        json.dumps({
            "type": "zeus-evaluator-linear-v1",
            "feature_size": 8,
            "weights": [0.0] * 8,
            "bias": 2.2,
        }),
        encoding="utf-8",
    )

    execute_tool("calculate", {"expression": "6 * 7"})
    with TestClient(app) as client:
        candidates = client.get("/api/training/candidates").json()["candidates"]
        response = client.post("/api/training/evaluate", json={"candidate_id": candidates[-1]["id"]})

    assert response.status_code == 200
    assert response.json()["available"] is True
    assert response.json()["decision"] == "approve"
    assert response.json()["score"] > 0.67


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
