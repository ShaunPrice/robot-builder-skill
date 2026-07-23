# OpenAI builds

> ⚠️ **Status: format-checked, not end-to-end tested.** These follow OpenAI's documented
> formats (Custom GPT instructions ≤8,000 chars, ≤20 knowledge files; AGENTS.md for
> Codex), but haven't been exercised on-platform. Report issues on the repo.

## A. ChatGPT Custom GPT (recommended for chat use)

1. Go to chatgpt.com → **GPTs → Create** (requires a plan with GPT creation).
2. Open the **Configure** tab:
   - **Name**: `Robot Builder` · **Description**: "Your robotics mentor — from first
     parts list to machine learning, across ground, water, and air."
   - **Instructions**: paste the body of [`gpt-instructions.md`](gpt-instructions.md)
     (everything below its `---` line).
3. **Knowledge**: upload all 13 files from the repo's `references/` folder plus
   `TRAINING_MANUAL.md` (14 files — under the 20-file limit). The prebuilt
   `robot-builder-openai-gpt.zip` release asset contains exactly this set plus the
   instructions file — unzip and drag them in.
4. **Capabilities**: enable Web Search (part prices move) and Code Interpreter (for the
   simulation example). Image generation optional.
5. Save (private, link-only, or public — your call).

## B. Codex CLI / OpenAI agents (for building alongside code)

Codex reads `AGENTS.md` from the working directory:

```bash
git clone https://github.com/ShaunPrice/robot-builder-skill.git my-robot
cd my-robot   # or copy AGENTS.md + references/ into your own robot project
```

[`AGENTS.md`](AGENTS.md) (in this directory) is a ready-made project file that tells the
agent to act as the Robot Builder mentor and consult `references/` — copy it and the
`references/` folder into any robot project's root.

## C. OpenAI API (Assistants/Responses)

Use `gpt-instructions.md` as the system prompt and attach the `references/` markdown
files via file search / retrieval. Same pattern as the Custom GPT, programmatically.
