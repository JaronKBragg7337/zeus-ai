# Zeus AI Desktop Automation Roadmap

This document captures the direction for Zeus beyond the first local workbench.

## Product Direction

Zeus should become a desktop AI operator that can work across the user's computer, local files, local models, optional APIs, and optional connectors.

The initial principle is visibility before policy:

- Show what Zeus can access.
- Log what Zeus does.
- Let the user decide what limits, approvals, or policies belong in their setup.
- Include an emergency stop so the user can halt automation quickly.

## Capability Goals

1. Desktop app
   - Native Windows app through Tauri.
   - Reuse the existing React interface.
   - Bundle the Python/FastAPI backend as a sidecar in a later packaging step.

2. Full-computer use
   - Support all local drives when `ZEUSAI_FULL_COMPUTER_ACCESS=1`.
   - Keep local action logs.
   - Completed first Windows tool layer: windows, screenshots, OCR, mouse, keyboard, and waits.
   - Add a visible desktop settings screen for access mode and runtime status.

3. Automatic work
   - Watch selected folders or all local roots for new files.
   - Build a local index automatically.
   - Summarize, classify, search, or retrieve from local data.
   - Show what happened in an action timeline.

4. Kill switch
   - Stop future tool execution.
   - Halt running agent loops between steps.
   - Log kill/resume events.
   - Later: terminate active subprocesses spawned by Zeus.

5. APIs and connectors
   - Local-only remains the default.
   - Optional API keys can enable cloud providers or external tools.
   - First detailed handoff is `docs/connector-handoff.md` for Slack Socket Mode.
   - Connector model should support MCP-style tools, local plugins, and authenticated APIs.
   - Secrets must be user-supplied and stored outside Git.

6. Research what people want
   - After the desktop/control foundation is working, research likely users:
     - local AI users
     - creators
     - developers
     - small business operators
     - people with messy files/data
     - people who need private automation
   - Turn findings into a prioritized roadmap.

## Near-Term Technical Steps

1. Add a desktop settings panel for:
   - full-computer access
   - shell enablement
   - command risk policy
   - audit log viewer
   - kill/resume status

2. Package backend as a sidecar:
   - build Python backend with PyInstaller
   - start it from Tauri
   - stop it when the desktop app exits

3. Add file watcher/indexer:
   - start with explicit folders
   - add full-computer mode
   - skip only what the user chooses to skip
   - log indexing events

4. Add connector foundation:
   - local connector registry
   - API key storage plan
   - MCP adapter plan
   - per-connector action logs

5. Add game-test run recording:
   - task/request and selected target window
   - ordered desktop actions and observations
   - linked local screenshots
   - final outcome and reviewer label
   - keep raw runs separate from approved training data
