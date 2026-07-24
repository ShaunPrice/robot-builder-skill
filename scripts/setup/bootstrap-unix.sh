#!/usr/bin/env bash
# Robot Builder — beginner dev-environment bootstrap for macOS and Linux.
#
# Sets up the safe, universal starting point: Docker + a working ROS 2 container.
# It does NOT install a CUDA/Isaac stack (opt-in, machine-specific — see
# references/hardware-requirements.md) and never touches a robot's Pi/Jetson.
#
# Usage:   ./bootstrap-unix.sh          # interactive: shows each step, asks before installing
#          ./bootstrap-unix.sh --yes    # unattended
#
# Every command here is also documented step-by-step in references/getting-started.md and
# references/docker-and-environments.md — this script is a convenience, not a black box.
set -euo pipefail

ROS_IMAGE="${ROS_IMAGE:-osrf/ros:jazzy-desktop}"
ASSUME_YES=0; WITH_CHATBOT=0
for arg in "$@"; do case "$arg" in
  --yes|-y) ASSUME_YES=1;;
  --with-chatbot) WITH_CHATBOT=1;;
esac; done

say(){ printf '\n\033[1;36m▶ %s\033[0m\n' "$*"; }
info(){ printf '  %s\n' "$*"; }
ask(){ # ask "question" -> returns 0 for yes
  [ "$ASSUME_YES" = 1 ] && return 0
  printf '  \033[1m%s\033[0m [y/N] ' "$1"; read -r a </dev/tty || return 1
  case "$a" in y|Y|yes|YES) return 0;; *) return 1;; esac
}
have(){ command -v "$1" >/dev/null 2>&1; }

OS="$(uname -s)"
say "Robot Builder setup — detected: $OS"
info "Target: Docker + the ROS 2 image '$ROS_IMAGE'. Nothing else is installed."

# ---------- Docker ----------
install_docker_mac(){
  if ! have brew; then
    say "Homebrew is missing (the macOS package manager)."
    if ask "Install Homebrew now (official installer from brew.sh)?"; then
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else info "Skipping. Install Homebrew yourself, then re-run."; exit 1; fi
  fi
  say "Installing Docker Desktop via Homebrew…"
  brew install --cask docker
  info "Starting Docker Desktop (it may ask for permission once)…"
  open -a Docker || true
}
install_docker_linux(){
  say "Installing Docker Engine via Docker's official convenience script…"
  info "This runs: curl -fsSL https://get.docker.com | sh"
  ask "Proceed?" || { info "Skipping. See docker-and-environments.md for the manual apt steps."; exit 1; }
  curl -fsSL https://get.docker.com | sh
  if ! groups "$USER" | grep -qw docker; then
    info "Adding $USER to the 'docker' group (so you don't need sudo)…"
    sudo usermod -aG docker "$USER"
    info "Log out and back in (or run 'newgrp docker') for that to take effect."
  fi
  sudo systemctl enable --now docker 2>/dev/null || sudo service docker start 2>/dev/null || true
}
install_chatbot(){ # optional: a no-Docker local chatbot backend (Ollama + a small model)
  say "Optional: local no-Docker chatbot backend (Ollama + a small model)…"
  if have ollama; then info "Ollama already installed."; else
    case "$OS" in
      Darwin) ask "Install Ollama via Homebrew?" && brew install ollama || return 0;;
      Linux)  ask "Install Ollama (official script from ollama.com)?" && curl -fsSL https://ollama.com/install.sh | sh || return 0;;
    esac
  fi
  info "Pulling a small local model (llama3.2:3b, ~2 GB)…"
  ollama pull llama3.2:3b || info "Model pull skipped — run 'ollama pull llama3.2:3b' later."
  if [ "$OS" = Darwin ] && have brew; then
    ask "Install the AnythingLLM desktop app (the chat UI — no Docker)?" && brew install --cask anythingllm || true
  else
    info "Install the AnythingLLM desktop app from anythingllm.com (Linux: AppImage) — the no-Docker chat UI."
  fi
  cat <<EOF2

  Your local mentor (offline, no Docker, no subscription):
    1. Open AnythingLLM, create a Workspace, and point it at Ollama (model: llama3.2:3b).
    2. Set the workspace system prompt to the Robot Builder persona (builds/hermes/system-prompt.md).
    3. Upload robot-builder-complete.md as the workspace knowledge (see the Gemini build zip, or generate it).
EOF2
}

if have docker; then
  say "Docker is already installed — good."
else
  case "$OS" in
    Darwin) install_docker_mac;;
    Linux)  install_docker_linux;;
    *) info "Unsupported OS '$OS'. Install Docker manually, then re-run."; exit 1;;
  esac
fi

# ---------- wait for the Docker daemon ----------
say "Waiting for the Docker engine to be ready…"
for i in $(seq 1 60); do
  if docker info >/dev/null 2>&1; then info "Docker engine is up."; break; fi
  [ "$i" = 60 ] && { info "Docker isn't responding yet. On macOS, open Docker Desktop and wait for it to finish starting, then re-run."; exit 1; }
  sleep 2
done

# ---------- ROS 2 image ----------
say "Pulling the ROS 2 image (first time is a few hundred MB)…"
docker pull "$ROS_IMAGE"

say "Verifying ROS 2 runs inside the container…"
if docker run --rm "$ROS_IMAGE" ros2 --help >/dev/null 2>&1; then
  printf '\n\033[1;32m✓ Success — Docker and ROS 2 are working.\033[0m\n'
else
  info "The image pulled but the ROS 2 check failed. Try: docker run -it --rm $ROS_IMAGE bash"
  exit 1
fi

[ "$WITH_CHATBOT" = 1 ] && install_chatbot

cat <<EOF

Next steps:
  • Open a ROS 2 shell:   docker run -it --rm $ROS_IMAGE bash
  • Then inside it:       ros2 topic list
  • Full dev-shell (with your workspace + GUI) — see references/docker-and-environments.md
  • On Linux you can also install ROS 2 natively (apt) for hardware access — see ros.md

Ask the mentor: "set up a ROS 2 workspace and run the talker/listener demo".
EOF
