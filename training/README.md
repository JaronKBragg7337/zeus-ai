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
  instruction_examples/ seed, candidate, approved, and rejected examples
  conversations/        optional exported conversations
  tool_traces/          optional tool/action traces
  code_tasks/           optional coding-task examples
  project_docs/         optional local project docs
  decisions/            optional decision memories
  processed/            generated JSONL datasets

knowledge/
  manuals/              factual reference docs
  research/             papers and research notes
  books/                local long-form references
  code_docs/            framework/API documentation
  project_docs/         project specs and reference docs
  processed/            extracted or chunked knowledge text
  index/                generated local search/vector indexes
```

Local generated data is ignored by Git. Commit only small seed examples that are safe to publish. Keep knowledge separate from training: knowledge tells Zeus what to retrieve; training changes Zeus behavior.

## Automatic Capture

Zeus captures local training material from real usage by default:

- tool calls -> `data/tool_traces/tool_calls.jsonl`
- agent runs -> `data/tool_traces/agent_runs.jsonl`
- chat completions -> `data/tool_traces/chat_completions.jsonl`
- user corrections -> `data/tool_traces/user_corrections.jsonl`
- candidate instruction examples -> `data/instruction_examples/candidates.jsonl`

Candidates are not treated as trusted training data. Review them first:

```text
GET /api/training/candidates
POST /api/training/review
```

The desktop app also has a Training Review panel for this queue.

Approved examples are appended to:

```text
data/instruction_examples/approved.jsonl
```

Rejected examples and review records are kept locally for evaluator training and debugging.

The capture switch is:

```powershell
$env:ZEUSAI_CAPTURE_TRAINING = "1"  # default
$env:ZEUSAI_CAPTURE_TRAINING = "0"  # disable capture
```

To redirect generated data:

```powershell
$env:ZEUSAI_DATA_DIR = "D:\ZeusTrainingData"
```

Explicit corrections can be sent to:

```text
POST /api/training/correction
```

with:

```json
{
  "original": "What Zeus said or did",
  "correction": "What Zeus should learn instead",
  "context": "Optional note"
}
```

The default dataset command uses only committed seed examples plus reviewed approved examples:

```powershell
python training/data/build_dataset.py
```

Experiment-only options:

```powershell
python training/data/build_dataset.py --include-candidates
python training/data/build_dataset.py --include-tool-traces
python training/data/build_dataset.py --include-knowledge
```

Use the opt-in flags carefully. Pending candidates, failed traces, and knowledge docs are valuable, but they should not automatically become positive behavior examples.

## Honest Expectations

`Zeus-Tiny` will be weak at first. That is normal. Its job is to create the training loop and data flywheel:

1. Zeus acts locally.
2. Zeus logs actions and outcomes.
3. Candidate examples wait for review.
4. The dataset builder turns approved traces into training examples.
5. Zeus-Tiny trains on those examples.
6. Zeus takes over small native decisions.

Larger `Zeus-Small` and `Zeus-Core` models can come later with more data and rented GPU compute.
