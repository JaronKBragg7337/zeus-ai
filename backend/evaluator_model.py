"""Zeus Evaluator v1 runtime.

Evaluator v1 is a small local scorer that predicts whether a candidate example
should be learned from. It is intentionally simple: hashed lexical features plus
a trained linear model saved as JSON.
"""
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from config import get_evaluator_model_dir


DEFAULT_FEATURE_SIZE = 2048
TOKEN_RE = re.compile(r"[a-zA-Z0-9_:\\./\\\\-]+|[^\s]", re.UNICODE)


def score_candidate_example(candidate: Dict[str, Any], model_dir: Optional[Path] = None) -> Dict[str, Any]:
    model = load_evaluator_model(model_dir)
    text = candidate_to_evaluator_text(candidate)
    if not model:
        return {
            "available": False,
            "score": None,
            "decision": "unknown",
            "reason": "Zeus Evaluator v1 has not been trained yet.",
            "model_path": str(_model_path(model_dir)),
        }

    score = predict_score(text, model)
    decision = decision_from_score(score)
    return {
        "available": True,
        "score": round(score, 6),
        "decision": decision,
        "reason": reason_from_score(score, decision),
        "model_path": str(_model_path(model_dir)),
        "model_type": model.get("type", "unknown"),
        "candidate_id": candidate.get("id"),
    }


def load_evaluator_model(model_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    path = _model_path(model_dir)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if data.get("type") != "zeus-evaluator-linear-v1":
        return None
    return data


def predict_score(text: str, model: Dict[str, Any]) -> float:
    feature_size = int(model.get("feature_size", DEFAULT_FEATURE_SIZE))
    weights = [float(value) for value in model.get("weights", [])]
    if len(weights) != feature_size:
        return 0.0

    bias = float(model.get("bias", 0.0))
    features = hashed_features(text, feature_size)
    logit = bias + sum(weights[index] * value for index, value in features.items())
    return sigmoid(logit)


def candidate_to_evaluator_text(candidate: Dict[str, Any]) -> str:
    instruction = candidate.get("instruction") or ""
    output = candidate.get("ideal_output") or candidate.get("output") or candidate.get("response") or ""
    source = candidate.get("source") or "unknown"
    status = candidate.get("status") or "unknown"
    metadata = candidate.get("metadata") or {}
    return (
        f"Source: {source}\n"
        f"Status: {status}\n"
        f"Metadata: {json.dumps(metadata, ensure_ascii=False, sort_keys=True)}\n"
        f"Instruction:\n{instruction}\n\n"
        f"Output:\n{output}"
    )


def hashed_features(text: str, feature_size: int = DEFAULT_FEATURE_SIZE) -> Dict[int, float]:
    counts: Dict[int, float] = {}
    tokens = list(tokenize(text))
    if not tokens:
        return counts
    for token in tokens:
        index = stable_hash(token) % feature_size
        counts[index] = counts.get(index, 0.0) + 1.0

    norm = math.sqrt(sum(value * value for value in counts.values())) or 1.0
    return {index: value / norm for index, value in counts.items()}


def tokenize(text: str) -> Iterable[str]:
    for token in TOKEN_RE.findall(text.lower()):
        yield token


def stable_hash(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def decision_from_score(score: float) -> str:
    if score >= 0.67:
        return "approve"
    if score <= 0.33:
        return "reject"
    return "revise"


def reason_from_score(score: float, decision: str) -> str:
    if decision == "approve":
        return "Evaluator v1 predicts this candidate is likely useful for behavior training."
    if decision == "reject":
        return "Evaluator v1 predicts this candidate should not be learned from as-is."
    return "Evaluator v1 predicts this candidate needs human review or revision before training."


def _model_path(model_dir: Optional[Path] = None) -> Path:
    base = Path(model_dir) if model_dir else get_evaluator_model_dir()
    return base / "evaluator.json"
