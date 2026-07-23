# Google Gemini builds

> ✅ **Status: Gem build TESTED on-platform (2026-07-24).** A "Robot Builder" Gem was
> created with these instructions + knowledge and correctly answered a self-balancing
> PID debugging scenario with details that exist only in the knowledge files (oscillation
> triage order, Kd ≈ Kp/20–50 ratio, dt-dependent complementary-filter coefficient).
> The Gemini CLI (`GEMINI.md`) variant remains format-checked only.
>
> **Key finding: Gems cap knowledge at 10 files.** The 14 modules don't fit individually —
> upload the 9 core files plus `advanced-modules.md` (compute-platforms + control-and-
> stability + air-robots + ai-ml merged; TRAINING_MANUAL omitted — it's human onboarding,
> not mentor knowledge). The release zip ships exactly this 10-file set.

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
4. **Knowledge**: upload the 10 files from the release zip's `knowledge-gem/` folder
   (9 core modules + `advanced-modules.md`) — Gems reject uploads beyond 10 files.
5. Save and chat.

## C. Gemini API

Use the GEMINI.md body as the `system_instruction` and attach the reference markdown via
the Files API / context caching. Same adapter, programmatic.
