# Google Gemini builds

> ✅ **Status: Gem build TESTED on-platform (2026-07-24).** A "Robot Builder" Gem was
> created with these instructions + knowledge and correctly answered a self-balancing
> PID debugging scenario with details that exist only in the knowledge files (oscillation
> triage order, Kd ≈ Kp/20–50 ratio, dt-dependent complementary-filter coefficient).
> The Gemini CLI (`GEMINI.md`) variant remains format-checked only.
>
> **Key finding: Gems cap knowledge at 10 files.** The skill now has 18 reference modules,
> far past that. The scaling fix: the whole skill ships as **one consolidated file**,
> `robot-builder-complete.md` (every module, table-of-contents + `MODULE:` markers),
> uploaded as the Gem's single knowledge file. This uses 1 of the 10 slots and never
> outgrows the cap no matter how many modules are added. The release zip's `knowledge-gem/`
> folder contains exactly that file plus `TRAINING_MANUAL.md`.

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
4. **Knowledge**: upload `robot-builder-complete.md` from the release zip's `knowledge-gem/`
   folder (the entire skill in one file) — optionally add `TRAINING_MANUAL.md`. One file
   carries all 18 modules and stays well under the 10-file cap.
5. Save and chat.

## C. Gemini API

Use the GEMINI.md body as the `system_instruction` and attach the reference markdown via
the Files API / context caching. Same adapter, programmatic.
