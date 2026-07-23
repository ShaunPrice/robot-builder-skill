# Google Gemini builds

> ⚠️ **Status: format-checked, not end-to-end tested.** These follow Google's documented
> formats (GEMINI.md context files for Gemini CLI; Gems with instructions + knowledge),
> but haven't been exercised on-platform. Report issues on the repo.

## A. Gemini CLI (for building alongside code)

Gemini CLI automatically loads `GEMINI.md` from the project directory:

```bash
git clone https://github.com/ShaunPrice/robot-builder-skill.git my-robot
cd my-robot
cp builds/gemini/GEMINI.md .   # put the context file at the project root
gemini
```

Or copy `GEMINI.md` + the `references/` folder into your own robot project's root. For
global availability, append it to `~/.gemini/GEMINI.md`.

## B. Gemini Gem (for chat use)

1. In the Gemini app: **Gems → New Gem** (Gem creation availability varies by plan).
2. **Name**: `Robot Builder`.
3. **Instructions**: paste the body of [`GEMINI.md`](GEMINI.md) — it doubles as the Gem
   persona. Remove the file-path table if you skip step 4, or reword it to "your
   uploaded knowledge files".
4. **Knowledge**: upload the 13 files from `references/` plus `TRAINING_MANUAL.md`
   (the prebuilt `robot-builder-gemini.zip` release asset contains exactly this set).
5. Save and chat.

## C. Gemini API

Use the GEMINI.md body as the `system_instruction` and attach the reference markdown via
the Files API / context caching. Same adapter, programmatic.
