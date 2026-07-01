"""Train Zeus Evaluator v1.

This trains a tiny local linear scorer from evaluator JSONL. It does not use a
cloud API or pretrained model. The output is a JSON model consumed by the
backend evaluator runtime.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from evaluator_model import DEFAULT_FEATURE_SIZE, hashed_features, predict_score  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[2])
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--model-dir", default=None)
    parser.add_argument("--feature-size", type=int, default=DEFAULT_FEATURE_SIZE)
    parser.add_argument("--epochs", type=int, default=600)
    parser.add_argument("--lr", type=float, default=0.8)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    dataset = Path(args.dataset) if args.dataset else repo_root / "data" / "processed" / "zeus_evaluator.jsonl"
    model_dir = Path(args.model_dir) if args.model_dir else repo_root / "models" / "zeus-evaluator-v1"
    examples = load_examples(dataset, args.feature_size)
    if not examples:
        raise SystemExit(f"No evaluator examples found in {dataset}")

    random.seed(args.seed)
    weights = [0.0] * args.feature_size
    bias = 0.0

    for epoch in range(1, args.epochs + 1):
        random.shuffle(examples)
        total_loss = 0.0
        for features, target in examples:
            logit = bias + sum(weights[index] * value for index, value in features.items())
            prediction = 1.0 / (1.0 + pow(2.718281828459045, -max(-60.0, min(60.0, logit))))
            error = prediction - target
            for index, value in features.items():
                weights[index] -= args.lr * error * value
            bias -= args.lr * error
            total_loss += (prediction - target) ** 2

        if epoch == 1 or epoch % 100 == 0 or epoch == args.epochs:
            print(f"epoch={epoch} mse={total_loss / len(examples):.6f}")

    model = {
        "type": "zeus-evaluator-linear-v1",
        "trained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset": str(dataset),
        "example_count": len(examples),
        "feature_size": args.feature_size,
        "weights": [round(value, 8) for value in weights],
        "bias": round(bias, 8),
        "thresholds": {"reject_max": 0.33, "approve_min": 0.67},
    }
    model_dir.mkdir(parents=True, exist_ok=True)
    output = model_dir / "evaluator.json"
    output.write_text(json.dumps(model, indent=2), encoding="utf-8")
    print(f"Saved Zeus Evaluator v1 to {output}")
    print_training_preview(dataset, model)


def load_examples(path: Path, feature_size: int) -> List[Tuple[Dict[int, float], float]]:
    examples = []
    for record in read_jsonl(path):
        text = record.get("text") or ""
        score = float(record.get("score", 0.0))
        score = max(0.0, min(1.0, score))
        features = hashed_features(text, feature_size)
        if features:
            examples.append((features, score))
    return examples


def print_training_preview(dataset: Path, model: Dict) -> None:
    for record in read_jsonl(dataset)[:5]:
        text = record.get("text", "")
        score = predict_score(text, model)
        print(f"preview target={float(record.get('score', 0.0)):.2f} predicted={score:.3f} decision={record.get('decision')}")


def read_jsonl(path: Path) -> List[Dict]:
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
