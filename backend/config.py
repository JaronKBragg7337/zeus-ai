"""Local runtime configuration for Zeus AI Workbench."""
import os
import string
from pathlib import Path
from typing import Iterable, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BACKEND_DIR / "uploads"
LOCAL_RAG_DIR = BACKEND_DIR / "local_rag_store"
CHROMA_DB_DIR = BACKEND_DIR / "chroma_db"
LOG_DIR = BACKEND_DIR / "logs"
DATA_DIR = PROJECT_ROOT / "data"
TRAINING_DIR = PROJECT_ROOT / "training"
ZEUS_NATIVE_DIR = PROJECT_ROOT / "models" / "zeus-tiny"
ZEUS_EVALUATOR_DIR = PROJECT_ROOT / "models" / "zeus-evaluator-v1"
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"


def get_allowed_roots() -> List[Path]:
    """Return directories the app is allowed to browse or modify."""
    raw = os.getenv("ZEUSAI_ALLOWED_ROOTS") or os.getenv("OMNILOCAL_ALLOWED_ROOTS")
    if is_full_computer_access_enabled() and not raw:
        return _local_computer_roots()

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
    raw = os.getenv("ZEUSAI_ENABLE_SHELL") or os.getenv("OMNILOCAL_ENABLE_SHELL", "")
    return raw.lower() in {"1", "true", "yes", "on"}


def get_command_risk_policy() -> str:
    policy = os.getenv("ZEUSAI_COMMAND_RISK_POLICY", "log").lower()
    if policy not in {"log", "warn", "block"}:
        return "log"
    return policy


def is_full_computer_access_enabled() -> bool:
    return os.getenv("ZEUSAI_FULL_COMPUTER_ACCESS", "").lower() in {"1", "true", "yes", "on"}


def is_native_model_enabled() -> bool:
    return os.getenv("ZEUSAI_NATIVE_MODEL", "").lower() in {"1", "true", "yes", "on"}


def get_native_model_dir() -> Path:
    return Path(os.getenv("ZEUSAI_NATIVE_MODEL_DIR", ZEUS_NATIVE_DIR)).expanduser()


def get_evaluator_model_dir() -> Path:
    raw = os.getenv("ZEUSAI_EVALUATOR_MODEL_DIR")
    if raw:
        return Path(raw).expanduser()
    if os.getenv("ZEUSAI_DESKTOP") == "1" and os.name == "nt":
        local_app_data = Path(os.getenv("LOCALAPPDATA", Path.home()))
        return local_app_data / "Zeus AI" / "models" / "zeus-evaluator-v1"
    return ZEUS_EVALUATOR_DIR


def get_data_dir() -> Path:
    raw = os.getenv("ZEUSAI_DATA_DIR")
    if raw:
        return Path(raw).expanduser()
    if os.getenv("ZEUSAI_DESKTOP") == "1" and os.name == "nt":
        local_app_data = Path(os.getenv("LOCALAPPDATA", Path.home()))
        return local_app_data / "Zeus AI" / "data"
    return DATA_DIR


def get_memory_db_path() -> Path:
    """Return the local, user-owned SQLite database used for Zeus memory."""
    raw = os.getenv("ZEUSAI_MEMORY_DB")
    if raw:
        return Path(raw).expanduser()
    return get_data_dir() / "memory" / "zeus_memory.sqlite3"


def get_knowledge_dir() -> Path:
    raw = os.getenv("ZEUSAI_KNOWLEDGE_DIR")
    if raw:
        return Path(raw).expanduser()
    if os.getenv("ZEUSAI_DESKTOP") == "1" and os.name == "nt":
        local_app_data = Path(os.getenv("LOCALAPPDATA", Path.home()))
        return local_app_data / "Zeus AI" / "knowledge"
    return KNOWLEDGE_DIR


def get_knowledge_index_dir() -> Path:
    raw = os.getenv("ZEUSAI_KNOWLEDGE_INDEX_DIR")
    if raw:
        return Path(raw).expanduser()
    return get_knowledge_dir() / "index"


def is_training_capture_enabled() -> bool:
    return os.getenv("ZEUSAI_CAPTURE_TRAINING", "1").lower() not in {"0", "false", "no", "off"}


def get_action_log_path() -> Path:
    return Path(os.getenv("ZEUSAI_ACTION_LOG", LOG_DIR / "actions.jsonl")).expanduser()


def _local_computer_roots() -> List[Path]:
    if os.name == "nt":
        roots = []
        for letter in string.ascii_uppercase:
            root = Path(f"{letter}:\\")
            if root.exists():
                roots.append(root.resolve())
        return roots or [Path.home().resolve()]
    return [Path("/").resolve()]
