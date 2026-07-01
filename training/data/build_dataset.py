"""Build local Zeus JSONL training data.

This script gathers safe local seed examples plus optional local-only folders.
Generated output is ignored by Git.
"""
import argparse
import json
from pathlib import Path


SOURCE_DIRS = [
    "data/raw",
    "data/instruction_examples",
    "data/conversations",
    "data/tool_traces",
    "data/code_tasks",
    "data/project_docs",
    "data/decisions",
]


def records_from_file(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return

    if path.suffix.lower() == ".jsonl":
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                yield {"text": line.strip(), "source": str(path)}
                continue
            if "text" in data:
                yield {"text": data["text"], "source": str(path)}
            elif "instruction" in data and "ideal_output" in data:
                yield {
                    "text": f"<|user|>\n{data['instruction']}\n<|assistant|>\n{data['ideal_output']}",
                    "source": str(path),
                }
            else:
                yield {"text": json.dumps(data, ensure_ascii=False), "source": str(path)}
        return

    yield {"text": text, "source": str(path)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output = Path(args.output) if args.output else repo_root / "data" / "processed" / "zeus_corpus.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with output.open("w", encoding="utf-8") as out:
        for rel in SOURCE_DIRS:
            base = repo_root / rel
            if not base.exists():
                continue
            for path in sorted(base.rglob("*")):
                if path.is_file() and path.suffix.lower() in {".txt", ".md", ".json", ".jsonl"}:
                    for record in records_from_file(path):
                        if record.get("text", "").strip():
                            out.write(json.dumps(record, ensure_ascii=False) + "\n")
                            count += 1

    print(f"Wrote {count} records to {output}")


if __name__ == "__main__":
    main()
