"""Local Zeus Knowledge indexing.

Knowledge is factual reference material for retrieval. It is deliberately kept
separate from instruction/training examples, which change Zeus behavior.
"""
import hashlib
import json
import math
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List

from config import get_knowledge_dir, get_knowledge_index_dir


SOURCE_FOLDERS = {"manuals", "research", "books", "code_docs", "project_docs", "processed"}
INCLUDE_EXTENSIONS = {
    ".txt",
    ".md",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".json",
    ".yaml",
    ".yml",
    ".html",
    ".css",
    ".csv",
    ".log",
}
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
MAX_FILE_CHARS = 2_000_000


def build_knowledge_index() -> Dict[str, Any]:
    root = get_knowledge_dir().resolve()
    index_dir = get_knowledge_index_dir().resolve()
    index_dir.mkdir(parents=True, exist_ok=True)
    index_path = _index_path()
    manifest_path = _manifest_path()

    chunks_written = 0
    files_indexed = 0
    with index_path.open("w", encoding="utf-8") as handle:
        for path in _iter_source_files(root):
            text = path.read_text(encoding="utf-8", errors="replace")[:MAX_FILE_CHARS]
            if not text.strip():
                continue
            files_indexed += 1
            rel_path = str(path.relative_to(root))
            category = Path(rel_path).parts[0] if Path(rel_path).parts else "unknown"
            for chunk_index, chunk in enumerate(_chunk_text(text)):
                if not chunk.strip():
                    continue
                record = {
                    "id": _chunk_id(rel_path, chunk_index, chunk),
                    "source": rel_path,
                    "category": category,
                    "chunk_index": chunk_index,
                    "content": chunk,
                }
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                chunks_written += 1

    manifest = {
        "built_at": _timestamp(),
        "knowledge_root": str(root),
        "index_path": str(index_path),
        "files_indexed": files_indexed,
        "chunks": chunks_written,
        "source_folders": sorted(SOURCE_FOLDERS),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def knowledge_status() -> Dict[str, Any]:
    manifest_path = _manifest_path()
    index_path = _index_path()
    manifest: Dict[str, Any] = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}

    source_files = list(_iter_source_files(get_knowledge_dir().resolve()))
    return {
        "knowledge_root": str(get_knowledge_dir().resolve()),
        "index_path": str(index_path),
        "indexed": index_path.exists(),
        "source_file_count": len(source_files),
        "files_indexed": manifest.get("files_indexed", 0),
        "chunks": manifest.get("chunks", 0),
        "built_at": manifest.get("built_at"),
        "source_folders": sorted(SOURCE_FOLDERS),
    }


def search_knowledge(query: str, top_k: int = 5) -> Dict[str, Any]:
    top_k = max(1, min(top_k, 25))
    records = _read_index()
    scored = []
    for record in records:
        score = _cosine_score(query, record.get("content", ""))
        if score > 0:
            scored.append((score, record))
    scored.sort(key=lambda item: item[0], reverse=True)

    matches = [
        {
            "source": record.get("source", "unknown"),
            "category": record.get("category", "unknown"),
            "chunk_index": record.get("chunk_index", 0),
            "score": round(score, 6),
            "content": record.get("content", ""),
        }
        for score, record in scored[:top_k]
    ]
    context = "\n\n---\n\n".join(match["content"] for match in matches)
    return {
        "query": query,
        "matches": matches,
        "context": context,
        "indexed": _index_path().exists(),
    }


def _iter_source_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []

    files = []
    for folder in SOURCE_FOLDERS:
        base = root / folder
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix.lower() in INCLUDE_EXTENSIONS and path.name != ".gitkeep":
                files.append(path)
    return files


def _chunk_text(text: str) -> List[str]:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= CHUNK_SIZE:
        return [compact]

    chunks = []
    start = 0
    while start < len(compact):
        end = start + CHUNK_SIZE
        chunk = compact[start:end]
        if end < len(compact):
            last_space = chunk.rfind(" ")
            if last_space > CHUNK_SIZE // 2:
                chunk = chunk[:last_space]
                end = start + last_space + 1
        chunks.append(chunk.strip())
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


def _read_index() -> List[Dict[str, Any]]:
    path = _index_path()
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


def _index_path() -> Path:
    return get_knowledge_index_dir() / "knowledge_chunks.jsonl"


def _manifest_path() -> Path:
    return get_knowledge_index_dir() / "manifest.json"


def _chunk_id(source: str, chunk_index: int, chunk: str) -> str:
    digest = hashlib.sha256(f"{source}:{chunk_index}:{chunk[:200]}".encode("utf-8")).hexdigest()
    return digest[:32]


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_]+", text.lower())


def _cosine_score(left: str, right: str) -> float:
    left_counts = Counter(_tokenize(left))
    right_counts = Counter(_tokenize(right))
    if not left_counts or not right_counts:
        return 0.0
    shared = set(left_counts) & set(right_counts)
    dot = sum(left_counts[token] * right_counts[token] for token in shared)
    left_norm = math.sqrt(sum(value * value for value in left_counts.values()))
    right_norm = math.sqrt(sum(value * value for value in right_counts.values()))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


def _timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
