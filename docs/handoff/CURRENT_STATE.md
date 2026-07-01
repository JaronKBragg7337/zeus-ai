# Zeus AI Current State

Last updated: 2026-07-01

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
- first Zeus-native tiny model path

GitHub repo:

```text
https://github.com/JaronKBragg7337/zeus-ai
```

Current branch:

```text
master
```

Latest known commit before this file:

```text
07a53fe Add training review queue and knowledge lane
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

## Local Build Outputs

The verified local desktop build copy is:

```text
C:\Users\lilli\.codex\local-builds\omnilocal-ai
```

Current verified Windows app outputs:

```text
C:\Users\lilli\.codex\local-builds\omnilocal-ai\frontend\src-tauri\target\release\zeus-ai-desktop.exe
C:\Users\lilli\.codex\local-builds\omnilocal-ai\frontend\src-tauri\target\release\bundle\msi\Zeus AI_0.1.0_x64_en-US.msi
C:\Users\lilli\.codex\local-builds\omnilocal-ai\frontend\src-tauri\target\release\bundle\nsis\Zeus AI_0.1.0_x64-setup.exe
```

Generated traces and app data default to:

```text
C:\Users\lilli\AppData\Local\Zeus AI\data
```

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

Frontend from local build copy:

```powershell
cd C:\Users\lilli\.codex\local-builds\omnilocal-ai\frontend
npm run typecheck
npm run build
npm run desktop:build
```

Packaged smoke pattern:

1. Start `zeus-ai-desktop.exe`.
2. Check `/api/health`.
3. Execute harmless `calculate` tool.
4. Check `/api/training/candidates`.
5. Approve one candidate through `/api/training/review`.
6. Stop `zeus-ai-desktop` and `zeus-backend`.

## Do Not Commit

- `.venv/`
- `node_modules/`
- `frontend/src-tauri/target/`
- `frontend/src-tauri/binaries/*`
- `data/tool_traces/*`
- `data/instruction_examples/candidates.jsonl`
- `data/instruction_examples/approved.jsonl`
- `data/instruction_examples/rejected.jsonl`
- `data/instruction_examples/reviews.jsonl`
- `data/processed/*`
- `knowledge/*` generated/user docs except `.gitkeep` and `knowledge/README.md`
- model weights/checkpoints
- secrets or API keys

