# Zeus AI Workbench

Zeus AI Workbench is a local FastAPI + React/Vite app for working with Ollama models, browsing an allowed project folder, running a constrained local agent, and indexing small documents for local RAG.

The app does not require cloud APIs, paid services, secrets, API keys, or telemetry.

Zeus now also includes the first Zeus-native model track. Ollama/Qwen can remain a temporary runtime or communication layer, but `training/` contains a from-scratch `Zeus-Tiny` path for building local Zeus-owned weights over time.

## Requirements

- Windows 11, macOS, or Linux
- Python 3.10+
- Node.js 20.19+ or 22.12+
- Ollama running locally at `http://localhost:11434`
- One local Ollama chat model, for example `llama3.2:3b` or `qwen3.5:4b`
- Recommended on Windows: `uv` for Python installs and `pnpm` for frontend installs
- Rust/Cargo for desktop development with Tauri

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

## Desktop App

Zeus AI includes a Tauri desktop shell. Desktop dev/build commands generate a local FastAPI backend sidecar with PyInstaller, bundle it with Tauri, and start it automatically when the desktop app opens.

The sidecar uses:

- `ZEUSAI_DESKTOP=1`
- `ZEUSAI_FULL_COMPUTER_ACCESS=1`
- `ZEUSAI_ENABLE_SHELL=1`
- `ZEUSAI_COMMAND_RISK_POLICY=log`
- `ZEUSAI_BACKEND_HOST=127.0.0.1`
- `ZEUSAI_BACKEND_PORT=8000`

Closing the desktop window stops the backend sidecar process tree.

Development:

```powershell
cd frontend
pnpm install
npm run desktop:dev
```

Production desktop build:

```powershell
cd frontend
npm run desktop:build
```

Build outputs are created under `frontend/src-tauri/target/release/`. On Windows, the full build produces:

- `frontend/src-tauri/target/release/zeus-ai-desktop.exe`
- `frontend/src-tauri/target/release/bundle/msi/Zeus AI_0.1.0_x64_en-US.msi`
- `frontend/src-tauri/target/release/bundle/nsis/Zeus AI_0.1.0_x64-setup.exe`

The generated backend sidecar binary lives under `frontend/src-tauri/binaries/` and is intentionally ignored by Git. Rebuild it with:

```powershell
.\scripts\build-backend-sidecar.ps1
```

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

## Zeus-Native Model Track

The long-term goal is not to hide Qwen behind a Zeus label. The repo has a native model path for training Zeus-owned weights from scratch:

```powershell
python training/data/build_dataset.py
python training/tokenizer/train_tokenizer.py
python training/pretrain/train_zeus_tiny.py
python training/inference/zeus_tiny_infer.py --prompt "Classify this task"
```

`Zeus-Tiny` starts as a small specialist model for routing, tool-call formatting, memory classification, planning, and result review. It is expected to be weak at fluent chat until the dataset and compute grow.

To route backend chat through Zeus-Tiny:

```powershell
$env:ZEUSAI_NATIVE_MODEL = "1"
.\.venv\Scripts\python.exe backend\main.py
```

If no checkpoint exists yet, Zeus reports the training commands instead of silently falling back to Qwen.

## Backend

Manual start:

```powershell
.\.venv\Scripts\python.exe backend\main.py
```

API:

- Health: `http://localhost:8000/api/health`
- Models: `http://localhost:8000/api/models`
- Chat: `POST http://localhost:8000/api/chat`
- Kill switch: `POST http://localhost:8000/api/control/kill`
- Resume: `POST http://localhost:8000/api/control/resume`
- Audit log: `GET http://localhost:8000/api/audit/actions`
- File list/read/write: constrained to allowed roots
- RAG upload/query: local only

By default, file access is limited to the repo root. To allow additional project folders:

```powershell
$env:ZEUSAI_ALLOWED_ROOTS = "G:\My Drive\Codex Coworker\omnilocal-ai;C:\path\to\another\project"
.\.venv\Scripts\python.exe backend\main.py
```

To let Zeus see all local drives that the current Windows user can access:

```powershell
$env:ZEUSAI_FULL_COMPUTER_ACCESS = "1"
.\.venv\Scripts\python.exe backend\main.py
```

Shell command execution is disabled by default. To enable it for allowed roots only:

```powershell
$env:ZEUSAI_ENABLE_SHELL = "1"
```

Command risk handling is configurable:

```powershell
$env:ZEUSAI_COMMAND_RISK_POLICY = "log"   # run and log known-risk patterns
$env:ZEUSAI_COMMAND_RISK_POLICY = "warn"  # run and include warning metadata
$env:ZEUSAI_COMMAND_RISK_POLICY = "block" # block known-risk patterns
```

The default is `log`, because Zeus is meant to show what it can do before you decide what policies you want.

Emergency controls:

- `POST /api/control/kill` stops future tool execution and asks running agent loops to halt.
- `POST /api/control/resume` clears the stop state.
- The sidebar has a Stop Zeus / Resume Zeus button.

Audit logs:

- Tool calls and control events are written to `backend/logs/actions.jsonl`.
- Recent actions are available from `GET /api/audit/actions`.

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

## Control And Visibility Notes

- No cloud LLM APIs are required.
- The app talks to local Ollama by default.
- Cloud/API connectors can be added later when the user supplies keys.
- File browsing and file writes use `ZEUSAI_ALLOWED_ROOTS`, or all local roots when `ZEUSAI_FULL_COMPUTER_ACCESS=1`.
- The default allowed root is this repo until full-computer mode is enabled.
- Uploaded RAG files are stored under `backend/uploads/`, which is ignored by Git.
- Local RAG stores are ignored by Git.
- Shell execution is disabled unless `ZEUSAI_ENABLE_SHELL=1`.
- Automation actions are logged locally.
- The kill switch can stop future tool execution and halt agent loops between steps.
- This is a local developer tool and does not include authentication. Do not expose it to a public network.

## Troubleshooting

- `Ollama connection failed`: start Ollama and verify `ollama list`.
- `Path is outside allowed roots`: set `ZEUSAI_ALLOWED_ROOTS` or `ZEUSAI_FULL_COMPUTER_ACCESS=1` before starting the backend.
- `pip install` stalls on Windows: use `uv pip install --python .\.venv\Scripts\python.exe -r backend\requirements.txt`.
- `npm install` fails under Google Drive: move or clone the repo to a normal local NTFS folder such as `C:\Users\<you>\source\omnilocal-ai`, then run frontend installs there. This repo was verified from a local `C:` copy because package extraction failed repeatedly in the Google Drive workspace.
- RAG quality is basic by default: the core install uses a lightweight local lexical index. For heavier semantic RAG, install `backend/requirements-optional-rag.txt`.

## Known Limitations

- The desktop app has Windows sidecar packaging now; macOS/Linux desktop packaging has not been verified.
- The default RAG fallback is lexical, not embedding-based semantic search.
- Full-computer use is supported through environment configuration today; it needs a proper desktop settings UI.
- APIs/connectors/MCP are planned but not built in yet.
- Future user-facing packaging should add install/update flows, first-run model checks, an action log viewer, connector management, and per-workspace automation policy.
