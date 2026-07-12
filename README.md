# Zeus AI Workbench

Zeus AI Workbench is a local FastAPI + React/Vite desktop workbench for working with Ollama models, local files, desktop tools, local RAG, and Zeus-owned-model experiments.

The base application does not require cloud APIs, paid services, secrets, API keys, or telemetry. Optional connectors such as Slack keep their credentials in local operating-system storage, never in Git.

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

The packaged Windows app starts with desktop and shell tools enabled. Desktop tools are currently Windows-only and include:

- visible-window discovery and focusing
- full-desktop or region screenshots saved as local PNG files
- local OCR through Tesseract
- mouse movement/clicks and keyboard typing/hotkeys
- timed waits for multi-step desktop tasks

Desktop screenshots are stored under `%LOCALAPPDATA%\Zeus AI\data\screenshots` in the installed app. They are local runtime artifacts and are ignored by Git.

## One-Command Docker Deployment

Zeus can run as two containers while using an Ollama service already running on the host. `compose.yaml` starts the FastAPI backend and the browser frontend, persists Zeus data/knowledge in Docker volumes, and deliberately does **not** start or download Ollama.

```powershell
docker compose up --build
```

Open `http://localhost:3000`. The backend reaches host Ollama through `http://host.docker.internal:11434` by default. On a Linux host, set `ZEUSAI_OLLAMA_BASE_URL` in a local `.env` if your Ollama service is reachable at a different address. Copy `.env.example` for optional port/workspace overrides; do not put secrets in it.

Container mode disables full desktop mouse/keyboard/screen control because a container cannot safely observe or control the host desktop. Use the packaged desktop app for Windows computer use.

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

Zeus also captures local training examples from real use:

- tool calls
- agent runs
- chat completions
- user corrections
- successful task completions

Raw traces are written under `data/tool_traces/`. Training examples are written first to `data/instruction_examples/candidates.jsonl` with `review_status: pending`. Approved examples move to `data/instruction_examples/approved.jsonl`; rejected examples move to `data/instruction_examples/rejected.jsonl`. All generated local data is ignored by Git.

The desktop app includes a Training Review panel for approving or rejecting pending examples.

The dataset builder trains on `seed.jsonl` plus `approved.jsonl` by default:

```powershell
python training/data/build_dataset.py
```

Use opt-in flags such as `--include-candidates`, `--include-tool-traces`, or `--include-knowledge` only when intentionally experimenting. Set `ZEUSAI_CAPTURE_TRAINING=0` to disable capture.

In the packaged desktop app, generated training data defaults to `%LOCALAPPDATA%\Zeus AI\data` so it survives app restarts.

Knowledge is separate from training data. Put factual reference material under `knowledge/`; put behavior examples under `data/instruction_examples/`.

Zeus Knowledge can be indexed and searched locally:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/knowledge/index
Invoke-RestMethod -Method Post http://localhost:8000/api/knowledge/search -ContentType "application/json" -Body '{"query":"what does this manual say?","top_k":5}'
```

The desktop app includes a Knowledge panel for rebuilding and searching the local index.

The packaged desktop app also watches these local Knowledge source folders by default. It checks for changes every 30 seconds and rebuilds only when files change. The Knowledge panel can pause/resume this local watcher.

In the packaged desktop app, Zeus Knowledge defaults to `%LOCALAPPDATA%\Zeus AI\knowledge`.

### Repository Map Source

The Repository Map panel imports a public `repos.json` manifest and its declared project summaries into local Knowledge. Zeus records the manifest URL, fetch time, and SHA-256 content hashes in `knowledge/project_docs/repository-map/provenance.json`, then rebuilds local search. This is a factual retrieval lane, not automatic private memory or model training.

The default source is the public [Summary-Of-repos-Memory-linker](https://github.com/JaronKBragg7337/Summary-Of-repos-Memory-linker) manifest. The linked Heartbeat Observatory view at [HeartbeatCenter](https://www.heartbeatobservatory.com/HeartbeatCenter/) renders that same manifest at runtime, so the 3D directory and Zeus use one canonical public inventory.

Evaluator/scoring data can be built separately:

```powershell
python training/data/build_evaluator_dataset.py
python training/evaluator/train_evaluator_v1.py
```

This writes `data/processed/zeus_evaluator.jsonl` from seed evaluator examples plus local approved/rejected/corrected examples.

The trained Evaluator v1 model is saved to `models/zeus-evaluator-v1/evaluator.json` during repo development and can score pending candidates through `POST /api/training/evaluate` or the Training Review panel. In the packaged desktop app, Evaluator v1 defaults to `%LOCALAPPDATA%\Zeus AI\models\zeus-evaluator-v1\evaluator.json`.

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
- Conversations: `GET /api/conversations`, `GET /api/conversations/{id}`, `POST /api/conversations`
- Kill switch: `POST http://localhost:8000/api/control/kill`
- Resume: `POST http://localhost:8000/api/control/resume`
- Audit log: `GET http://localhost:8000/api/audit/actions`
- File list/read/write: constrained to allowed roots
- RAG upload/query: local only
- Knowledge status/index/search: local factual retrieval under `knowledge/`
- Repository Map status/sync: `GET /api/sources/repository-map/status`, `POST /api/sources/repository-map/sync`

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

When full-computer mode is enabled on Windows, the following local tools are registered in addition to file/shell tools:

- `get_screen_info`, `list_windows`, `focus_window`
- `capture_screen`, `read_screen_text`
- `move_mouse`, `click_mouse`, `type_text`, `press_keys`, `wait_for`

The agent is instructed to inspect visible windows or the screen before interacting with the desktop. It records normal tool/audit data locally. The current desktop layer is coordinate-based; it is not yet a browser DOM automation system or a game-engine-specific testing framework.

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

### Conversation History

Chat conversations are persisted locally and can be reopened from the conversation history pane. In a packaged desktop install, they are saved under `%LOCALAPPDATA%\Zeus AI\data\conversations`; in repository development they are saved under `data/conversations/`. Conversation records are not committed to Git.

### Inspectable Memory

The Memory panel holds user-managed long-term context: facts, preferences, decisions, project notes, and instructions. It is a local SQLite store at `%LOCALAPPDATA%\Zeus AI\data\memory\zeus_memory.sqlite3` in the packaged app. Relevant saved entries are added to Chat and Agent context by default, and Chat exposes a memory toggle.

Memory is not training data and is not a silent capture of every conversation. It can be edited or deleted in the panel. See `docs/memory-and-remote-sync.md` for the planned optional Heartbeat Observatory/Supabase sync architecture.

### Active Heartbeat

The packaged desktop app starts a local Zeus Heartbeat every 15 minutes. It observes local model availability, tool/capability state, allowed roots, knowledge and memory status, then writes an inspectable observation and a concrete curiosity-task queue under `%LOCALAPPDATA%\Zeus AI\data\heartbeat`.

Use the Heartbeat panel to run an observation immediately, pause/resume the timer, or select an interval from 5 minutes to 4 hours. The heartbeat is active while Zeus is running. It does not automatically browse the web, execute arbitrary tasks, or turn observations into training data; those capabilities will be added through source/task adapters with their own provenance records.

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
- Screenshot files, conversation records, tool traces, training candidates, model weights, and connector credentials are local artifacts and are ignored by Git.
- User-managed memory is stored locally by default. Its SQLite database is ignored by Git.
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
- Desktop observation/control is Windows-only and uses screenshots, OCR, windows handles, and absolute coordinates. It does not yet provide robust game-state perception, replay, video capture, or browser DOM automation.
- Tool-capable Ollama models are required for reliable multi-step agent work. Zeus now preserves Ollama's native assistant tool-call message followed by the tool result, but a weak or misconfigured model can still stop a task without selecting the next tool.
- Conversation history is local-only. It has no export, search, delete, sync, team sharing, or cross-device synchronization yet.
- Local Zeus Memory is implemented, but remote Heartbeat/Supabase synchronization and 3D visualization are designed rather than implemented.
- Slack/mobile communication is available through the optional local Slack Connector panel. It uses Socket Mode and Windows Credential Manager for an `xoxb-` bot token plus an `xapp-` app token; no Slack token, secret, or workspace data belongs in this repository. The Slack app still needs Socket Mode, `message.im`, and the documented bot scopes before it can receive DMs.
- The default RAG fallback is lexical, not embedding-based semantic search.
- Full-computer access, shell enablement, and command-risk policy are environment/runtime configuration today; they need a proper desktop settings UI.
- APIs/connectors/MCP are planned but not built in yet.
- Future user-facing packaging should add install/update flows, first-run model checks, an action log viewer, connector management, and per-workspace automation policy.

## Build Method Docs

Zeus is also documenting the method used to build it so other people and future AI coworkers can repeat the path:

- `docs/founder-system-blueprint.md`
- `docs/ai-coworker-protocol.md`
- `docs/implementation-log.md`
- `docs/repeatable-build-playbook.md`
- `docs/connector-handoff.md`
- `docs/memory-and-remote-sync.md`
- `docs/architecture-principles.md`
