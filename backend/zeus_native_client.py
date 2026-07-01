"""Client for Zeus-native local model inference.

This path intentionally does not load Qwen, Llama, Mistral, or any other
pretrained model. It calls the local Zeus-Tiny inference script against weights
trained by the scripts under training/.
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List

from config import PROJECT_ROOT, get_native_model_dir


class ZeusNativeClient:
    def __init__(self, project_root: Path = PROJECT_ROOT):
        self.project_root = project_root
        self.infer_script = project_root / "training" / "inference" / "zeus_tiny_infer.py"

    async def chat(self, messages: List[Dict[str, Any]], model: str = "zeus-tiny",
                   stream: bool = True, temperature: float = 0.7,
                   tools: List[Dict[str, Any]] | None = None) -> AsyncIterator[str]:
        prompt = self._messages_to_prompt(messages)
        output = await self.generate(prompt, model=model, temperature=temperature)
        yield output

    async def chat_once(self, messages: List[Dict[str, Any]], model: str = "zeus-tiny",
                        temperature: float = 0.7,
                        tools: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        prompt = self._messages_to_prompt(messages)
        return {"role": "assistant", "content": await self.generate(prompt, model=model, temperature=temperature)}

    async def generate(self, prompt: str, model: str = "zeus-tiny", temperature: float = 0.7) -> str:
        model_dir = get_native_model_dir()
        if not (model_dir / "model.pt").exists() or not (model_dir / "tokenizer.json").exists():
            return (
                "Zeus native mode is enabled, but Zeus-Tiny has not been trained yet. "
                "Run `python training/data/build_dataset.py`, "
                "`python training/tokenizer/train_tokenizer.py`, and "
                "`python training/pretrain/train_zeus_tiny.py` first."
            )

        cmd = [
            sys.executable,
            str(self.infer_script),
            "--model-dir",
            str(model_dir),
            "--prompt",
            prompt,
            "--max-new-tokens",
            "160",
            "--temperature",
            str(temperature),
            "--json",
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(self.project_root),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            detail = stderr.decode("utf-8", errors="replace")[:2000]
            return f"Zeus-Tiny inference failed: {detail}"

        try:
            data = json.loads(stdout.decode("utf-8", errors="replace"))
            return data.get("text", "")
        except json.JSONDecodeError:
            return stdout.decode("utf-8", errors="replace")

    @staticmethod
    def _messages_to_prompt(messages: List[Dict[str, Any]]) -> str:
        lines = []
        for message in messages[-12:]:
            role = message.get("role", "user")
            content = message.get("content", "")
            lines.append(f"<|{role}|>\n{content}")
        lines.append("<|assistant|>\n")
        return "\n".join(lines)


zeus_native = ZeusNativeClient()
