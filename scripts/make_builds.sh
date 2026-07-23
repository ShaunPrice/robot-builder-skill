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

# Gemini: adapter files + knowledge/
mkdir -p "$STAGE/gemini"
cp builds/gemini/*.md "$STAGE/gemini/"
knowledge "$STAGE/gemini/knowledge"
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
