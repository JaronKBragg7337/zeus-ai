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
VALID_REVIEW_LABELS = {"success", "failed", "user_corrected", "bug", "unsafe", "unclear", "other"}


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
        _append_candidate_example(
            instruction=f"Use Zeus tool `{name}` with these parameters: {json.dumps(_redact(parameters), ensure_ascii=False)}",
            ideal_output=f"Tool `{name}` completed successfully. Result summary: {json.dumps(_summarize_result(result), ensure_ascii=False)}",
            source="tool_call",
            status="success",
            metadata={"tool": name},
        )
    else:
        _append_candidate_example(
            instruction=f"Use Zeus tool `{name}` with these parameters: {json.dumps(_redact(parameters), ensure_ascii=False)}",
            ideal_output=f"Tool `{name}` did not complete successfully. Result summary: {json.dumps(_summarize_result(result), ensure_ascii=False)}",
            source="tool_call",
            status="failed",
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

    _append_candidate_example(
        instruction=task,
        ideal_output=final_message,
        source="agent_completion",
        status="success" if status == "success" else "failed",
        metadata={"project_path": project_path, "steps": steps, "agent_status": status},
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
    _append_candidate_example(
        instruction=last_user.get("content", ""),
        ideal_output=response,
        source="chat_completion",
        status="success",
        metadata={"model": model, "tools_enabled": tools_enabled, "rag_enabled": rag_enabled},
    )

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
    _append_candidate_example(
        instruction=record["original_user"] or "Improve the prior Zeus response using the user's correction.",
        ideal_output=f"User correction: {record['correction']}",
        source="user_correction",
        status="user_corrected",
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
    candidate = _append_candidate_example(
        instruction=original,
        ideal_output=correction,
        source="explicit_correction",
        status="user_corrected",
        metadata={"context": _truncate(context, 1000)},
    )
    return {"captured": True, "trace_id": record["id"], "candidate_id": candidate["id"]}


def list_candidate_examples(limit: int = 100) -> List[Dict[str, Any]]:
    if not is_training_capture_enabled():
        return []

    candidates = _read_jsonl(_path("instruction_examples", "candidates.jsonl"))
    reviewed_ids = {
        record.get("candidate_id")
        for record in _read_jsonl(_path("instruction_examples", "reviews.jsonl"))
        if record.get("candidate_id")
    }
    pending = [record for record in candidates if record.get("id") not in reviewed_ids]
    bounded_limit = max(0, min(limit, 500))
    if bounded_limit == 0:
        return []
    return pending[-bounded_limit:]


def review_candidate_example(candidate_id: str, approved: bool, *, reviewer: str = "user",
                             notes: str = "", label: Optional[str] = None) -> Dict[str, Any]:
    if not is_training_capture_enabled():
        return {"reviewed": False, "reason": "training capture disabled"}

    candidates = _read_jsonl(_path("instruction_examples", "candidates.jsonl"))
    candidate = next((record for record in candidates if record.get("id") == candidate_id), None)
    if not candidate:
        return {"reviewed": False, "reason": "candidate not found", "candidate_id": candidate_id}

    normalized_label = _normalize_label(label or candidate.get("status") or "other")
    review = _entry({
        "type": "training_review",
        "candidate_id": candidate_id,
        "approved": approved,
        "reviewer": _truncate(reviewer or "user", 200),
        "notes": _truncate(notes, 2000),
        "label": normalized_label,
    })
    _append_jsonl(_path("instruction_examples", "reviews.jsonl"), review)

    reviewed_candidate = {
        **candidate,
        "review_status": "approved" if approved else "rejected",
        "review_id": review["id"],
        "review_label": normalized_label,
        "review_notes": review["notes"],
    }
    if approved:
        _append_jsonl(_path("instruction_examples", "approved.jsonl"), reviewed_candidate)
    else:
        _append_jsonl(_path("instruction_examples", "rejected.jsonl"), reviewed_candidate)

    return {
        "reviewed": True,
        "approved": approved,
        "candidate_id": candidate_id,
        "review_id": review["id"],
        "label": normalized_label,
    }


def _append_candidate_example(instruction: str, ideal_output: str, *, source: str, status: str,
                              metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    text = (
        "<|system|>\n"
        "You are Zeus-Tiny. Learn from this reviewed local Zeus usage example.\n"
        "<|user|>\n"
        f"{_truncate(instruction, MAX_TEXT_CHARS)}\n"
        "<|assistant|>\n"
        f"{_truncate(ideal_output, MAX_TEXT_CHARS)}"
    )
    record = _entry({
        "type": "candidate_instruction_example",
        "source": source,
        "status": _normalize_label(status),
        "review_status": "pending",
        "instruction": _truncate(instruction, MAX_TEXT_CHARS),
        "ideal_output": _truncate(ideal_output, MAX_TEXT_CHARS),
        "text": text,
        "metadata": _redact(metadata or {}),
    })
    _append_jsonl(_path("instruction_examples", "candidates.jsonl"), record)
    return record


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


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            records.append(data)
    return records


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


def _normalize_label(label: str) -> str:
    normalized = str(label or "other").lower().strip().replace(" ", "_")
    return normalized if normalized in VALID_REVIEW_LABELS else "other"


def _truncate(text: Any, limit: int) -> str:
    value = str(text)
    return value if len(value) <= limit else value[:limit] + "...[truncated]"
