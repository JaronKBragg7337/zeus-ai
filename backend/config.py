"""Local runtime configuration for OmniLocal AI Workbench."""
import os
from pathlib import Path
from typing import Iterable, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BACKEND_DIR / "uploads"
LOCAL_RAG_DIR = BACKEND_DIR / "local_rag_store"
CHROMA_DB_DIR = BACKEND_DIR / "chroma_db"


def get_allowed_roots() -> List[Path]:
    """Return directories the app is allowed to browse or modify."""
    raw = os.getenv("OMNILOCAL_ALLOWED_ROOTS")
    roots: Iterable[str] = raw.split(os.pathsep) if raw else [str(PROJECT_ROOT)]
    resolved = []
    for item in roots:
        if not item.strip():
            continue
        resolved.append(Path(item).expanduser().resolve())
    return resolved or [PROJECT_ROOT]


def format_allowed_roots() -> List[str]:
    return [str(path) for path in get_allowed_roots()]


def is_shell_enabled() -> bool:
    return os.getenv("OMNILOCAL_ENABLE_SHELL", "").lower() in {"1", "true", "yes", "on"}
