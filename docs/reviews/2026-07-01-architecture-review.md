# Architecture Review: Knowledge / Index / Training Boundaries

Date: 2026-07-01
Reviewer: Claude Cowork (Fable 5), covering ledger task Z-004
Scope: backend/training_capture.py, knowledge_index.py, evaluator_model.py, tools.py, agent.py

## Verdict

The lane separation is sound and worth keeping:

- raw traces (tool_traces/*.jsonl) are append-only and separate from
- candidate examples (instruction_examples/candidates.jsonl), which require
- human review (reviews.jsonl -> approved/rejected) before training, while
- knowledge (retrieval index) never feeds behavior training directly.

This matches the stated design and is the right shape for a training flywheel.

## Bug fixed during this review

Agent mode dropped native Ollama tool calls. Tool-capable models (qwen)
return `message.tool_calls` with empty `content`; the agent only read
`content`, so every LLM-path agent task ended instantly with an empty
result. Fixed in commit `aee4559` (chat_once + _extract_native_tool_call,
plus an explicit error message for genuinely empty responses).

## Findings for Codex (ordered by priority)

### F-1: `calculate` tool uses Python eval (fix soon)

`_calculate` runs `eval()` with emptied builtins. That sandbox is escapable
with standard tricks (`().__class__.__mro__...`), which makes `calculate`
an unlabeled second shell that bypasses `ZEUSAI_ENABLE_SHELL` and the
command risk policy. Zeus already has a real shell tool behind the user's
chosen policy switch, so nothing is gained by leaving this open. Replace
eval with an AST-based math evaluator (ast.parse + whitelisted node types
+ math functions). No capability is lost; the tool becomes honest and the
audit trail stays meaningful.

### F-2: Correction detection over-triggers

`_looks_like_correction` markers include "no " and "actually", so casual
messages ("no worries", "actually that was great") get captured as
user-correction training candidates. This pollutes the candidate lane the
evaluator later learns from. Tighten markers or require the message to
reference the prior assistant turn.

### F-3: Every chat auto-becomes a "success" candidate

capture_chat_completion labels all chat completions status=success. The
review queue will fill with low-value candidates and the seeded evaluator
will drift toward approving everything. Consider capturing chat only on
explicit user signal (thumbs-up, correction, or agent-completed task) or
add a sampling rate.

### F-4: Scaling notes (fine today, plan for later)

- candidates.jsonl / knowledge index are fully re-read on every request
  (O(n) per API call). Fine at current volume; move to SQLite or an
  in-memory cache with mtime check when files grow past ~50 MB.
- knowledge search is bag-of-words cosine. Good enough as fallback; the
  planned optional local embedding upgrade remains the right next step.
- RAG engine and knowledge index are two parallel retrieval systems.
  Eventually consolidate so panels share one retrieval API.

### F-5: run_command hard risk-list is cosmetic

The `dangerous` substring list catches almost nothing an actual mistake
would produce (case, quoting, PowerShell aliases). Since the user has
explicitly chosen log-first policy, do not grow the blocklist; instead
make the audit log the strong guarantee: log cwd, exit code, and a hash
of stdout so actions are reconstructable. The kill switch already covers
the emergency path.

## What is good and should not be churned

- Kill switch is checked at both tool-execution and agent-loop level.
- Redaction of sensitive keys before anything is written to disk.
- Desktop data lives under %LOCALAPPDATA%\Zeus AI, separate from repo.
- Reviews are append-only and candidates are immutable once reviewed.
