# Zeus Memory And Heartbeat Sync

Zeus memory has two distinct jobs. They should not be collapsed into one database simply because a 3D world can visualize both.

## What Exists Now

Zeus has an inspectable local memory store at `%LOCALAPPDATA%\Zeus AI\data\memory\zeus_memory.sqlite3` in the packaged Windows app. It stores user-managed facts, preferences, decisions, project notes, instructions, and tags.

- Memory is editable and deletable in the Zeus Memory panel.
- Chat and Agent retrieve only the entries relevant to the current request.
- Chat has a visible memory toggle.
- Zeus does not automatically convert every conversation, screenshot, tool result, or Slack message into memory.
- Memory is separate from factual Knowledge/RAG and from behavior-training examples.

This is intentional. A useful assistant needs durable context, but an inspectable memory system must make it possible to see, correct, and remove what is being retrieved.

## Heartbeat Observatory Is The Right Remote Surface

Heartbeat Observatory already has a public 3D world, Vercel server functions, Supabase identity/realtime, and a drafted PAM control-plane schema. It should become an optional remote sync and visualization surface for Zeus, not a replacement for the local source of truth.

The 3D data-center/library idea can work well when each visible object has an honest link to a real record:

- a building or room represents a project, memory collection, or active Zeus instance
- shelves/terminals represent memory categories and provenance, not fictional data
- a status light represents a real sync or agent state
- selecting an object opens the actual source record and its edit/history controls

The world is the interface. The data model remains the source of truth.

## Repository Map: One Shared Project Directory

`Summary-Of-repos-Memory-linker` is the verified public directory for the account's repositories. Zeus now treats its `repos.json` manifest as an optional source adapter:

1. The Repository Map panel downloads the manifest and only its declared relative summary files.
2. Zeus writes the material under local `knowledge/project_docs/repository-map/`, with a source URL, fetch time, and SHA-256 content hash in `provenance.json`.
3. Zeus rebuilds the local knowledge index. The map is retrieval material, never automatic behavior-training data or private memory.
4. `/HeartbeatCenter/` can render the same public `repos.json` directly at runtime. Its deployment guide is already maintained by the linker repository.

This makes the linker manifest the shared public project directory. Zeus has a local cached/searchable projection; Heartbeat has a visual projection; neither needs a manually copied second inventory.

The repository map is separate from PAM device synchronization. A future PAM connector should send only explicit device status and user-authorized records to the private control plane, never publish local knowledge or private memory merely because it was indexed.

## Recommended Sync Architecture

1. Zeus writes to local SQLite first, so normal computer use still works without a network.
2. An optional desktop sync worker reads only changed memory records and sends outbound events to the PAM control plane.
3. Heartbeat/Supabase stores account-owned records protected by RLS and makes sync state visible in the world.
4. Zeus receives only its own account's remote changes, applies them locally, and records an audit receipt.
5. A conflict is surfaced as an editable record; it is never silently overwritten.

The existing Heartbeat PAM schema is already a strong base for identity, devices, threads, messages, event queues, and an action ledger. Add a dedicated `pam_memory_items` table and a change/version field before implementing synchronization. Do not repurpose public world-space rows to store private memory content.

## What Must Be Built Before Remote Sync

- A Zeus connector configuration UI with local secret storage.
- Device pairing to a PAM instance, rather than a copied database key in Zeus.
- A `pam_memory_items` migration, RLS policies, and realtime subscription design in Heartbeat Observatory.
- An outbound-event protocol with stable record IDs, revisions, timestamps, provenance, and tombstones for deletions.
- End-to-end tests for offline changes, two-device conflicts, deletes, and revocation.

No Supabase URL, service role key, user access token, Slack token, or Vercel secret belongs in this repository.

## Model Runtime Note

The Colibri project shown in the screenshots is real and demonstrates a disk-streamed 744B MoE runtime. It is an experimental C inference engine, not a compatible replacement for the Ollama API Zeus currently uses. Keep Zeus runtime-agnostic: Ollama remains the supported local adapter today, and a future Colibri adapter should be added only after it can satisfy Zeus's chat, streaming, and tool-call contracts.
