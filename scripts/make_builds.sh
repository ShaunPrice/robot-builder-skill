#!/usr/bin/env bash
# Assemble per-platform distribution zips into dist/ from the single source of truth
# (SKILL.md + references/ + TRAINING_MANUAL.md + builds/<platform>/ adapters).
# Usage: scripts/make_builds.sh   (run from the repo root)
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf dist && mkdir -p dist
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

knowledge() {  # $1 = target dir; copies the shared knowledge set
  mkdir -p "$1"
  cp references/*.md TRAINING_MANUAL.md "$1/"
}

# OpenAI: adapter files + flat knowledge/ for Custom GPT upload
mkdir -p "$STAGE/openai"
cp builds/openai/*.md "$STAGE/openai/"
knowledge "$STAGE/openai/knowledge"
(cd "$STAGE/openai" && zip -qr - .) > dist/robot-builder-openai-gpt.zip

# Gemini: adapter files + full knowledge/ (for CLI) + knowledge-gem/ (10-file set —
# Gems cap knowledge at 10 files, verified on-platform 2026-07-24)
mkdir -p "$STAGE/gemini/knowledge-gem"
cp builds/gemini/*.md "$STAGE/gemini/"
knowledge "$STAGE/gemini/knowledge"
for f in parts-and-budgets getting-started sensors ros ground-robots water-robots \
         docker-and-environments security simulation-and-gyms; do
  cp "references/$f.md" "$STAGE/gemini/knowledge-gem/"
done
{ echo "# Advanced modules (combined for Gemini's 10-file knowledge limit): compute platforms, control & stability, air robots, AI/ML"; echo
  cat references/compute-platforms.md; echo; echo "---"; echo
  cat references/control-and-stability.md; echo; echo "---"; echo
  cat references/air-robots.md; echo; echo "---"; echo
  cat references/ai-ml.md
} > "$STAGE/gemini/knowledge-gem/advanced-modules.md"
(cd "$STAGE/gemini" && zip -qr - .) > dist/robot-builder-gemini.zip

# Hermes (UNTESTED): system prompt + install + knowledge/
mkdir -p "$STAGE/hermes"
cp builds/hermes/*.md "$STAGE/hermes/"
knowledge "$STAGE/hermes/knowledge"
(cd "$STAGE/hermes" && zip -qr - .) > dist/robot-builder-hermes.zip

# OpenClaw (UNTESTED): the Claude-format skill folder itself + install notes
mkdir -p "$STAGE/openclaw/robot-builder/references"
cp SKILL.md TRAINING_MANUAL.md "$STAGE/openclaw/robot-builder/"
cp references/*.md "$STAGE/openclaw/robot-builder/references/"
cp builds/openclaw/INSTALL.md "$STAGE/openclaw/"
(cd "$STAGE/openclaw" && zip -qr - .) > dist/robot-builder-openclaw.zip

ls -lh dist/
echo "Claude native: package with skill-creator's package_skill.py -> robot-builder.skill"
