# Zeus Task Ledger

This is the first place a new AI coworker should check for active work.

Status keys:

- `todo`
- `doing`
- `blocked`
- `done`

## Active Tasks

| ID | Status | Owner Role | Task | Notes |
| --- | --- | --- | --- | --- |
| Z-001 | done | Codex 5.5 | Add local knowledge indexing and search | Added backend endpoints and desktop Knowledge panel. |
| Z-002 | done | Codex 5.5 | Add evaluator/scoring dataset generation from reviewed examples | Added seed evaluator data and dataset builder. |
| Z-003 | done | Codex 5.5 | Make Zeus-Tiny training path clearly consume approved examples | Tightened dataset/tokenizer path around seed + approved examples. |
| Z-004 | done | Claude Cowork Fable | Architecture review for knowledge/index/training boundaries | See docs/reviews/2026-07-01-architecture-review.md. Fixed agent tool-call bug found during review. |
| Z-005 | todo | Claude Cowork Opus | Risk and scaling critique for AWS training-gym plan | No cloud resources until user explicitly decides. |
| Z-006 | done | Fable 5 | Product framing and founder-system narrative | See docs/product/market-and-vision.md. Market map + layered L0-L5 vision. |
| Z-011 | todo | Codex 5.5 | Apply review findings F-1..F-5 | F-1 (replace calculate eval with AST) is highest priority. |
| Z-012 | todo | Codex 5.5 | Build L2 folder-watch + auto-index | Top product move: removes manual upload, answers desktop vision. |
| Z-013 | todo | Codex 5.5 | Build L3 inspectable memory panel | Biggest market differentiator per Z-006 research. |
| Z-007 | todo | Claude Code Sonnet | Independent code review after local indexing lands | Focus on bugs, tests, packaging. |
| Z-008 | todo | Codex 5.5 | Package and smoke-test final desktop build | Needed after Knowledge panel and backend endpoints are committed. |
| Z-009 | done | Codex 5.5 | Add Evaluator v1 local scorer | Trains from approved/rejected/corrected examples and scores candidates through API/UI. |
| Z-010 | todo | Codex 5.5 | Surface evaluator score automatically in review queue | Current UI scores on button press. |
| Z-014 | done | Codex | Preserve native Ollama tool-call context across multi-step chat and agent runs | Verified live with `qwen3.5:4b` calling `capture_screen` then completing. |
| Z-015 | done | Codex | Add Windows desktop observation/control and package it | Installed app exposes screen, window, OCR, mouse, keyboard, and wait tools in full-computer mode. |
| Z-016 | done | Codex | Persist and reopen desktop chat conversations | Added local conversation API and history pane; records are ignored by Git. |
| Z-017 | done | Codex | Add Slack Socket Mode integration | Local Credential Manager storage, status panel, inbound DM conversation/reply flow, and secret-safe logs are implemented. |
| Z-018 | todo | Desktop/game automation implementer | Build game-testing run recorder | Group screenshots, tool actions, observations, and outcomes into reviewable runs; do not label raw captures as training-ready automatically. |
| Z-019 | done | Codex | Add local inspectable memory | Added user-managed SQLite memory, UI, retrieval for Chat/Agent, and tests. |
| Z-020 | doing | Release automation | Validate native macOS and Linux desktop packages in GitHub Actions | Native runner workflow added; results must be checked after it runs. |
| Z-021 | todo | Zeus + Heartbeat implementer | Add PAM memory sync and honest world visualization | Read `docs/memory-and-remote-sync.md`; add schema/device pairing before a remote connector. |
| Z-022 | done | Codex | Add first provenance-tagged source adapter | Repository Map imports a configurable public manifest plus declared summaries into local Knowledge with hashes, source URLs, and fetch timestamps. |
| Z-027 | todo | Platform implementer | Generalize source-adapter registry | Expand the tested Repository Map pattern to browser, GitHub, Reddit, and Heartbeat/PAM adapters. |
| Z-023 | todo | Runtime implementer | Add a runtime capability evaluation harness | Treat Ollama, Zeus-Tiny, and future engines as adapters measured against Zeus-owned contracts. |
| Z-024 | done | Codex | Add local Zeus Heartbeat service and panel | Timer creates logged local observations and curiosity tasks while Zeus runs. |
| Z-025 | todo | Background-runtime implementer | Run Zeus Heartbeat while desktop UI is closed | Requires a separate installed background worker/service with explicit lifecycle management. |
| Z-026 | todo | Slack connector implementer | Add proactive update destination and background Slack service | The current Socket Mode connector runs while Zeus is open. |

## Current User Priorities

1. Zeus should be a real local desktop app.
2. Zeus should have full-computer capability with logs and a kill switch.
3. Zeus should learn from real use, but with review before training.
4. Zeus should have separate local knowledge storage/indexing.
5. Zeus should eventually train Zeus-owned model weights.
6. The repo should document the build method so others can repeat it.
7. Zeus should communicate with the user through an optional Slack/mobile connector while it is running, without putting credentials in Git.
8. The repository must reflect verified current behavior, known gaps, and handoff-ready next steps.

## Handoff Rule

When a task changes status, update this file and `docs/implementation-log.md`.
