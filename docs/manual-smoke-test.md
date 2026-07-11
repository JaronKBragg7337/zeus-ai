# Manual Smoke Test

Use this checklist after backend and frontend dependencies are installed.

## Start Services

```powershell
.\.venv\Scripts\python.exe backend\main.py
```

```powershell
cd frontend
npm run dev
```

Open `http://localhost:3000`.

## Workflows

1. Models
   - Open the Models panel.
   - Confirm `llama3.2:3b` or `qwen3.5:4b` appears.
   - Select one model.

2. Chat
   - Open Chat.
   - Send `Reply with one short sentence saying the local model works.`
   - Confirm a streamed response appears.

3. Files
   - Open Files.
   - Confirm the repo root is listed.
   - Open `README.md`.
   - Confirm browsing outside allowed roots is blocked by the backend.

4. RAG
   - Create a small `.txt` file with a unique phrase.
   - Upload it in Documents using collection `smoke`.
   - Query for the unique phrase.
   - Confirm the retrieved passage includes the uploaded text.

5. Agent
   - Open Agent.
   - Set Project path to `.`.
   - Ask it to list the files in the current project folder.
   - Confirm it uses constrained local file tools. Shell execution should stay disabled unless explicitly enabled.

6. Desktop tools (Windows full-computer mode)
   - In Agent, ask: `Capture a screenshot of the currently visible desktop and report the saved file path.`
   - Confirm the run calls `capture_screen` and returns a local PNG path.
   - Confirm the PNG is saved under the configured Zeus data directory, not in the repository's tracked files.

7. Conversation history
   - Send a short chat message.
   - Start a new conversation, then reopen the saved thread from the history pane.
   - Confirm the earlier messages load and that the active conversation remains after an app restart.

8. No Cloud APIs
   - Confirm no API key or secret is required.
   - Confirm model calls go through local Ollama.
