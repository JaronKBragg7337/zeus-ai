"""Train Zeus-Tiny from scratch with a minimal GPT-style transformer."""
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

import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / "inference"))
from tokenizer_runtime import ZeusTokenizer


class TinyGPT(nn.Module):
    def __init__(self, vocab_size: int, block_size: int = 128, n_embd: int = 128, n_head: int = 4, n_layer: int = 4):
        super().__init__()
        self.config = {
            "vocab_size": vocab_size,
            "block_size": block_size,
            "n_embd": n_embd,
            "n_head": n_head,
            "n_layer": n_layer,
        }
        self.token_embedding = nn.Embedding(vocab_size, n_embd)
        self.position_embedding = nn.Embedding(block_size, n_embd)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=n_embd,
            nhead=n_head,
            dim_feedforward=4 * n_embd,
            dropout=0.1,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.blocks = nn.TransformerEncoder(encoder_layer, num_layers=n_layer)
        self.ln_f = nn.LayerNorm(n_embd)
        self.head = nn.Linear(n_embd, vocab_size, bias=False)
        self.block_size = block_size

    def forward(self, idx, targets=None):
        batch, time = idx.shape
        positions = torch.arange(0, time, device=idx.device).unsqueeze(0)
        x = self.token_embedding(idx) + self.position_embedding(positions)
        mask = torch.triu(torch.ones(time, time, device=idx.device), diagonal=1).bool()
        x = self.blocks(x, mask=mask)
        logits = self.head(self.ln_f(x))
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))
        return logits, loss


def load_tokens(dataset_path: Path, tokenizer: ZeusTokenizer):
    ids = []
    for line in dataset_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        ids.extend(tokenizer.encode(data["text"], add_bos=True, add_eos=True))
    return torch.tensor(ids, dtype=torch.long)


def get_batch(tokens, block_size, batch_size, device):
    if len(tokens) <= block_size + 1:
        raise SystemExit("Dataset is too small for the configured block size.")
    starts = torch.randint(0, len(tokens) - block_size - 1, (batch_size,))
    x = torch.stack([tokens[i:i + block_size] for i in starts]).to(device)
    y = torch.stack([tokens[i + 1:i + block_size + 1] for i in starts]).to(device)
    return x, y


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[2])
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--model-dir", default=None)
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--block-size", type=int, default=128)
    parser.add_argument("--n-embd", type=int, default=128)
    parser.add_argument("--n-head", type=int, default=4)
    parser.add_argument("--n-layer", type=int, default=4)
    parser.add_argument("--lr", type=float, default=3e-4)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    model_dir = Path(args.model_dir) if args.model_dir else repo_root / "models" / "zeus-tiny"
    dataset = Path(args.dataset) if args.dataset else repo_root / "data" / "processed" / "zeus_corpus.jsonl"
    tokenizer_path = model_dir / "tokenizer.json"

    tokenizer = ZeusTokenizer(tokenizer_path)
    tokens = load_tokens(dataset, tokenizer)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = TinyGPT(
        vocab_size=len(tokenizer.token_to_id),
        block_size=args.block_size,
        n_embd=args.n_embd,
        n_head=args.n_head,
        n_layer=args.n_layer,
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)

    model.train()
    for step in range(1, args.steps + 1):
        x, y = get_batch(tokens, args.block_size, args.batch_size, device)
        _logits, loss = model(x, y)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        if step == 1 or step % 50 == 0:
            print(f"step={step} loss={loss.item():.4f}")

    model_dir.mkdir(parents=True, exist_ok=True)
    torch.save({"model_state": model.state_dict(), "config": model.config}, model_dir / "model.pt")
    print(f"Saved Zeus-Tiny checkpoint to {model_dir / 'model.pt'}")


if __name__ == "__main__":
    main()
