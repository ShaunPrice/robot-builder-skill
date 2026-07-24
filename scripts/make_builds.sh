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

# Logical reading order for the consolidated single-file build.
ORDER="parts-and-budgets hardware-requirements setup-and-cloud design-and-3d getting-started \
compute-platforms sensors ros ground-robots water-robots air-robots \
manipulation-and-arms cnc-and-motion swarm-and-multi-robot control-and-stability \
simulation-and-gyms docker-and-environments security ai-ml"

consolidate() {  # $1 = output file: the entire reference set in one file with a TOC
  local out="$1"
  {
    echo "# Robot Builder — complete knowledge base"
    echo
    echo "The entire Robot Builder reference set in one file. (Gemini Gems cap knowledge at"
    echo "10 files, so the whole skill ships as one.) Each module below is delimited by a"
    echo "\`MODULE: name\` marker. Contents:"
    echo
    for f in $ORDER; do echo "- $f"; done
    for f in $ORDER; do
      echo; echo "<!-- ===================== MODULE: $f.md ===================== -->"; echo
      cat "references/$f.md"; echo
    done
  } > "$out"
  echo "consolidated $(echo $ORDER | wc -w | tr -d ' ') modules -> $out ($(wc -l < "$out") lines)"
}

# OpenAI: adapter files + flat knowledge/ for Custom GPT upload
mkdir -p "$STAGE/openai"
cp builds/openai/*.md "$STAGE/openai/"
knowledge "$STAGE/openai/knowledge"
(cd "$STAGE/openai" && zip -qr - .) > dist/robot-builder-openai-gpt.zip

# Gemini: adapter files + full knowledge/ (for the CLI) + knowledge-gem/ (the WHOLE skill
# consolidated into ONE file + the manual — Gems cap knowledge at 10 files, so a single
# complete file scales no matter how many modules the skill grows to).
mkdir -p "$STAGE/gemini/knowledge-gem"
cp builds/gemini/*.md "$STAGE/gemini/"
knowledge "$STAGE/gemini/knowledge"
consolidate "$STAGE/gemini/knowledge-gem/robot-builder-complete.md"
cp TRAINING_MANUAL.md "$STAGE/gemini/knowledge-gem/"
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
