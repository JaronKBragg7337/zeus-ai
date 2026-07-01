# AI Coworker Protocol

This project assumes capable AI coworkers may work on Zeus over time, including Codex, Claude Code, Claude Cowork, Fable, and future Zeus-native agents.

The identity of the project remains Zeus. External models and coding agents are workers, not the Zeus identity.

## Standing User Intent

The user wants momentum and real artifacts.

Use the local machine fully when needed for normal engineering work:

- inspect files
- install local dependencies
- build apps
- run tests
- package desktop installers
- create local training data
- run local training smoke tests
- use local tools and scripts

Do not repeatedly ask for permission for ordinary development steps.

Make visible before doing actions that:

- spend money
- publish data
- expose secrets
- delete or overwrite broad areas
- create cloud resources
- upload private training data

## Required Work Pattern

1. Read the repo before making assumptions.
2. Make small, testable changes.
3. Preserve the project structure unless the change requires otherwise.
4. Verify with commands.
5. Update docs when behavior changes.
6. Commit in logical steps.
7. Push only when the work is ready or the user asked.
8. Keep generated secrets, data, model weights, caches, and build artifacts out of Git.

## Documentation Duty

When an AI coworker makes a meaningful change, it should update at least one of:

- `README.md`
- `docs/implementation-log.md`
- a focused doc under `docs/`
- training docs under `training/`

Good entries include:

- date
- agent/tool used
- goal
- files changed
- commands run
- tests/builds
- outcome
- follow-up work

## Model Worker Roles

These names are operating roles, not fixed vendors.

- **Zeus Manager**
  - owns project direction, memory, routing, and final judgment

- **Codex Worker**
  - repo edits, tests, builds, packaging, code review

- **Claude Worker**
  - architecture review, long-form reasoning, docs, alternate implementation critique

- **Fable Worker**
  - storytelling, product framing, demos, brand, presentation, promotion

- **Zeus-Native Worker**
  - routing, memory classification, tool-call formatting, local task summaries, eventually broader reasoning

## Handoff Format

When handing work to another AI coworker, include:

```text
Project:
Current branch/commit:
Goal:
Recent changes:
Commands already run:
Known failures:
Generated artifacts:
Do not touch:
Next best step:
```

## Principle

The repo should make the work repeatable by another person with similar tools. Do not leave the build process trapped in one chat transcript.

