"""Run local Zeus-Tiny inference from from-scratch weights."""
import argparse
import json
import math
from pathlib import Path

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except ImportError as exc:
    raise SystemExit("PyTorch is required. Install with: uv pip install --python .venv\\Scripts\\python.exe torch") from exc

from tokenizer_runtime import ZeusTokenizer


class TinyGPT(nn.Module):
    def __init__(self, vocab_size: int, block_size: int = 128, n_embd: int = 128, n_head: int = 4, n_layer: int = 4):
        super().__init__()
        self.token_embedding = nn.Embedding(vocab_size, n_embd)
        self.position_embedding = nn.Embedding(block_size, n_embd)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=n_embd,
            nhead=n_head,
            dim_feedforward=4 * n_embd,
            dropout=0.0,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.blocks = nn.TransformerEncoder(encoder_layer, num_layers=n_layer)
        self.ln_f = nn.LayerNorm(n_embd)
        self.head = nn.Linear(n_embd, vocab_size, bias=False)
        self.block_size = block_size

    def forward(self, idx):
        idx = idx[:, -self.block_size:]
        batch, time = idx.shape
        positions = torch.arange(0, time, device=idx.device).unsqueeze(0)
        x = self.token_embedding(idx) + self.position_embedding(positions)
        mask = torch.triu(torch.ones(time, time, device=idx.device), diagonal=1).bool()
        x = self.blocks(x, mask=mask)
        return self.head(self.ln_f(x))


@torch.no_grad()
def generate(model, idx, max_new_tokens, temperature, eos_id):
    for _ in range(max_new_tokens):
        logits = model(idx)[:, -1, :]
        if temperature <= 0:
            next_id = torch.argmax(logits, dim=-1, keepdim=True)
        else:
            probs = F.softmax(logits / temperature, dim=-1)
            next_id = torch.multinomial(probs, num_samples=1)
        idx = torch.cat([idx, next_id], dim=1)
        if int(next_id.item()) == eos_id:
            break
    return idx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", default=Path(__file__).resolve().parents[2] / "models" / "zeus-tiny")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--max-new-tokens", type=int, default=120)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    model_dir = Path(args.model_dir)
    tokenizer = ZeusTokenizer(model_dir / "tokenizer.json")
    checkpoint = torch.load(model_dir / "model.pt", map_location="cpu")
    config = checkpoint["config"]
    model = TinyGPT(**config)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()

    ids = tokenizer.encode(args.prompt, add_bos=True)
    idx = torch.tensor([ids], dtype=torch.long)
    generated = generate(model, idx, args.max_new_tokens, args.temperature, tokenizer.eos_id)
    new_tokens = generated[0, len(ids):].tolist()
    text = tokenizer.decode(new_tokens)

    if args.json:
        print(json.dumps({"text": text}, ensure_ascii=False))
    else:
        print(text)


if __name__ == "__main__":
    main()
