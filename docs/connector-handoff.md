# Connector Handoff

This document is the starting point for an AI coworker or developer adding an external Zeus connector. It records the real current state as of 2026-07-11.

## Current State

- Zeus runs locally as a FastAPI backend with a React/Tauri desktop shell.
- The packaged Windows app can use local desktop tools, local files, local Ollama models, RAG, and local conversation history.
- Zeus includes a first Slack Socket Mode connector, local Windows Credential Manager storage, a desktop Slack panel, inbound-DM handling, local conversation persistence, and a status-only connector API.
- A Slack app must still be configured and installed in a workspace separately before it can communicate with Zeus.

## First Connector: Slack

The intended first mobile communication path is a Slack bot. Once it is installed in the user's workspace, Slack's mobile app can deliver Zeus messages to the user's phone and receive direct messages for Zeus.

Use Slack Socket Mode for the first implementation. It allows a local Zeus process to receive Slack events without exposing a public web server or opening an inbound firewall port.

### Required Slack Configuration

Perform these in the Slack app configuration only when the owner is ready to authorize them:

1. Enable Socket Mode and create an app-level token with `connections:write`.
2. Add bot OAuth scopes: `chat:write`, `im:read`, and `im:history`.
3. Subscribe to the `message.im` bot event.
4. Install or reinstall the app to the target workspace.
5. In Zeus's Slack Connector panel, enter the bot token (`xoxb-`) and app-level token (`xapp-`). Zeus sends them only to its local backend, stores them in Windows Credential Manager, and clears the form values.

Do not place token values, client secrets, signing secrets, copied Slack event bodies, workspace exports, screenshots, or user messages in Git, docs, test fixtures, logs, or training candidates.

### Current Implementation

- `backend/slack_connector.py` uses Bolt for Python with the async Socket Mode handler.
- The connector starts with the local backend when both locally stored tokens exist.
- Incoming `message.im` events are stored as a local `slack-<channel>` conversation and receive a local Ollama reply without desktop tools.
- `GET /api/connectors/slack/status` reports configuration/connection state but never token values.
- The Slack panel can remove both local credentials to support rotation.

### Follow-up Implementation Shape

1. Add a general connector registry for Slack, Heartbeat/PAM, browser, and future adapters.
2. Add an owner-selected destination/channel setting for proactive Zeus updates.
3. Add user-configurable model selection and optional tool/task routing for inbound Slack DMs.
4. Keep continuous operation separate from app startup. Socket Mode can receive events while Zeus is running; receiving messages while the desktop app is closed requires an explicit always-running user service or scheduled task.

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
