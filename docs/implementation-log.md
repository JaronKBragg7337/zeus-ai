# Implementation Log

This file is a human-readable build trail. It should be updated when Zeus gains a meaningful capability.

Generated action logs and training traces live elsewhere. This log is for decisions, verification, and repeatability.

## 2026-07-11 - Native Tool Continuation, Desktop Control, and Conversation History

Goal:
Make the installed Windows app complete desktop-oriented multi-step tasks, retain chat threads, and give future contributors an accurate handoff.

What changed:

- Corrected the Ollama tool-call conversation protocol in both agent and chat loops. After a model returns `assistant.tool_calls`, Zeus now appends that assistant message and returns each tool result with `role: tool` and `tool_name` before asking the model for the next step.
- Added Windows desktop primitives in `backend/desktop_control.py` and registered them behind full-computer mode: screen information, visible-window enumeration/focus, screenshot capture, OCR, mouse control, clicks, typing, hotkeys, and waits.
- Added local conversation storage and `GET/POST /api/conversations` endpoints.
- Added a chat-history pane that lists, saves, and reloads local conversations.
- Updated `.gitignore` so local screenshots cannot be staged accidentally.
- Added `docs/connector-handoff.md` and refreshed the handoff files to make Slack/mobile work an explicit, secret-safe next task.

Verification:

- `python -m compileall backend`
- `python -m pytest backend\\tests -q` -> 23 passed
- `pnpm typecheck`
- `pnpm build`
- `pnpm desktop:build`
- Installed the generated MSI, launched Zeus AI, checked backend health, and checked the conversation endpoint.
- Ran a live local `qwen3.5:4b` agent task that called `capture_screen`, saved a local PNG, and then returned a completion.

Current limitation:

The desktop layer is working Windows automation, not robust game understanding or browser DOM control. Training Review still captures individual tool-level candidates; it does not yet create a curated multimodal game-test trajectory. Slack/mobile communication is documented but not implemented or authorized.

Follow-up:

- Implement Z-017 connector registry and Slack Socket Mode using secret-safe local configuration.
- Implement Z-018 game-test run records with linked screenshots/actions/outcomes.
- Add browser automation and a desktop settings surface.

## 2026-07-01 - Desktop Sidecar Packaging

Goal:
Build Zeus as a Windows desktop app that starts its backend automatically.

What changed:

- Added Tauri desktop shell.
- Added PyInstaller backend sidecar build script.
- Added Tauri sidecar lifecycle handling.
- Desktop build now produces `.exe`, `.msi`, and NSIS installer.

Verification:

- Backend tests passed.
- Frontend build/typecheck passed.
- Tauri build passed.
- Packaged app launched and backend responded.

Follow-up:

- Replace local HTTP with a native bridge later if product direction requires no visible local-port architecture.

## 2026-07-01 - Zeus Local Capability Identity

Goal:
Stop Zeus from answering like a generic hosted chatbot.

What changed:

- Added Zeus-specific system prompt.
- Chat tools enabled by default.
- Desktop sidecar enables shell tool.
- Backend health reports shell/native model status.

Verification:

- Backend tests passed.
- Desktop build passed.
- Packaged backend reported full file access and shell enabled.

Follow-up:

- Add Windows UI/screen automation connector for true computer-use actions.

## 2026-07-01 - Zeus-Native Tiny Model Track

Goal:
Create the first path toward Zeus-owned weights instead of only Qwen/Ollama.

What changed:

- Added `training/` pipeline.
- Added local dataset builder.
- Added simple tokenizer trainer.
- Added from-scratch tiny transformer training script.
- Added local Zeus-Tiny inference script.
- Added `ZEUSAI_NATIVE_MODEL=1` backend switch.

Verification:

- Backend/training syntax checks passed.
- Backend tests passed.
- Seed dataset built.
- Tokenizer trained.
- Tiny smoke training produced local weights.
- Tiny inference generated local text from Zeus-Tiny weights.

Follow-up:

- Add review/curation flow for training examples.
- Train specialist models for routing, memory classification, and tool-call formatting.

## 2026-07-01 - Automatic Training Capture

Goal:
Turn real Zeus usage into local Zeus-Tiny training examples.

What changed:

- Added training capture module.
- Captures tool calls, agent runs, chat completions, corrections, and successful completions.
- Writes generated JSONL under local data folders.
- Packaged desktop writes persistent data under `%LOCALAPPDATA%\Zeus AI\data`.

Verification:

- Backend/training syntax checks passed.
- Backend tests passed.
- Dataset builder consumed generated capture files.
- Desktop package rebuilt.
- Packaged desktop tool call wrote traces to app-data.

Follow-up:

- Add local review UI before training on captured data.
- Add scoring labels for good/bad examples.

## 2026-07-01 - Training Review Queue and Knowledge Lane

Goal:
Keep Zeus learning from real usage without treating every trace as a positive training example.

What changed:

- Captured behavior examples now land in `data/instruction_examples/candidates.jsonl`.
- Added training review API endpoints for pending candidates and approval/rejection.
- Added a desktop Training Review panel.
- Approved examples move to `data/instruction_examples/approved.jsonl`.
- Rejected examples and review records stay local for debugging and future evaluator training.
- Dataset builder now trains on seed plus approved examples by default.
- Added `knowledge/` as a separate lane for factual docs, manuals, research, books, code docs, and generated indexes.

Verification:

- Pending tool-use candidates are created during local tool execution.
- Approved candidates are appended to the approved training set.
- Dataset builder avoids raw traces and pending candidates unless explicitly opted in.

Follow-up:

- Add quality labels and evaluator training for failed/corrected examples.
- Add local knowledge indexing that feeds RAG without changing model behavior.

## 2026-07-01 - Knowledge Index and Evaluator Data

Goal:
Give Zeus a local factual knowledge lane and a separate scoring/evaluator lane.

What changed:

- Added local knowledge indexer under `backend/knowledge_index.py`.
- Added knowledge status, rebuild, and search API endpoints.
- Added desktop Zeus Knowledge panel.
- Added evaluator seed examples under `data/evaluator_examples/seed.jsonl`.
- Added `training/data/build_evaluator_dataset.py`.
- Tightened tokenizer training so pending/rejected instruction examples are not swept into the tokenizer by default.
- Updated docs and handoff files for the new lanes.

Verification:

- Backend/training syntax checks passed.
- Backend tests passed.
- Default behavior dataset built from seed plus approved examples.
- Evaluator dataset built from seed/review/correction sources.
- Frontend typecheck passed.
- Frontend production build passed.

Follow-up:

- Add semantic embeddings as an optional local-only upgrade for Zeus Knowledge.
- Add a trained Zeus evaluator model once enough reviewed data exists.
- Add a first-run desktop setup screen for knowledge folders and training-data policy.

## 2026-07-01 - Zeus Evaluator v1

Goal:
Train Zeus to score whether a candidate example should be learned from.

What changed:

- Added `backend/evaluator_model.py` runtime.
- Added `POST /api/training/evaluate`.
- Added `training/evaluator/train_evaluator_v1.py`.
- Added `training/evaluator/score_candidate.py`.
- Added ignored local model path `models/zeus-evaluator-v1/evaluator.json`.
- Added a Score button/result to the Training Review panel.

Verification:

- Backend test covers local evaluator scoring through the API.
- Evaluator dataset builds locally.
- Evaluator v1 trains locally from approved/rejected/corrected examples.

Follow-up:

- Add automatic evaluator scoring beside each pending candidate in the review UI.
- Retrain evaluator after enough real approved/rejected/corrected examples exist.
- Later replace the linear evaluator with a Zeus-native neural evaluator if data volume justifies it.

## 2026-07-01 - Fix agent tool calls + architecture review + product framing

Agent/tool used: Claude Cowork (Fable 5)

Goal:
Fix reported "Zeus agent not working," review the knowledge/training lanes
(Z-004), and write market + product framing (Z-006).

What changed:

- Fixed agent mode dropping native Ollama tool calls. Tool-capable models
  (qwen) return message.tool_calls with empty content; the agent only read
  content and ended tasks instantly with an empty message. Added chat_once
  usage + `_extract_native_tool_call` with a text-parse fallback, plus an
  explicit error when a response is genuinely empty.
- Added `backend/tests/test_basic.py` cases for native tool-call extraction.
- Added `docs/reviews/2026-07-01-architecture-review.md` (findings F-1..F-5;
  F-1 = replace calculate eval() with an AST evaluator).
- Added `docs/product/market-and-vision.md` (market map, L0-L5 layered vision,
  recommended product order: folder-watch/index -> inspectable memory).
- Updated TASK_LEDGER: Z-004 and Z-006 done; added Z-011..Z-013.

Commands run:

- .venv\Scripts\python.exe -m compileall backend  (OK)
- .venv\Scripts\python.exe -m pytest backend\tests  (20 passed)
- Live: POST /api/agent "compute 17*23" -> tool_call calculate -> 391

Outcome:
Agent works end to end on the LLM path. Fix committed (aee4559) and pushed.
Desktop app rebuilt so the installed app carries the fix.

Follow-up:
Z-011 apply review findings (F-1 first), Z-012 folder-watch + auto-index,
Z-013 inspectable memory panel.
