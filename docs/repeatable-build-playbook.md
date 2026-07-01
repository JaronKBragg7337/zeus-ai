# Repeatable Build Playbook

This playbook is for someone trying to reproduce the Zeus path with a capable coding AI and a Windows machine.

## Required Local Foundation

- Windows 11
- Python
- Node.js
- Rust/Cargo
- Git/GitHub CLI
- Ollama
- Local model for temporary communication/runtime
- Optional GPU for local training
- Optional cloud GPU credits for later larger Zeus-native runs

## Build Order

1. **Baseline Repo**
   - initialize Git
   - add `.gitignore`
   - commit generated baseline

2. **Local Workbench**
   - make backend run
   - make frontend build
   - verify Ollama model listing/chat
   - add basic tests

3. **Desktop App**
   - add Tauri shell
   - package backend as sidecar
   - build Windows installers
   - verify packaged app starts backend

4. **Local Control**
   - file tools
   - shell tool
   - kill switch
   - audit logs
   - full-computer mode

5. **Zeus Identity**
   - system prompt
   - local capability awareness
   - stop exposing temporary runtime model as identity

6. **Zeus-Native Model Track**
   - dataset folders
   - tokenizer trainer
   - from-scratch tiny transformer
   - inference script
   - backend native switch

7. **Learning Flywheel**
   - capture tool traces
   - capture completions
   - capture corrections
   - build dataset
   - train smoke model

8. **Computer-Use Body**
   - app launching
   - screenshot reading
   - keyboard/mouse automation
   - browser automation
   - UI state logging

9. **Founder-System Layer**
   - project memory
   - task queue
   - background loops
   - product/release packaging
   - company/process setup workflows

## Verification Standard

Every capability should have at least one of:

- automated test
- build command
- smoke script
- manual checklist
- logged packaged-app verification

## Training Data Rule

Captured data should be local and ignored by Git by default.

Before serious model training:

1. review generated JSONL
2. remove private or bad examples
3. label high-quality traces
4. run small local training
5. evaluate
6. scale to cloud GPU only when useful

## Release Standard

A Zeus release should include:

- installer
- README updates
- implementation log entry
- known limitations
- smoke-test result
- next-step roadmap

