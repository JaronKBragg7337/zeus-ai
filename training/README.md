# Zeus-Native Model Track

This folder is the first path toward Zeus having its own model instead of only using Qwen, Llama, or another external model as the brain.

The first target is `Zeus-Tiny`: a small transformer trained from scratch for Zeus-specific jobs:

- intent classification
- tool-call formatting
- memory classification
- task planning
- project summarization
- result review

It is not meant to compete with major chat models at first. It is meant to become the first native Zeus brain-piece.

## Flow

```powershell
python training/data/build_dataset.py
python training/tokenizer/train_tokenizer.py
python training/pretrain/train_zeus_tiny.py
python training/inference/zeus_tiny_infer.py --prompt "List files in this repo"
```

Then run the backend with:

```powershell
$env:ZEUSAI_NATIVE_MODEL = "1"
.\.venv\Scripts\python.exe backend\main.py
```

When `ZEUSAI_NATIVE_MODEL=1`, Zeus routes chat through `backend/zeus_native_client.py` and the local Zeus-Tiny checkpoint under `models/zeus-tiny/`.

## What Is Native

The scripts here do not load Qwen, Llama, Mistral, or any pretrained model. The tokenizer is trained from local Zeus text, and the transformer weights start random.

## Data Layout

```text
data/
  raw/                  local source text you choose to add
  instruction_examples/ seed instruction JSONL committed to the repo
  conversations/        optional exported conversations
  tool_traces/          optional tool/action traces
  code_tasks/           optional coding-task examples
  project_docs/         optional local project docs
  decisions/            optional decision memories
  processed/            generated JSONL datasets
```

Local generated data is ignored by Git. Commit only small seed examples that are safe to publish.

## Honest Expectations

`Zeus-Tiny` will be weak at first. That is normal. Its job is to create the training loop and data flywheel:

1. Zeus acts locally.
2. Zeus logs actions and outcomes.
3. The dataset builder turns good traces into training examples.
4. Zeus-Tiny trains on those examples.
5. Zeus takes over small native decisions.

Larger `Zeus-Small` and `Zeus-Core` models can come later with more data and rented GPU compute.
