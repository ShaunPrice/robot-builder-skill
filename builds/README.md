# Builds for other AI assistants

Robot Builder is authored as a Claude skill, but the knowledge is plain markdown — so it
ports. Each build below is an **adapter** around the same source of truth
([SKILL.md](../SKILL.md) + [references/](../references)): nothing is forked, so updates
to the references flow into every platform.

| Platform | Format | Directory / asset | Status |
|---|---|---|---|
| **Claude** (claude.ai, Claude Code) | Native skill (`.skill` / skills folder) | [`robot-builder.skill` release asset](https://github.com/ShaunPrice/robot-builder-skill/releases/latest), repo root | ✅ Tested — native platform |
| **OpenAI** (ChatGPT Custom GPT, Codex CLI) | GPT Instructions + Knowledge files; `AGENTS.md` | [`openai/`](openai/) | ✅ Custom GPT tested on-platform (Codex variant format-checked) |
| **Google Gemini** (Gems, Gemini CLI) | Gem instructions + knowledge; `GEMINI.md` | [`gemini/`](gemini/) | ✅ Gem tested on-platform — note the 10-file knowledge cap (CLI variant format-checked) |
| **Hermes** (Nous hermes-agent / local Docker LLMs) | Native `~/.hermes/skills/` (Claude format!) or system prompt + docs | [`hermes/`](hermes/) | ✅ Tested on-platform with local Gemma4-4B (see context-size gotcha) |
| **OpenClaw** | Claude-compatible skills folder via `openclaw skills install` | [`openclaw/`](openclaw/) | ✅ Install + discovery verified (agent runtime not exercised) |

Each directory has its own `INSTALL.md`. Prebuilt zips for every platform are attached to
the [latest release](https://github.com/ShaunPrice/robot-builder-skill/releases/latest);
`scripts/make_builds.sh` regenerates them from source.

## Porting notes (read before adding a platform)

- The **adapter's job** is: persona + the build-ladder workflow + safety rules + a map of
  which reference file answers which question. The **references' job** is the actual
  knowledge. Keep adapters short; never copy reference content into them.
- The safety rules in SKILL.md (LiPo discipline, props-off, legal flight, "AI proposes /
  deterministic code disposes", no port-forwarding) are **non-negotiable across every
  platform** — port them verbatim.
- Small-context models (local Hermes-class): load one reference at a time, never the
  whole set.
