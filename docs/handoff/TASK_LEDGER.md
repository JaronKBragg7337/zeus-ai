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

## Current User Priorities

1. Zeus should be a real local desktop app.
2. Zeus should have full-computer capability with logs and a kill switch.
3. Zeus should learn from real use, but with review before training.
4. Zeus should have separate local knowledge storage/indexing.
5. Zeus should eventually train Zeus-owned model weights.
6. The repo should document the build method so others can repeat it.

## Handoff Rule

When a task changes status, update this file and `docs/implementation-log.md`.
