# OmniLocal AI Workbench

OmniLocal AI Workbench is a local FastAPI + React/Vite app for working with Ollama models, browsing an allowed project folder, running a constrained local agent, and indexing small documents for local RAG.

The app does not require cloud APIs, paid services, secrets, API keys, or telemetry.

## Requirements

- Windows 11, macOS, or Linux
- Python 3.10+
- Node.js 20.19+ or 22.12+
- Ollama running locally at `http://localhost:11434`
- One local Ollama chat model, for example `llama3.2:3b` or `qwen3.5:4b`
- Recommended on Windows: `uv` for Python installs and `pnpm` for frontend installs

## Windows Quickstart

From the repo root:

```powershell
python -m venv .venv
uv pip install --python .\.venv\Scripts\python.exe -r backend\requirements.txt
.\.venv\Scripts\python.exe backend\main.py
```

In a second terminal:

```powershell
cd frontend
pnpm install
npm run dev
```

Open `http://localhost:3000`.

If `uv` is not installed, use:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

If `pnpm` is not installed, try:

```powershell
npm install --no-bin-links
npm run dev
```

## Ollama Setup

Start Ollama, then install a model if needed:

```powershell
ollama pull llama3.2:3b
ollama pull qwen3.5:4b
ollama list
```

The backend model endpoint should return installed models:

```powershell
Invoke-RestMethod http://localhost:8000/api/models
```

## Backend

Manual start:

```powershell
.\.venv\Scripts\python.exe backend\main.py
```

API:

- Health: `http://localhost:8000/api/health`
- Models: `http://localhost:8000/api/models`
- Chat: `POST http://localhost:8000/api/chat`
- File list/read/write: constrained to allowed roots
- RAG upload/query: local only

By default, file access is limited to the repo root. To allow additional project folders:

```powershell
$env:OMNILOCAL_ALLOWED_ROOTS = "G:\My Drive\Codex Coworker\omnilocal-ai;C:\path\to\another\project"
.\.venv\Scripts\python.exe backend\main.py
```

Shell command execution is disabled by default. To enable it for allowed roots only:

```powershell
$env:OMNILOCAL_ENABLE_SHELL = "1"
```

## Frontend

Manual start:

```powershell
cd frontend
pnpm install
npm run dev
```

Production build:

```powershell
npm run build
npm run typecheck
```

The frontend expects the backend on `http://localhost:8000` and runs on `http://localhost:3000`.

## Tests

Backend syntax and tests:

```powershell
.\.venv\Scripts\python.exe -m compileall backend
.\.venv\Scripts\python.exe -m pytest backend\tests
```

Frontend build checks:

```powershell
cd frontend
npm run build
npm run typecheck
```

## Security Notes

- No cloud LLM APIs are used.
- The app talks to local Ollama only.
- File browsing and file writes are restricted to `OMNILOCAL_ALLOWED_ROOTS`.
- The default allowed root is this repo.
- Uploaded RAG files are stored under `backend/uploads/`, which is ignored by Git.
- Local RAG stores are ignored by Git.
- Shell execution is disabled unless `OMNILOCAL_ENABLE_SHELL=1`.
- This is a local developer tool and does not include authentication. Do not expose it to a public network.

## Troubleshooting

- `Ollama connection failed`: start Ollama and verify `ollama list`.
- `Path is outside allowed roots`: set `OMNILOCAL_ALLOWED_ROOTS` before starting the backend.
- `pip install` stalls on Windows: use `uv pip install --python .\.venv\Scripts\python.exe -r backend\requirements.txt`.
- `npm install` fails under Google Drive: move or clone the repo to a normal local NTFS folder such as `C:\Users\<you>\source\omnilocal-ai`, then run frontend installs there. This repo was verified from a local `C:` copy because package extraction failed repeatedly in the Google Drive workspace.
- RAG quality is basic by default: the core install uses a lightweight local lexical index. For heavier semantic RAG, install `backend/requirements-optional-rag.txt`.

## Known Limitations

- The app is local-first and single-user; it is not packaged as a desktop app yet.
- The default RAG fallback is lexical, not embedding-based semantic search.
- The file manager is intentionally constrained to allowed roots.
- Shell tools are opt-in because unrestricted shell access is unsafe.
- Future user-facing app packaging should add install/update flows, first-run model checks, stronger permissions UI, and per-workspace settings.
