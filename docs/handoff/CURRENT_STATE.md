# Zeus AI Current State

Last updated: 2026-07-11

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

Read these files first:

1. `README.md`
2. `docs/ai-coworker-protocol.md`
3. `docs/implementation-log.md`
4. `docs/handoff/TASK_LEDGER.md`
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

## 2026-07-11 Verified Changes

- Fixed the native Ollama tool protocol. Zeus now preserves the assistant tool-call envelope and sends the result back as an Ollama `tool` message, which allows models such as `qwen3.5:4b` to continue after a tool call.
- Added Windows desktop tools: screen information, visible-window enumeration/focus, screenshot capture, OCR, mouse/keyboard input, and waits. These tools register when full-computer mode is enabled; the packaged desktop sidecar enables that mode.
- Live-tested a local agent request to capture the visible desktop. It called `capture_screen`, saved a local PNG, then returned a completion.
- Added persisted chat conversations with list, load, and save API endpoints and a desktop history pane.
- Rebuilt, installed, launched, and health-checked the Windows desktop app after these changes.
- Slack is not connected yet. Read `docs/connector-handoff.md` before implementing it. Do not generate, paste, commit, log, or train on Slack credentials.

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
9. Stop `zeus-ai-desktop` and `zeus-backend`.

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
