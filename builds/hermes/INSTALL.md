# Hermes build (Nous Hermes agent / local Docker LLM stacks)

> ✅ **Status: TESTED on-platform (2026-07-24)** against the NousResearch `hermes-agent`
> Docker image with a local Gemma4-4B via Docker Model Runner. Key result: **Hermes
> natively consumes the Claude SKILL.md format** — the skill folder drops straight into
> `~/.hermes/skills/` and Hermes discovers it, reads its reference files with tool calls,
> and answers with file-specific detail (verified with the L298N/motor-driver scenario;
> single-query test via `hermes chat -q`, ~3 min on a 4B model).

## A. Native skill install (recommended — verified)

```bash
git clone https://github.com/ShaunPrice/robot-builder-skill.git /tmp/rb
mkdir -p ~/.hermes/skills/robot-builder/references
cp /tmp/rb/SKILL.md /tmp/rb/TRAINING_MANUAL.md ~/.hermes/skills/robot-builder/
cp /tmp/rb/references/*.md ~/.hermes/skills/robot-builder/references/
hermes chat -q "Use your robot-builder skill: what motor driver should a beginner avoid and why?"
```

Hermes auto-injects skill descriptions into its system prompt and loads the skill body
plus references on demand (`skill_view` tool) — same progressive-disclosure model as
Claude.

### Gotchas found in testing (both will bite you)

1. **Context size.** Hermes's system prompt with many skills installed runs ~15–20k
   tokens, but **Docker Model Runner serves models with a 4,096-token context by
   default** → instant "exceeds available context" failure. Fix:
   ```bash
   docker model configure --context-size 32768 ai/gemma4:4B
   ```
2. **Model presence.** A Docker prune can silently remove the model while the config
   still points at it (404 "model not found"). Re-pull with
   `docker model pull ai/gemma4:4B` (~6 GB). *(This build was verified locally against the
   `ai/gemma4:4B` tag; if `docker model ls` / Docker Hub don't list that exact tag on your
   machine, use the current public Gemma tag, e.g. `ai/gemma4:E4B`, in both commands.)*

## B. Generic system-prompt fallback (for wrappers without a skills system)

If your local stack is a bare llama.cpp/Ollama wrapper with no skill support, use
[`system-prompt.md`](system-prompt.md) as the system prompt and keep the reference files
in a folder the model can be handed one at a time — a 4–8B model cannot hold all 19
files at once. The routing table inside the prompt says which file answers which
question. The release zip's `knowledge/` folder contains the full file set.

## Expectations with small local models

Great for: routing to the right reference, explaining a loaded file, checklists, wiring
sanity checks. Weak at: long multi-file synthesis and safety judgment — **the safety
rules are hard rules precisely because a small model shouldn't improvise them.** Verify
anything safety-critical against the actual reference text.
