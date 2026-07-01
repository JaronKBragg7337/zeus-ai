# Zeus Knowledge

Zeus Knowledge is separate from Zeus training data.

Use this area for facts and reference material Zeus can retrieve from, summarize,
or index locally:

- `manuals/` - product manuals, setup guides, and operating procedures.
- `research/` - papers, notes, market research, and technical references.
- `books/` - long-form reference material you are allowed to store locally.
- `code_docs/` - framework docs, API docs, and library notes.
- `project_docs/` - project-specific documents and specifications.
- `processed/` - local extracted/chunked text generated from the folders above.
- `index/` - generated local search/vector indexes.

Training data changes Zeus behavior. Knowledge tells Zeus what to look up.

Keep that boundary clear:

- Put approved behavior examples in `data/instruction_examples/approved.jsonl`.
- Put raw/candidate behavior traces in `data/tool_traces/` and
  `data/instruction_examples/candidates.jsonl`.
- Put factual reference material here.

The local contents of these folders are ignored by Git by default so private
documents and generated indexes do not get published.

## Local Index

Build or rebuild the local index:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/knowledge/index
```

Search it:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/knowledge/search -ContentType "application/json" -Body '{"query":"what should Zeus remember?","top_k":5}'
```

Status:

```powershell
Invoke-RestMethod http://localhost:8000/api/knowledge/status
```

The desktop app also has a Zeus Knowledge panel for these actions.

Packaged Windows desktop builds store knowledge under:

```text
%LOCALAPPDATA%\Zeus AI\knowledge
```
