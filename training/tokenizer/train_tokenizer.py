"""Train a simple Zeus tokenizer from local text.

This is intentionally small and dependency-free. It learns a word-level vocab
from local Zeus data and saves tokenizer.json beside the Zeus-Tiny checkpoint.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path


SPECIAL_TOKENS = ["<|pad|>", "<|unk|>", "<|bos|>", "<|eos|>", "<|system|>", "<|user|>", "<|assistant|>"]
TOKEN_RE = re.compile(r"<\|[^|]+\|>|[A-Za-z0-9_:\\./\\\\-]+|[^\s]", re.UNICODE)


def iter_texts(root: Path):
    candidates = [
        root / "data" / "raw",
        root / "data" / "instruction_examples",
        root / "data" / "processed",
        root / "data" / "project_docs",
        root / "data" / "decisions",
    ]
    for base in candidates:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".txt", ".md", ".jsonl", ".json"}:
                yield path.read_text(encoding="utf-8", errors="replace")


def tokenize(text: str):
    return TOKEN_RE.findall(text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[2])
    parser.add_argument("--vocab-size", type=int, default=4096)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output = Path(args.output) if args.output else repo_root / "models" / "zeus-tiny" / "tokenizer.json"
    output.parent.mkdir(parents=True, exist_ok=True)

    counts = Counter()
    for text in iter_texts(repo_root):
        counts.update(tokenize(text))

    vocab = list(SPECIAL_TOKENS)
    for token, _count in counts.most_common(max(0, args.vocab_size - len(vocab))):
        if token not in vocab:
            vocab.append(token)

    tokenizer = {
        "type": "zeus-word-v1",
        "special_tokens": SPECIAL_TOKENS,
        "token_to_id": {token: idx for idx, token in enumerate(vocab)},
        "id_to_token": {str(idx): token for idx, token in enumerate(vocab)},
        "pattern": TOKEN_RE.pattern,
    }
    output.write_text(json.dumps(tokenizer, indent=2), encoding="utf-8")
    print(f"Saved tokenizer with {len(vocab)} tokens to {output}")


if __name__ == "__main__":
    main()
