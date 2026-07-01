"""Ollama client for local LLM inference."""
import aiohttp
import json
from typing import AsyncIterator, List, Dict, Any, Optional

OLLAMA_BASE_URL = "http://localhost:11434"


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url

    async def chat(self, messages: List[Dict[str, str]], model: str = "qwen3.5:4b",
                   stream: bool = True, temperature: float = 0.7,
                   tools: Optional[List[Dict]] = None) -> AsyncIterator[str]:
        """Stream chat completions from Ollama."""
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {"temperature": temperature}
        }
        if tools:
            payload["tools"] = tools

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/api/chat", json=payload) as resp:
                if stream:
                    async for line in resp.content:
                        if line.strip():
                            try:
                                data = json.loads(line)
                                if "message" in data and "content" in data["message"]:
                                    content = data["message"]["content"]
                                    if content:
                                        yield content
                                elif "done" in data and data["done"]:
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    data = await resp.json()
                    content = data["message"].get("content", "")
                    if content:
                        yield content

    async def chat_once(self, messages: List[Dict[str, Any]], model: str = "qwen3.5:4b",
                        temperature: float = 0.7,
                        tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Run a single non-streaming chat request and return Ollama's raw message."""
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature}
        }
        if tools:
            payload["tools"] = tools

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/api/chat", json=payload) as resp:
                data = await resp.json()
                return data.get("message", {})

    async def generate(self, prompt: str, model: str = "qwen3.5:4b",
                       system: Optional[str] = None) -> str:
        """Generate a single response (non-streaming)."""
        payload = {"model": model, "prompt": prompt, "stream": False}
        if system:
            payload["system"] = system

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/api/generate", json=payload) as resp:
                data = await resp.json()
                return data.get("response", "")

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available Ollama models."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/tags") as resp:
                data = await resp.json()
                return data.get("models", [])

    async def pull_model(self, model_name: str) -> AsyncIterator[Dict]:
        """Pull/download a model from Ollama."""
        payload = {"model": model_name, "stream": True}
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/api/pull", json=payload) as resp:
                async for line in resp.content:
                    if line.strip():
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            continue

    async def delete_model(self, model_name: str) -> bool:
        """Delete a model from Ollama."""
        async with aiohttp.ClientSession() as session:
            async with session.delete(f"{self.base_url}/api/delete",
                                       json={"model": model_name}) as resp:
                return resp.status == 200

    async def model_info(self, model_name: str) -> Dict[str, Any]:
        """Get info about a specific model."""
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/api/show",
                                       json={"model": model_name}) as resp:
                return await resp.json()


ollama = OllamaClient()
