"""Optional local Slack Socket Mode connector for Zeus."""
from __future__ import annotations

import asyncio
import time
from typing import Any

from audit_log import append_action
from conversation_store import get_conversation, save_conversation
from memory_store import memory_context
from ollama_client import ollama
from prompts import build_zeus_system_prompt
from secret_store import SLACK_APP_TOKEN, SLACK_BOT_TOKEN, delete_secret, get_secret, set_secret


class SlackConnector:
    def __init__(self) -> None:
        self._app: Any = None
        self._handler: Any = None
        self._lock = asyncio.Lock()
        self._state: dict[str, Any] = {"state": "not_configured", "detail": "Slack credentials have not been saved locally.", "connected_at": None}

    def status(self) -> dict[str, Any]:
        bot_present = bool(get_secret(SLACK_BOT_TOKEN))
        app_present = bool(get_secret(SLACK_APP_TOKEN))
        return {
            **self._state,
            "bot_token_saved": bot_present,
            "app_token_saved": app_present,
            "configured": bot_present and app_present,
        }

    async def configure(self, *, bot_token: str | None = None, app_token: str | None = None) -> dict[str, Any]:
        if bot_token:
            _validate_token(bot_token, "xoxb-")
        if app_token:
            _validate_token(app_token, "xapp-")
        if bot_token:
            set_secret(SLACK_BOT_TOKEN, bot_token)
        if app_token:
            set_secret(SLACK_APP_TOKEN, app_token)
        await self.restart()
        append_action({"type": "connector", "connector": "slack", "action": "configure", "bot_token_saved": bool(bot_token), "app_token_saved": bool(app_token)})
        return self.status()

    async def clear(self) -> dict[str, Any]:
        await self.stop()
        delete_secret(SLACK_BOT_TOKEN)
        delete_secret(SLACK_APP_TOKEN)
        self._state = {"state": "not_configured", "detail": "Slack credentials were removed from local Credential Manager.", "connected_at": None}
        append_action({"type": "connector", "connector": "slack", "action": "clear"})
        return self.status()

    async def start(self) -> None:
        async with self._lock:
            if self._handler:
                return
            bot_token = get_secret(SLACK_BOT_TOKEN)
            app_token = get_secret(SLACK_APP_TOKEN)
            if not bot_token or not app_token:
                self._state = {"state": "not_configured", "detail": "Save both Slack tokens locally to connect.", "connected_at": None}
                return
            try:
                from slack_bolt.app.async_app import AsyncApp
                from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

                # Socket Mode receives authenticated envelopes over Slack's WebSocket,
                # not inbound HTTP requests, so no signing secret is required here.
                app = AsyncApp(
                    token=bot_token,
                    signing_secret="socket-mode-no-http",
                    request_verification_enabled=False,
                )

                @app.event("message")
                async def direct_message(event: dict[str, Any]) -> None:
                    await self._handle_direct_message(event)

                handler = AsyncSocketModeHandler(app, app_token)
                await handler.connect_async()
                self._app = app
                self._handler = handler
                self._state = {"state": "connected", "detail": "Slack Socket Mode is connected.", "connected_at": _timestamp()}
                append_action({"type": "connector", "connector": "slack", "action": "connected"})
            except Exception as error:
                self._app = None
                self._handler = None
                self._state = {"state": "error", "detail": f"Slack connection failed: {type(error).__name__}", "connected_at": None}
                append_action({"type": "connector", "connector": "slack", "action": "connection_error", "error_type": type(error).__name__})

    async def stop(self) -> None:
        async with self._lock:
            handler, self._handler = self._handler, None
            self._app = None
            if handler:
                try:
                    await handler.close_async()
                except Exception:
                    pass
            if self._state.get("state") == "connected":
                self._state = {"state": "stopped", "detail": "Slack connector stopped.", "connected_at": None}

    async def restart(self) -> None:
        await self.stop()
        await self.start()

    async def send_message(self, channel: str, text: str) -> dict[str, Any]:
        if not self._app:
            raise RuntimeError("Slack is not connected.")
        response = await self._app.client.chat_postMessage(channel=channel, text=text)
        append_action({"type": "connector", "connector": "slack", "action": "send_message", "channel": channel, "characters": len(text)})
        return {"ok": bool(response.get("ok")), "channel": response.get("channel"), "ts": response.get("ts")}

    async def _handle_direct_message(self, event: dict[str, Any]) -> None:
        if event.get("channel_type") != "im" or event.get("bot_id") or event.get("subtype"):
            return
        text = str(event.get("text") or "").strip()
        channel = str(event.get("channel") or "")
        user = str(event.get("user") or "")
        if not text or not channel:
            return

        reply = await self._reply(text)
        if self._app:
            await self._app.client.chat_postMessage(channel=channel, text=reply)
        self._save_dm(channel, text, reply)
        append_action({"type": "connector", "connector": "slack", "action": "direct_message", "channel": channel, "user": user, "inbound_characters": len(text), "outbound_characters": len(reply)})

    async def _reply(self, text: str) -> str:
        messages = [{"role": "system", "content": build_zeus_system_prompt(tools_enabled=False) + "\n\nYou are replying through a Slack direct message. Keep the response concise and useful."}]
        saved_memory = memory_context(text)
        if saved_memory:
            messages.append({"role": "system", "content": "Relevant saved Zeus memory:\n" + saved_memory})
        messages.append({"role": "user", "content": text})
        chunks = []
        async for chunk in ollama.chat(messages, model="qwen3.5:4b", stream=True, temperature=0.6, tools=None):
            chunks.append(chunk)
        return "".join(chunks).strip() or "I received your message, but the local model did not return a response."

    def _save_dm(self, channel: str, inbound: str, outbound: str) -> None:
        conversation_id = f"slack-{channel.replace('-', '_')}"
        current = get_conversation(conversation_id) or {}
        messages = list(current.get("messages", []))
        now = _timestamp()
        messages.extend([
            {"role": "user", "content": inbound, "timestamp": now},
            {"role": "assistant", "content": outbound, "timestamp": _timestamp()},
        ])
        save_conversation(conversation_id, "Slack direct messages", messages)


def _validate_token(value: str, prefix: str) -> None:
    if not value.strip().startswith(prefix):
        raise ValueError(f"Expected a Slack token starting with {prefix}")


def _timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


slack_connector = SlackConnector()
