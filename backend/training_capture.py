"""Local training-example capture for Zeus-Tiny.

The capture path is intentionally append-only JSONL and local. Generated files
are ignored by Git so real user traces do not get published accidentally.
"""
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import get_data_dir, is_training_capture_enabled


MAX_TEXT_CHARS = 6000
MAX_RESULT_CHARS = 4000
SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "password",
    "secret",
    "token",
}
CORRECTION_MARKERS = (
    "correction:",
    "actually",
    "that's wrong",
    "that is wrong",
    "no,",
    "no ",
    "not what i meant",
    "you misunderstood",
    "fix that",
)


def capture_tool_call(name: str, parameters: Dict[str, Any], result: Dict[str, Any], status: str) -> None:
    if not is_training_capture_enabled():
        return

    trace = {
        "type": "tool_call",
        "tool": name,
        "parameters": _redact(parameters),
        "status": status,
        "result": _summarize_result(result),
    }
    _append_jsonl(_path("tool_traces", "tool_calls.jsonl"), _entry(trace))

    if status == "ok":
        _append_instruction_example(
            instruction=f"Use Zeus tool `{name}` with these parameters: {json.dumps(_redact(parameters), ensure_ascii=False)}",
            ideal_output=f"Tool `{name}` completed successfully. Result summary: {json.dumps(_summarize_result(result), ensure_ascii=False)}",
            source="tool_call",
            metadata={"tool": name},
        )


def capture_agent_completion(task: str, final_message: str, *, project_path: Optional[str], steps: int,
                             status: str = "success", tool_events: Optional[List[Dict[str, Any]]] = None) -> None:
    if not is_training_capture_enabled():
        return

    trace = {
        "type": "agent_run",
        "task": _truncate(task, MAX_TEXT_CHARS),
        "project_path": project_path,
        "steps": steps,
        "status": status,
        "tool_events": _redact(tool_events or []),
        "final_message": _truncate(final_message, MAX_TEXT_CHARS),
    }
    _append_jsonl(_path("tool_traces", "agent_runs.jsonl"), _entry(trace))

    if status == "success":
        _append_instruction_example(
            instruction=task,
            ideal_output=final_message,
            source="agent_completion",
            metadata={"project_path": project_path, "steps": steps},
        )


def capture_chat_completion(messages: List[Dict[str, Any]], response: str, *, model: str,
                            tools_enabled: bool, rag_enabled: bool) -> None:
    if not is_training_capture_enabled() or not response.strip():
        return

    last_user = _last_message(messages, "user")
    if not last_user:
        return

    _append_jsonl(_path("tool_traces", "chat_completions.jsonl"), _entry({
        "type": "chat_completion",
        "model": model,
        "tools_enabled": tools_enabled,
        "rag_enabled": rag_enabled,
        "instruction": _truncate(last_user.get("content", ""), MAX_TEXT_CHARS),
        "response": _truncate(response, MAX_TEXT_CHARS),
    }))

    capture_user_correction_if_present(messages)


def capture_user_correction_if_present(messages: List[Dict[str, Any]]) -> bool:
    if not is_training_capture_enabled() or len(messages) < 2:
        return False

    last = messages[-1]
    if last.get("role") != "user":
        return False

    correction = str(last.get("content", ""))
    if not _looks_like_correction(correction):
        return False

    previous_assistant = None
    original_user = None
    for message in reversed(messages[:-1]):
        if previous_assistant is None and message.get("role") == "assistant":
            previous_assistant = message
            continue
        if previous_assistant is not None and message.get("role") == "user":
            original_user = message
            break

    record = {
        "type": "user_correction",
        "original_user": _truncate((original_user or {}).get("content", ""), MAX_TEXT_CHARS),
        "previous_assistant": _truncate((previous_assistant or {}).get("content", ""), MAX_TEXT_CHARS),
        "correction": _truncate(correction, MAX_TEXT_CHARS),
    }
    _append_jsonl(_path("tool_traces", "user_corrections.jsonl"), _entry(record))
    _append_instruction_example(
        instruction=record["original_user"] or "Improve the prior Zeus response using the user's correction.",
        ideal_output=f"User correction: {record['correction']}",
        source="user_correction",
        metadata={"had_previous_assistant": bool(previous_assistant)},
    )
    return True


def capture_explicit_correction(original: str, correction: str, *, context: str = "") -> Dict[str, Any]:
    record = _entry({
        "type": "explicit_correction",
        "context": _truncate(context, MAX_TEXT_CHARS),
        "original": _truncate(original, MAX_TEXT_CHARS),
        "correction": _truncate(correction, MAX_TEXT_CHARS),
    })
    if not is_training_capture_enabled():
        return {"captured": False, "reason": "training capture disabled"}

    _append_jsonl(_path("tool_traces", "user_corrections.jsonl"), record)
    _append_instruction_example(
        instruction=original,
        ideal_output=correction,
        source="explicit_correction",
        metadata={"context": _truncate(context, 1000)},
    )
    return {"captured": True, "id": record["id"]}


def _append_instruction_example(instruction: str, ideal_output: str, *, source: str,
                                metadata: Optional[Dict[str, Any]] = None) -> None:
    text = (
        "<|system|>\n"
        "You are Zeus-Tiny. Learn from this local Zeus usage example.\n"
        "<|user|>\n"
        f"{_truncate(instruction, MAX_TEXT_CHARS)}\n"
        "<|assistant|>\n"
        f"{_truncate(ideal_output, MAX_TEXT_CHARS)}"
    )
    _append_jsonl(_path("instruction_examples", "generated_usage.jsonl"), _entry({
        "type": "instruction_example",
        "source": source,
        "text": text,
        "metadata": _redact(metadata or {}),
    }))


def _entry(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **payload,
    }


def _path(folder: str, filename: str) -> Path:
    return get_data_dir() / folder / filename


def _append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            normalized = key.lower().replace("-", "_")
            redacted[key] = "[REDACTED]" if normalized in SENSITIVE_KEYS else _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value[:50]]
    if isinstance(value, str):
        return _truncate(value, MAX_TEXT_CHARS)
    return value


def _summarize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    if "content" in result:
        return {**_redact(result), "content": f"[{len(result.get('content', ''))} chars]"}
    if "files" in result:
        return {**_redact(result), "files": _redact(result.get("files", [])[:20]), "file_count": len(result.get("files", []))}
    if "matches" in result:
        return {**_redact(result), "matches": _redact(result.get("matches", [])[:20]), "match_count": len(result.get("matches", []))}
    return _redact(result)


def _last_message(messages: List[Dict[str, Any]], role: str) -> Optional[Dict[str, Any]]:
    for message in reversed(messages):
        if message.get("role") == role:
            return message
    return None


def _looks_like_correction(text: str) -> bool:
    lower = text.lower().strip()
    return any(marker in lower for marker in CORRECTION_MARKERS)


def _truncate(text: Any, limit: int) -> str:
    value = str(text)
    return value if len(value) <= limit else value[:limit] + "...[truncated]"
