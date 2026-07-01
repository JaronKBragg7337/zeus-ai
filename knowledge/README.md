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
