# Zeus: Market Map and Product Framing

Date: 2026-07-01
Author: Claude Cowork (Fable 5), covering ledger task Z-006
Purpose: capture what people want from local AI, where the field is weak, and
how Zeus can be more than "a renamed chat model."

## The one-line framing

Most local-AI tools are a *chat window over a model*. Zeus is aiming to be a
*local operator with memory that takes real actions on your machine, with logs
and a kill switch*. That gap is the whole opportunity.

## What people actually want (from 2026 research)

Four demand signals show up repeatedly across comparisons and user writeups:

1. **Privacy and control by architecture, not policy.** Sensitive data never
   leaving the device removes compliance risk instead of promising to manage
   it. This is the reason people run local at all.

2. **Cost at volume.** A pipeline doing millions of tokens/day runs into real
   cloud bills; a local box pays for itself at moderate volume. Local is an
   infrastructure decision now, not a hobby.

3. **Persistent personal memory.** The loudest complaint about every assistant
   (including hosted Claude/ChatGPT) is that they are "brilliant amnesiacs" —
   every session starts from zero, stored memory is small, opaque, and
   unreliable for real work.

4. **Actually taking actions.** Today's assistants "can't act on memory without
   being asked." People want something that watches their work, keeps context,
   and does things — file I/O, shell, scheduling — not just answers.

## Where the existing tools stop

- **LM Studio** — best model-discovery + local inference server, single-user,
  no memory, no actions.
- **Ollama** — the runtime everyone builds on (Zeus included), not an app.
- **Open WebUI** — most active ecosystem, function calling + RAG, but it's a
  chat UI; it doesn't own your machine or persist a personal memory of you.
- **AnythingLLM** — good document RAG, but "built around workspaces, not around
  you," and the desktop version is a feature-subset of the server.
- **Across all of them:** "Neither builds persistent personal memory or takes
  real-world actions." Single-user, chat-shaped, forgetful.

That sentence is Zeus's product thesis stated by the market.

## Zeus's defensible position

Zeus already has, in the repo today, the three things the field is missing:

- **Actions:** local tools + agent loop + optional full-computer access.
- **Accountability:** append-only audit log + kill switch + risk policy.
- **A learning loop:** capture -> review -> approve -> train, kept separate
  from a retrieval knowledge lane.

No mainstream local tool ships all three. That is the wedge.

## "More than Zeus" — the layered vision

Think of Zeus in layers, each usable on its own and each a possible product:

- **L0 Runtime** — Ollama/Qwen now, Zeus-Tiny later. Swappable.
- **L1 Workbench** — the current app: chat, models, files, RAG, agent. Done.
- **L2 Operator** — folder watching + auto-index, scheduled/background tasks,
  full-computer actions, all logged. This is the next real build.
- **L3 Memory** — a persistent, inspectable, editable memory of the user and
  their projects. The feature the whole market is failing at. High priority.
- **L4 Founder System** — intent -> project -> tasks -> build -> verify ->
  package -> document -> promote. The blueprint already in the repo.
- **L5 Platform** — connectors (MCP), optional user-supplied API keys, and a
  path to multi-user / shareable app for other people.

The user's stated goal — full computer use, does more over time, acts
automatically but logs, optional APIs and MCP connectors — maps exactly onto
L2 + L3 + L5. The research says that is also what the broader market wants.

## Recommended next moves (product order)

1. **Ship L2 folder-watch + auto-index.** Turns "I have to upload files" into
   "Zeus already knows my folders." Directly answers the user's desktop-vs-
   localhost point and a top market complaint.
2. **Build L3 inspectable memory** as a first-class panel: what Zeus knows
   about you, editable, with provenance. This is the single biggest
   differentiator versus every tool listed above.
3. **Keep the kill switch + audit visible in the UI** as the trust story that
   makes "full computer use" acceptable to other users later.
4. **Expose MCP connectors as optional** so power is opt-in, not required.

## Positioning statements to test

- "The local AI that remembers you and does the work — on your machine, with a
  log of everything and an off switch."
- "Not a chat window. An operator."
- "Your files, your model, your memory. Nothing leaves the machine unless you
  say so."

## Sources

- Top 20 tools to run LLMs locally in 2026 (iunera)
- Local AI platforms on Mac compared 2026 (ModelPiper)
- Open WebUI vs AnythingLLM (wz-it, localaimaster, openwebui docs)
- Local AI vs Cloud AI in 2026 (MindStudio)
- The On-Device Agent Era 2026 (Digital Applied)
- Best personal AI assistants with memory 2026 (Vellum)
- Why your AI assistant forgets everything (dev.to)
