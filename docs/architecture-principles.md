# Zeus Architecture Principles

Zeus should learn from useful systems without becoming dependent on them. A project, model, vendor, website, or connector is evidence that a technique works. It is not the technique itself and it is not a permanent Zeus dependency.

## The Extraction Rule

When evaluating an outside system, separate it into four layers:

1. **Observed result**: what capability it demonstrably provides.
2. **Mechanism**: the underlying technique that creates that result.
3. **Contract**: the Zeus-owned interface needed to use that technique.
4. **Implementation**: one replaceable adapter that satisfies the contract.

Do not copy an implementation or lock Zeus to a provider when the mechanism can be expressed as a local contract.

Example: the Colibri project demonstrates sparse activation and disk-streamed model components. The Zeus principle is resource-aware model execution: load only the work needed for the current task, keep large artifacts out of scarce memory where possible, and expose latency/storage tradeoffs. Ollama remains the current adapter; Colibri is not a dependency.

## Runtime Independence

Zeus owns the work contract, not the model runtime:

- messages, streaming, tool calls, structured results, and cancellation are Zeus contracts
- Ollama, Zeus-Tiny, or a future runtime are adapters
- a runtime must earn use by passing Zeus capability tests, not by its parameter count or marketing claim
- model assets, embeddings, indexes, and tool traces are separate resources with explicit storage locations

This allows a better runtime to be adopted later without rewriting chat, Agent, memory, training review, or desktop control.

## Acquisition Is An Artifact Pipeline

Zeus should obtain information through a transparent sequence rather than treating every page, message, or tool result as immediate truth:

```text
discover -> acquire -> normalize -> attach provenance -> verify -> retrieve or promote
```

Every acquired artifact should be able to carry:

- source identity and locator (local path, URL, connector record, or worker)
- observed time and content hash
- access/ownership and license notes when known
- extraction method and parser version
- verification links or disagreements
- destination lane: raw artifact, factual knowledge, user memory, task evidence, or training candidate

The same source may be useful in more than one lane, but promotion must be deliberate. A web page can become a factual knowledge artifact; it does not automatically become a user memory or behavior-training example.

## Source Adapters, Not Hardcoded Sites

The source layer should support local folders, browser sessions, GitHub, Reddit, Slack, Heartbeat/PAM, APIs, and future sources through replaceable adapters. An adapter's responsibility is limited to acquiring and normalizing material; it does not decide permanent truth or make it part of model behavior.

This is how Zeus can use a new source without being rewritten around that source. Configuration selects available adapters, capability discovery reports what is currently connected, and the same artifact format flows to retrieval and review.

## Memory And World Projection

Local Zeus memory is the offline-first source of truth. Heartbeat Observatory can become an optional synchronized projection and interaction space:

- real memory/project records create real rooms, shelves, terminals, or status objects
- visual state must be derived from a record, not invented for atmosphere
- the 3D world is a powerful way to navigate and understand memory; it is not the only database
- a local Zeus instance remains useful if the site, network, or connector is unavailable

## Evaluation Before Dependence

Before adopting any engine, model, library, or service, test it against a small Zeus evaluation set:

- startup and resource use
- streaming quality and cancellation
- tool-call correctness across multiple steps
- memory/retrieval compatibility
- failure behavior and observability
- packaging on the supported operating systems

Keep the test result, not just an opinion. A dependency becomes a supported adapter only after it works against the contract.
