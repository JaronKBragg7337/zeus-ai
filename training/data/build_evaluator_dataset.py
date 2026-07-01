"""Build local Zeus evaluator/scoring data.

The evaluator lane is separate from behavior training. Approved examples teach
what good looks like; rejected, failed, and corrected examples teach what Zeus
should flag or revise.
"""
import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", default=None)
    parser.add_argument("--include-pending-failures", action="store_true", help="Include pending failed/user-corrected candidates.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output = Path(args.output) if args.output else repo_root / "data" / "processed" / "zeus_evaluator.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)

    records: List[Dict[str, Any]] = []
    records.extend(_seed_records(repo_root / "data" / "evaluator_examples" / "seed.jsonl"))
    records.extend(_reviewed_records(repo_root / "data" / "instruction_examples" / "approved.jsonl", approved=True))
    records.extend(_reviewed_records(repo_root / "data" / "instruction_examples" / "rejected.jsonl", approved=False))
    records.extend(_correction_records(repo_root / "data" / "tool_traces" / "user_corrections.jsonl"))
    if args.include_pending_failures:
        records.extend(_pending_failure_records(repo_root / "data" / "instruction_examples" / "candidates.jsonl"))

    with output.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} evaluator records to {output}")


def _seed_records(path: Path) -> Iterable[Dict[str, Any]]:
    for data in _read_jsonl(path):
        yield _format_record(
            instruction=data.get("instruction", ""),
            output=data.get("output", ""),
            decision=data.get("decision", "other"),
            score=float(data.get("score", 0.0)),
            reason=data.get("reason", ""),
            source=str(path),
        )


def _reviewed_records(path: Path, *, approved: bool) -> Iterable[Dict[str, Any]]:
    for data in _read_jsonl(path):
        decision = "approve" if approved else "reject"
        score = 1.0 if approved else 0.0
        label = data.get("review_label") or data.get("status") or "other"
        reason = data.get("review_notes") or f"Reviewed as {label}."
        yield _format_record(
            instruction=data.get("instruction", ""),
            output=data.get("ideal_output", ""),
            decision=decision,
            score=score,
            reason=reason,
            source=str(path),
            metadata={"candidate_id": data.get("id"), "label": label, "source": data.get("source")},
        )


def _correction_records(path: Path) -> Iterable[Dict[str, Any]]:
    for data in _read_jsonl(path):
        if data.get("type") not in {"user_correction", "explicit_correction"}:
            continue
        instruction = data.get("original_user") or data.get("original") or "Evaluate the prior Zeus response."
        output = data.get("previous_assistant") or data.get("original") or ""
        correction = data.get("correction", "")
        yield _format_record(
            instruction=instruction,
            output=output,
            decision="revise",
            score=0.25,
            reason=f"User correction: {correction}",
            source=str(path),
            metadata={"trace_id": data.get("id"), "context": data.get("context", "")},
        )


def _pending_failure_records(path: Path) -> Iterable[Dict[str, Any]]:
    for data in _read_jsonl(path):
        status = data.get("status")
        if status not in {"failed", "user_corrected"}:
            continue
        decision = "revise" if status == "user_corrected" else "reject"
        score = 0.25 if status == "user_corrected" else 0.0
        yield _format_record(
            instruction=data.get("instruction", ""),
            output=data.get("ideal_output", ""),
            decision=decision,
            score=score,
            reason=f"Pending candidate marked {status}.",
            source=str(path),
            metadata={"candidate_id": data.get("id"), "status": status, "source": data.get("source")},
        )


def _format_record(instruction: str, output: str, decision: str, score: float, reason: str,
                   source: str, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
    bounded_score = max(0.0, min(1.0, score))
    text = (
        "<|system|>\n"
        "You are Zeus-Evaluator. Score whether this Zeus example should be used, rejected, or revised.\n"
        "<|user|>\n"
        f"Instruction:\n{instruction}\n\nOutput:\n{output}\n"
        "<|assistant|>\n"
        f"Decision: {decision}\nScore: {bounded_score:.2f}\nReason: {reason}"
    )
    return {
        "text": text,
        "decision": decision,
        "score": bounded_score,
        "reason": reason,
        "source": source,
        "metadata": metadata or {},
    }


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


if __name__ == "__main__":
    main()
