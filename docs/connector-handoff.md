# Connector Handoff

This document is the starting point for an AI coworker or developer adding an external Zeus connector. It records the real current state as of 2026-07-11.

## Current State

- Zeus runs locally as a FastAPI backend with a React/Tauri desktop shell.
- The packaged Windows app can use local desktop tools, local files, local Ollama models, RAG, and local conversation history.
- There is no connector framework, Slack client, token storage implementation, background service, or inbound/outbound message route in the repository yet.
- A Slack app can be created and installed in a workspace separately, but that does not connect Zeus until the code below exists and local credentials are configured.

## First Connector: Slack

The intended first mobile communication path is a Slack bot. Once it is installed in the user's workspace, Slack's mobile app can deliver Zeus messages to the user's phone and receive direct messages for Zeus.

Use Slack Socket Mode for the first implementation. It allows a local Zeus process to receive Slack events without exposing a public web server or opening an inbound firewall port.

### Required Slack Configuration

Perform these in the Slack app configuration only when the owner is ready to authorize them:

1. Enable Socket Mode and create an app-level token with `connections:write`.
2. Add bot OAuth scopes: `chat:write`, `im:read`, and `im:history`.
3. Subscribe to the `message.im` bot event.
4. Install or reinstall the app to the target workspace.
5. Store the bot token and app-level token locally, outside the repository.

Do not place token values, client secrets, signing secrets, copied Slack event bodies, workspace exports, screenshots, or user messages in Git, docs, test fixtures, logs, or training candidates.

### Recommended Implementation Shape

1. Add a small connector registry so optional connectors can report `disabled`, `configuring`, `connected`, or `error` without affecting local Zeus when not configured.
2. Add a Slack Socket Mode worker that starts in the FastAPI lifecycle only when local Slack credentials exist.
3. Route inbound direct messages to a local Zeus task/conversation record. Persist an inbound/outbound audit event with secret-safe metadata only.
4. Add a `send_slack_message` capability for explicit Zeus updates. The destination should be an owner-selected direct-message channel or user ID, not a hardcoded workspace/user value.
5. Add a desktop Connector Settings panel that shows status and accepts configuration without displaying stored secrets after entry.
6. Keep continuous operation separate from app startup. Socket Mode can receive events while Zeus is running; receiving messages while the desktop app is closed requires an explicit always-running user service or scheduled task.

## Secret Handling

Secrets are compatible with an open-source Zeus repository when they remain local. A connector implementation should use one of these local-only mechanisms:

- Windows Credential Manager through a maintained library such as `keyring`.
- Environment variables supplied at process launch.
- A user-owned local secrets file excluded by `.gitignore`.

The connector must never include secret values in API responses, audit logs, tool result text, training captures, exception messages, or UI state.

## Verification Plan

Before real Slack credentials are used:

1. Unit-test disabled configuration and redaction behavior with fake token-shaped values.
2. Unit-test inbound/outbound message routing with a mocked Slack client.
3. Run backend tests and frontend typecheck/build.
4. With owner authorization, connect to one test direct message and verify an inbound message becomes a local conversation event.
5. Send one explicit test reply, verify it reaches Slack mobile, and verify no credential appears in Zeus logs or Git status.

## Non-Goals For The First Connector

- Publishing Zeus to the public Slack Marketplace.
- Running Zeus while the computer is shut down.
- Giving an external service blanket access to the local desktop.
- Treating ordinary Slack messages as approved model-training examples.

## Suggested Next Task

Create `Z-017` in `docs/handoff/TASK_LEDGER.md` and implement the connector registry plus secret-safe local configuration before generating Slack tokens or installing any Slack permissions.
