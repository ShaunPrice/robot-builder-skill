# Hermes build (local Docker LLM stack)

> ❌ **Status: UNTESTED.** Assembled for a Hermes-style local setup (shell wrapper →
> Docker container with a small local model, e.g. Gemma-class via Docker Model Runner)
> but it has not been run. Expect to adapt paths/flags to your wrapper. The core caveat
> is real regardless of setup: **small local models have small context windows — load
> one reference file at a time, never the whole library.**

## Layout

Copy the knowledge into the Hermes data directory so the container can see it:

```bash
mkdir -p ~/.hermes/knowledge/robot-builder
cp builds/hermes/system-prompt.md ~/.hermes/knowledge/robot-builder/
cp references/*.md TRAINING_MANUAL.md ~/.hermes/knowledge/robot-builder/
```

(If your wrapper mounts a different directory into the container, use that instead —
the only requirement is that the model can be handed these files.)

## Wiring it up

1. **System prompt**: point the wrapper at
   `~/.hermes/knowledge/robot-builder/system-prompt.md` (however your wrapper passes a
   system prompt — flag, env var, or config file).
2. **Per-question retrieval** (the important part): before asking a robotics question,
   paste or attach the ONE reference file that matches it — the routing table inside
   `system-prompt.md` says which. A 4–8B local model will not hold all 14 files.
3. If your stack has RAG/embedding support, index the `knowledge/robot-builder/` folder
   instead and let retrieval pick the file.

## Expectations with small local models

Great for: routing you to the right reference, explaining a concept from a loaded file,
step-by-step checklists, wiring sanity checks. Weak at: long multi-file synthesis, exact
part-number recall without the file loaded, and safety judgment — **the safety rules in
the system prompt are hard rules precisely because a small model shouldn't improvise
them.** For anything safety-critical, verify against the actual reference file text.
