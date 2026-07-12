"""Repository-map source adapter for Zeus Knowledge.

The adapter imports a public, machine-readable repository manifest into Zeus's
local knowledge lane. It keeps the remote source and each downloaded artifact
inspectable; it does not turn repository summaries into behavior training data.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import shutil
import time
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from config import get_data_dir, get_knowledge_dir
from knowledge_index import build_knowledge_index


DEFAULT_MANIFEST_URL = (
    "https://raw.githubusercontent.com/JaronKBragg7337/"
    "Summary-Of-repos-Memory-linker/main/repos.json"
)
MAX_SUMMARIES = 250
MAX_ARTIFACT_BYTES = 2_000_000


class RepositoryMapError(RuntimeError):
    """Raised when a repository map cannot be safely acquired or normalized."""


class RepositoryMapSource:
    def status(self) -> dict[str, Any]:
        state = self._load_state()
        return {
            "source": "repository_map",
            "configured_manifest_url": state.get("manifest_url", DEFAULT_MANIFEST_URL),
            "last_sync_at": state.get("last_sync_at"),
            "last_error": state.get("last_error"),
            "repository_count": state.get("repository_count", 0),
            "summary_count": state.get("summary_count", 0),
            "artifact_root": str(self._artifact_root()),
            "provenance_path": str(self._provenance_path()),
        }

    async def sync(self, *, manifest_url: str | None = None, rebuild_index: bool = True) -> dict[str, Any]:
        return await asyncio.to_thread(self._sync_blocking, manifest_url, rebuild_index)

    def _sync_blocking(self, manifest_url: str | None, rebuild_index: bool) -> dict[str, Any]:
        state = self._load_state()
        selected_url = _validate_manifest_url(manifest_url or state.get("manifest_url") or DEFAULT_MANIFEST_URL)
        started_at = _timestamp()
        try:
            manifest_text = _fetch_text(selected_url)
            manifest = json.loads(manifest_text)
            if not isinstance(manifest, dict) or not isinstance(manifest.get("repos"), list):
                raise RepositoryMapError("Repository map manifest must contain a 'repos' list.")

            repos = manifest["repos"]
            if len(repos) > MAX_SUMMARIES:
                raise RepositoryMapError(f"Repository map contains more than {MAX_SUMMARIES} repositories.")

            source_base = selected_url.rsplit("/", 1)[0] + "/"
            staged_root = self._artifact_root().with_name("repository-map-staging")
            if staged_root.exists():
                shutil.rmtree(staged_root)
            summary_root = staged_root / "summaries"
            summary_root.mkdir(parents=True, exist_ok=True)
            (staged_root / "repos.json").write_text(manifest_text, encoding="utf-8")

            artifacts: list[dict[str, Any]] = []
            for repo in repos:
                if not isinstance(repo, dict):
                    continue
                summary_file = _validated_summary_path(repo.get("summary_file"))
                if not summary_file:
                    continue
                summary_url = source_base + summary_file
                text = _fetch_text(summary_url)
                destination = staged_root / Path(summary_file)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(text, encoding="utf-8")
                artifacts.append({
                    "repository": str(repo.get("name", "unknown")),
                    "source_url": summary_url,
                    "local_path": str(Path(summary_file)),
                    "sha256": _sha256(text),
                    "bytes": len(text.encode("utf-8")),
                })

            catalog = _render_catalog(manifest, selected_url, artifacts, started_at)
            (staged_root / "README.md").write_text(catalog, encoding="utf-8")
            provenance = {
                "adapter": "repository_map",
                "manifest_url": selected_url,
                "fetched_at": started_at,
                "manifest_sha256": _sha256(manifest_text),
                "repository_count": len(repos),
                "artifacts": artifacts,
            }
            (staged_root / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")

            destination_root = self._artifact_root()
            backup_root = destination_root.with_name("repository-map-previous")
            if backup_root.exists():
                shutil.rmtree(backup_root)
            if destination_root.exists():
                destination_root.rename(backup_root)
            staged_root.rename(destination_root)
            if backup_root.exists():
                shutil.rmtree(backup_root)

            result = {
                "source": "repository_map",
                "manifest_url": selected_url,
                "synced_at": started_at,
                "repository_count": len(repos),
                "summary_count": len(artifacts),
                "artifact_root": str(destination_root),
                "provenance_path": str(self._provenance_path()),
            }
            if rebuild_index:
                result["knowledge_index"] = build_knowledge_index()
            self._save_state({
                "manifest_url": selected_url,
                "last_sync_at": started_at,
                "last_error": None,
                "repository_count": len(repos),
                "summary_count": len(artifacts),
            })
            return result
        except (OSError, ValueError, json.JSONDecodeError, RepositoryMapError) as error:
            self._save_state({
                "manifest_url": selected_url,
                "last_error": str(error),
            })
            raise RepositoryMapError(str(error)) from error

    def _artifact_root(self) -> Path:
        return get_knowledge_dir() / "project_docs" / "repository-map"

    def _state_path(self) -> Path:
        return get_data_dir() / "sources" / "repository-map.json"

    def _provenance_path(self) -> Path:
        return self._artifact_root() / "provenance.json"

    def _load_state(self) -> dict[str, Any]:
        try:
            data = json.loads(self._state_path().read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_state(self, updates: dict[str, Any]) -> None:
        path = self._state_path()
        existing = self._load_state()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({**existing, **updates}, indent=2), encoding="utf-8")


def _fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Zeus-AI-Repository-Map/1.0"})
    with urlopen(request, timeout=30) as response:  # nosec B310 - URL is validated/configured by the local user.
        data = response.read(MAX_ARTIFACT_BYTES + 1)
    if len(data) > MAX_ARTIFACT_BYTES:
        raise RepositoryMapError(f"Source artifact exceeded {MAX_ARTIFACT_BYTES} bytes: {url}")
    return data.decode("utf-8")


def _validate_manifest_url(value: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme != "https" or not parsed.netloc or not parsed.path.endswith(".json"):
        raise RepositoryMapError("Manifest URL must be an HTTPS URL ending in .json.")
    return value.strip()


def _validated_summary_path(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.suffix.lower() not in {".md", ".txt"}:
        raise RepositoryMapError(f"Invalid summary_file path: {value!r}")
    return path.as_posix()


def _render_catalog(manifest: dict[str, Any], manifest_url: str, artifacts: list[dict[str, Any]], fetched_at: str) -> str:
    lines = [
        "# Repository Map", "",
        "This local knowledge artifact was imported by Zeus. It is factual project reference material, not training data.", "",
        f"- Source manifest: {manifest_url}",
        f"- Fetched at: {fetched_at}",
        f"- Owner: {manifest.get('owner', 'unknown')}",
        f"- Repositories: {len(manifest.get('repos', []))}",
        f"- Downloaded summaries: {len(artifacts)}", "",
        "## Repository Directory", "",
    ]
    for repo in manifest.get("repos", []):
        if not isinstance(repo, dict):
            continue
        lines.extend([
            f"### {repo.get('name', 'Unnamed repository')}",
            f"- URL: {repo.get('url', '')}",
            f"- Category: {repo.get('category', 'Uncategorized')}",
            f"- Status: {repo.get('status', 'Unknown')}",
            f"- Summary: {repo.get('summary', '')}",
            f"- AI notes: {repo.get('ai_notes', '')}",
            "",
        ])
    return "\n".join(lines)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


repository_map = RepositoryMapSource()
