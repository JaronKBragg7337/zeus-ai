"""Runtime helpers for the Zeus word tokenizer."""
import json
import re
from pathlib import Path


class ZeusTokenizer:
    def __init__(self, tokenizer_path: Path):
        data = json.loads(Path(tokenizer_path).read_text(encoding="utf-8"))
        self.token_to_id = {str(k): int(v) for k, v in data["token_to_id"].items()}
        self.id_to_token = {int(k): str(v) for k, v in data["id_to_token"].items()}
        self.pattern = re.compile(data["pattern"], re.UNICODE)
        self.unk_id = self.token_to_id["<|unk|>"]
        self.bos_id = self.token_to_id["<|bos|>"]
        self.eos_id = self.token_to_id["<|eos|>"]

    def encode(self, text: str, *, add_bos: bool = False, add_eos: bool = False):
        ids = []
        if add_bos:
            ids.append(self.bos_id)
        ids.extend(self.token_to_id.get(token, self.unk_id) for token in self.pattern.findall(text))
        if add_eos:
            ids.append(self.eos_id)
        return ids

    def decode(self, ids):
        tokens = [self.id_to_token.get(int(idx), "<|unk|>") for idx in ids]
        text = " ".join(token for token in tokens if not token.startswith("<|"))
        return (
            text.replace(" ,", ",")
            .replace(" .", ".")
            .replace(" :", ":")
            .replace(" ;", ";")
            .replace(" !", "!")
            .replace(" ?", "?")
            .replace(" \\", "\\")
            .replace(" / ", "/")
        )
