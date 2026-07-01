"""Score a candidate example with Zeus Evaluator v1."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from evaluator_model import score_candidate_example  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[2])
    parser.add_argument("--candidate", default=None, help="Path to a candidate JSON file or JSONL file.")
    parser.add_argument("--instruction", default="")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    model_dir = repo_root / "models" / "zeus-evaluator-v1"
    candidate = load_candidate(Path(args.candidate)) if args.candidate else {
        "instruction": args.instruction,
        "ideal_output": args.output,
        "source": "cli",
        "status": "unknown",
    }
    print(json.dumps(score_candidate_example(candidate, model_dir), indent=2))


def load_candidate(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return {}
    first_line = text.splitlines()[0]
    return json.loads(first_line)


if __name__ == "__main__":
    main()
