# Zeus AI Current State

Last updated: 2026-07-12

## Project

Zeus AI Workbench is a local Windows-first desktop AI workbench with:

- Tauri desktop shell
- bundled FastAPI backend sidecar
- local Ollama chat
- local tools and file access
- local RAG/document ingestion
- audit logs and kill switch
- automatic training-example capture
- training review queue
- Zeus Evaluator v1 candidate scoring
- first Zeus-native tiny model path
- native Ollama multi-step tool-call protocol
- Windows desktop observation and control tools
- local chat conversation history and reload UI
- user-managed local memory retrieved by Chat and Agent
- Docker Compose backend/frontend deployment using host Ollama
- GitHub Actions verification and native package workflows
- Slack Socket Mode mobile/desktop messaging with local Windows Credential Manager storage
- Repository Map source adapter with local provenance records and searchable project summaries
- automatic local Knowledge watcher that rebuilds the index only after source files change

GitHub repo:

```text
https://github.com/JaronKBragg7337/zeus-ai
```

Current branch:

```text
master
```

To find the exact latest commit:

```powershell
git log -1 --oneline
```

## Where To Start

Read these files first, in this order:

1. `docs/handoff/CURRENT_STATE.md`
2. `docs/handoff/TASK_LEDGER.md`
3. `README.md`
4. `docs/ai-coworker-protocol.md`
5. `docs/implementation-log.md`
5. `docs/founder-system-blueprint.md`
6. `training/README.md`
7. `knowledge/README.md`

## Current Verified Build

The current Windows release was built from this repository and installed as a normal application. A source build produces the installer artifacts under:

```text
frontend\src-tauri\target\release\bundle\msi\
frontend\src-tauri\target\release\bundle\nsis\
```

Those generated installers and the PyInstaller sidecar are ignored by Git. A normal Windows installation uses `C:\Program Files\Zeus AI`; generated per-user data uses `%LOCALAPPDATA%\Zeus AI`.

Generated traces and app data default to:

```text
C:\Users\lilli\AppData\Local\Zeus AI\data
```

Packaged desktop Evaluator v1 model default:

```text
C:\Users\lilli\AppData\Local\Zeus AI\models\zeus-evaluator-v1\evaluator.json
```

Conversation history and desktop screenshots default to:

```text
%LOCALAPPDATA%\Zeus AI\data\conversations
%LOCALAPPDATA%\Zeus AI\data\screenshots
```

## 2026-07-12 Verified State

- Rebuilt Zeus from current `master`, removed the previous machine-wide MSI through an elevated Windows Installer operation, and installed the fresh MSI successfully. The current installed Windows version is `0.1.1`; a normal in-place upgrade from `0.1.0` to `0.1.1` was verified.
- The installed desktop application and its bundled backend are currently verified at `C:\Program Files\Zeus AI\zeus-ai-desktop.exe` and `C:\Program Files\Zeus AI\zeus-backend.exe`.
- The installed backend passed `/api/health` with full-computer access enabled. The temporary source-run backend was stopped after the installed app was launched.
- Slack Socket Mode is connected using local Windows Credential Manager values. Do not request, print, commit, or train on its `xoxb-` / `xapp-` tokens.
- The Repository Map source synced 47 repositories and 47 declared summaries into `%LOCALAPPDATA%\Zeus AI\knowledge\project_docs\repository-map`. `provenance.json` records the source URLs, fetch time, and content hashes.
- The packaged desktop app now defaults to a 30-second local Knowledge watcher. It detects changes in supported knowledge folders, records status under `%LOCALAPPDATA%\Zeus AI\data\knowledge-watch`, and rebuilds the local index only when source files changed.
- The public `Summary-Of-repos-Memory-linker` repository is the canonical public project directory. Zeus uses a local searchable projection. Heartbeat Observatory renders the same manifest at `https://www.heartbeatobservatory.com/HeartbeatCenter/`.

## 2026-07-11 Verified Changes

- Fixed the native Ollama tool protocol. Zeus now preserves the assistant tool-call envelope and sends the result back as an Ollama `tool` message, which allows models such as `qwen3.5:4b` to continue after a tool call.
- Added Windows desktop tools: screen information, visible-window enumeration/focus, screenshot capture, OCR, mouse/keyboard input, and waits. These tools register when full-computer mode is enabled; the packaged desktop sidecar enables that mode.
- Live-tested a local agent request to capture the visible desktop. It called `capture_screen`, saved a local PNG, then returned a completion.
- Added persisted chat conversations with list, load, and save API endpoints and a desktop history pane.
- Rebuilt, installed, launched, and health-checked the Windows desktop app after these changes.
- Slack is connected. Read `docs/connector-handoff.md` before changing it. Do not generate, paste, commit, log, or train on Slack credentials.
- Zeus Memory is implemented locally. Read `docs/memory-and-remote-sync.md` before attempting a Heartbeat Observatory/PAM connection.
- Docker Desktop was started and the Docker images/backend/frontend smoke checks passed. The full Compose stack shares the normal `3000`/`8000` ports with a desktop-development session, so do not run both without changing one set of ports.

## Standing Direction

The user wants Zeus to become a local AI operating system, not just a renamed chat model.

Near-term direction:

1. Preserve local desktop operation.
2. Keep cloud optional.
3. Keep raw traces separate from approved training data.
4. Keep knowledge separate from behavior training.
5. Keep AI coworker handoffs explicit and repeatable.
6. Build concrete layers, verify them, document them, commit them.

AWS is available later as a training gym, not as the place Zeus lives. Do not create paid resources or upload private data without making that visible first.

## Current Verified Commands

Backend:

```powershell
.\.venv\Scripts\python.exe -m compileall backend training
.\.venv\Scripts\python.exe -m pytest backend\tests
.\.venv\Scripts\python.exe training\data\build_dataset.py
```

Frontend from the repository:

```powershell
cd frontend
npm run typecheck
npm run build
npm run desktop:build
```

Packaged smoke pattern:

1. Start `zeus-ai-desktop.exe`.
2. Check `/api/health`.
3. Execute harmless `calculate` tool.
4. Check `/api/training/candidates`.
5. Score one candidate through `/api/training/evaluate`.
6. Approve one candidate through `/api/training/review`.
7. Create a chat, reopen it from conversation history, and confirm the messages load.
8. Ask Agent to capture the currently visible desktop and confirm a local screenshot path is returned.
9. Add a memory in the Memory panel, then ask a related chat question and confirm Zeus can use the saved context.
10. Open Repository Map, confirm its 47-repository snapshot is present, and search a known project through Knowledge.
11. Confirm the Slack panel reports connected, then send a harmless DM from Slack and confirm the local response.
12. Run `docker compose up --build` with Ollama running on the host, then confirm `http://localhost:3000` and `http://localhost:8000/api/health` respond.
13. Stop `zeus-ai-desktop` and `zeus-backend`.

## Do Not Commit

- `.venv/`
- `node_modules/`
- `frontend/src-tauri/target/`
- `frontend/src-tauri/binaries/*`
- `data/tool_traces/*`
- `data/screenshots/*`
- `data/conversations/*`
- `data/instruction_examples/candidates.jsonl`
- `data/instruction_examples/approved.jsonl`
- `data/instruction_examples/rejected.jsonl`
- `data/instruction_examples/reviews.jsonl`
- `data/processed/*`
- `knowledge/*` generated/user docs except `.gitkeep` and `knowledge/README.md`
- model weights/checkpoints
- secrets or API keys
