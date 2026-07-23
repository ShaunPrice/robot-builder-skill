# OpenClaw build

> ✅ **Status: install + discovery VERIFIED (2026-07-24) on OpenClaw 2026.6.33.**
> `openclaw skills install <local-clone>` accepted the skill unmodified, placed it at
> `~/.openclaw/workspace/skills/robot-builder`, and `openclaw skills list` reports it
> **✓ ready** with the SKILL.md description parsed. The agent *runtime* (an LLM
> answering through OpenClaw using the skill) was not exercised — that requires a
> configured model provider/gateway; run one robot question after your normal OpenClaw
> setup to confirm, and report via a repo issue either way.

## Install (verified)

```bash
git clone https://github.com/ShaunPrice/robot-builder-skill.git /tmp/robot-builder-skill
openclaw skills install /tmp/robot-builder-skill
openclaw skills list   # → "✓ ready  robot-builder"
```

The repo root **is** the skill: `SKILL.md` (frontmatter `name` + `description` +
playbook) with `references/` beside it — the same layout Claude Code consumes. OpenClaw
copies it into its workspace skills directory; restart the gateway/agent and ask
something robot-flavored ("what should I buy to build my first rover?") to confirm
triggering.

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
