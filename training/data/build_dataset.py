"""Build local Zeus JSONL training data.

By default this script trains only on seed examples and reviewed/approved local
usage examples. Raw traces, pending candidates, and knowledge sources are useful
inputs, but they must be opted in so Zeus does not learn every bug as a win.
"""
import argparse
import json
from pathlib import Path


DEFAULT_FILES = [
    "data/instruction_examples/seed.jsonl",
    "data/instruction_examples/approved.jsonl",
]

CURATED_TRAINING_DIRS = [
    "data/raw",
    "data/conversations",
    "data/code_tasks",
    "data/project_docs",
    "data/decisions",
]

KNOWLEDGE_DIRS = [
    "knowledge/manuals",
    "knowledge/research",
    "knowledge/books",
    "knowledge/code_docs",
    "knowledge/project_docs",
    "knowledge/processed",
]

INCLUDE_EXTENSIONS = {".txt", ".md", ".json", ".jsonl"}


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
    parser.add_argument("--include-candidates", action="store_true", help="Include pending candidate examples.")
    parser.add_argument("--include-tool-traces", action="store_true", help="Include raw local tool traces.")
    parser.add_argument("--include-curated-training-folders", action="store_true", help="Include manually curated data/* folders.")
    parser.add_argument("--include-knowledge", action="store_true", help="Include knowledge folders. Keep this separate unless intentionally training behavior on docs.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output = Path(args.output) if args.output else repo_root / "data" / "processed" / "zeus_corpus.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)

    files = [repo_root / rel for rel in DEFAULT_FILES]
    dirs = []

    if args.include_candidates:
        files.append(repo_root / "data" / "instruction_examples" / "candidates.jsonl")
    if args.include_tool_traces:
        dirs.append(repo_root / "data" / "tool_traces")
    if args.include_curated_training_folders:
        dirs.extend(repo_root / rel for rel in CURATED_TRAINING_DIRS)
    if args.include_knowledge:
        dirs.extend(repo_root / rel for rel in KNOWLEDGE_DIRS)

    count = 0
    with output.open("w", encoding="utf-8") as out:
        for path in files:
            count += write_records(path, out)
        for base in dirs:
            if not base.exists():
                continue
            for path in sorted(base.rglob("*")):
                count += write_records(path, out)

    print(f"Wrote {count} records to {output}")


def write_records(path: Path, out) -> int:
    if not path.exists() or not path.is_file() or path.suffix.lower() not in INCLUDE_EXTENSIONS:
        return 0

    count = 0
    for record in records_from_file(path):
        if record.get("text", "").strip():
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


if __name__ == "__main__":
    main()
