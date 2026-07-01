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
| Z-004 | todo | Claude Cowork Sonnet | Architecture review for knowledge/index/training boundaries | Review after Codex implementation lands. |
| Z-005 | todo | Claude Cowork Opus | Risk and scaling critique for AWS training-gym plan | No cloud resources until user explicitly decides. |
| Z-006 | todo | Fable 5 | Product framing and founder-system narrative | Fable maintains global state, handoff clarity, demos, promotion. |
| Z-007 | todo | Claude Code Sonnet | Independent code review after local indexing lands | Focus on bugs, tests, packaging. |
| Z-008 | todo | Codex 5.5 | Package and smoke-test final desktop build | Needed after Knowledge panel and backend endpoints are committed. |

## Current User Priorities

1. Zeus should be a real local desktop app.
2. Zeus should have full-computer capability with logs and a kill switch.
3. Zeus should learn from real use, but with review before training.
4. Zeus should have separate local knowledge storage/indexing.
5. Zeus should eventually train Zeus-owned model weights.
6. The repo should document the build method so others can repeat it.

## Handoff Rule

When a task changes status, update this file and `docs/implementation-log.md`.
