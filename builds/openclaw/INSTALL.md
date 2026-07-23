# OpenClaw build

> ❌ **Status: UNTESTED.** OpenClaw's skill system follows the Claude-compatible
> `SKILL.md` convention, so the native skill folder *should* drop straight in — but
> this has not been verified against a live OpenClaw install, and OpenClaw moves fast.
> Check the current OpenClaw docs for the exact skills directory and format before
> relying on it, and report back via a repo issue either way.

## Install (expected path)

OpenClaw discovers skills from its workspace/config skills directory (commonly
`~/.openclaw/skills/` — verify against your install's docs):

```bash
git clone https://github.com/ShaunPrice/robot-builder-skill.git ~/.openclaw/skills/robot-builder
```

The repo root **is** the skill: `SKILL.md` (frontmatter `name` + `description` +
playbook) with `references/` beside it — the same layout Claude Code consumes, which is
the format OpenClaw's skill loader targets. Restart the OpenClaw gateway/agent and ask
it something robot-flavored ("what should I buy to build my first rover?") to confirm it
triggers.

## If auto-discovery doesn't work

Fall back to context injection: paste the body of `SKILL.md` into the agent's system
prompt / workspace instructions, keep the repo checked out in the workspace, and let the
agent read `references/*.md` with its file tools — that mirrors how the AGENTS.md build
works (see `builds/openai/AGENTS.md`, which also works as a generic agent adapter).

## Cautions

- Same non-negotiable safety rules as every other build (see `SKILL.md`) — an
  autonomous agent framework with shell access makes the "AI proposes, deterministic
  code disposes" rule *more* important, not less: don't wire an OpenClaw agent directly
  to robot actuators.
- The heavy media (`media/`, GIFs, model zip) is dead weight for a skill install —
  a shallow clone or deleting `media/` after cloning keeps it lean.
