# Setup and the cloud-first path: start with nothing, grow into a full rig

The biggest thing standing between a curious beginner and their first robot is usually not
money or talent — it is the belief that you must install a mountain of software first. You
do not. This module is the on-ramp: **start entirely in the cloud with zero installs, do
real robotics today, and add local machinery only when you have a reason to.** It also
covers the automated installers that set up a full environment for you when you are ready,
with a manual path always available as the fallback.

A guiding rule for the mentor using this skill: **a beginner may not know the words.** URDF,
ROS, PID, SLAM, lidar, ESC, IMU — define each one the first time it appears, and prefer
plain labels ("save the robot file") over jargon ("export URDF"). A control someone does
not understand is a dead end.

## Start in the cloud — zero install, real work today

With nothing but a browser (even a Chromebook), a beginner can already do four of the
build ladder's rungs:

| Want to… | Do it in the browser with | Installs |
|---|---|---|
| **Design** a robot and see it in 3D | the Robot Drafter (see design-and-3d.md) | none |
| **Learn ROS 2 and write code** | GitHub Codespaces or Gitpod — browser VS Code on an Ubuntu container; run the `ros:jazzy` image inside it | none (a free account) |
| **Fly a simulator** | ArduPilot / PX4 SITL on any small cloud Linux VM (see simulation-and-gyms.md) | none |
| **Train a vision model** | Google Colab — a free browser notebook with a GPU, for YOLO or small RL (see hardware-requirements.md) | none |
| **Rent serious GPU** by the hour | RunPod / Lambda / vast.ai for Isaac Sim or heavy training | none |
| **Talk to the mentor** | Claude, ChatGPT, or Gemini | none |

So the honest starting advice is: **do not buy anything to begin.** Design a robot, learn
ROS, run a simulator, and train a model in the cloud first. Buy hardware once you know what
you are building and why — that is the cheapest possible way to be wrong (design-and-3d.md
makes the same point about parts).

## The expansion ladder: cloud → local → GPU → robot

Each rung reuses the work from the one before — the URDF you drafted, the ROS nodes you
wrote, the model you trained all carry forward. You climb only as far as your project needs.

1. **Cloud sandbox** (browser, zero install) — design, learn, code, simulate, train.
2. **Local Docker** on your own laptop (Mac/Windows/Linux) — the same ROS and simulators,
   now offline and free of a running meter (see docker-and-environments.md).
3. **Native Linux** (Ubuntu LTS) — full native ROS 2 + CUDA, the reference platform for
   anything serious, and what actually ships on the robot's Pi/Jetson (ros.md).
4. **A GPU box** you own or rent, served as a connectable Docker-MCP server so Claude can
   drive heavy sim/training/rendering on it while you work from a light laptop
   (docker-and-environments.md § Advanced; hardware-requirements.md sizes the box).
5. **The robot itself** — deploy to the Pi or Jetson (compute-platforms.md).

Nothing is wasted moving up: a beginner who trained a detector in Colab and drafted a rover
in the browser arrives at their first Pi with a model and a design already in hand.

## Automated installers — one command, with a manual/scripted fallback

When you are ready to bring it local, the skill can set up the environment for you rather
than making you follow a twenty-step wiki. Two ways to run it:

- **Let Claude do it** — with a Docker or terminal MCP connected (docker-and-environments.md),
  Claude runs the setup and reads back the results, adapting it to your machine.
- **Run the bundled script yourself** — the repo ships idempotent bootstrap scripts:
  - **macOS / Linux:** `scripts/setup/bootstrap-unix.sh` — installs Docker (Homebrew's
    Docker Desktop on macOS; `docker-ce` on Ubuntu/Debian), pulls the ROS 2 image, and
    verifies it runs. Re-running it is safe — it skips whatever is already present.
  - **Windows:** `scripts/setup/bootstrap-windows.ps1` — enables WSL2, installs Docker
    Desktop via `winget`, and pulls the ROS 2 image.

Each script **tells you what it will do and asks before installing**, prints every command,
and finishes with a one-line "it works" check. Pass `--yes` (or `-Yes`) for an unattended
run.

**The manual/scripted path is always open.** Every command the scripts run is also spelled
out step-by-step in getting-started.md and docker-and-environments.md, so you can copy-paste
them yourself, audit exactly what happens, or hand the script to Claude and ask it to
customize — a different ROS distro, a bundled simulator, a local LLM via Ollama. The
automation is a convenience, never a black box.

**What the installers deliberately do *not* do:** they do not touch your robot's Pi/Jetson,
and they do not install a full CUDA/Isaac stack — that is opt-in and machine-specific (see
hardware-requirements.md), because it is large and easy to get wrong. They set up the safe,
universal beginner dev environment: Docker plus a working ROS 2 container.

## Safety of automated installs

An installer runs code on your machine, so treat it like any downloaded installer
(security.md's supply-chain rules apply):

- The scripts run as your normal user; Docker Desktop asks for admin **once**, through its
  own signed installer. They are short and live in the repo — read one before you run it.
- They wrap the **official** installers (Homebrew, Docker Desktop, `winget`, the Docker
  convenience script) rather than fetching random binaries, and pin the ROS image tag.
- Nothing here needs, or asks for, credentials. If a "setup script" for robotics ever wants
  an API key or a password up front, stop and question it.

## Where to go next

Design first in design-and-3d.md, pick a host with hardware-requirements.md, flash and
first-boot with getting-started.md, and containerize or serve heavy compute with
docker-and-environments.md. The cloud-first order means you will have used ROS and a
simulator before you ever plug anything in.

## Which chatbot should I run this mentor in?

Because the skill is a persona prompt plus one knowledge file (the consolidated
`robot-builder-complete.md`), almost any chatbot that lets you set a system prompt and
attach documents can host it. What changes across users is where the model runs and what
it costs — match it to the machine:

- **Cheapest, works on any machine (Windows 11 Home, a basic Mac, a Chromebook) — a free
  cloud chatbot, zero install.** Open a free chat in Claude, ChatGPT, or Gemini, attach
  `robot-builder-complete.md`, paste the persona line, and go. For a persistent version, a
  Claude skill / Custom GPT / Gemini Gem (the repo's `builds/`) — note that *creating* one
  can need a low paid tier, though using it is cheap.
- **Local, no Docker, no subscription (privacy/offline).** A native desktop app is the
  answer. **AnythingLLM** fits best: a workspace is exactly "a system prompt + uploaded
  documents", it runs a small local model or a cheap API key, and it installs on
  Windows/Mac/Linux with **no Docker**. Alternatives: **Jan, LM Studio, GPT4All, Msty**.
  The local model engine underneath is **Ollama** (native installers, no Docker). The setup
  scripts' `--with-chatbot` flag installs Ollama plus a small model for you. On a weak
  laptop only 3–4B models run, and slowly; an Apple-Silicon Mac runs 7–8B comfortably; if
  local is too weak, plug a cheap **OpenRouter or Groq** API key into the same app for
  cloud-grade answers at cents per session. (Windows 11 Home *can* run Docker/WSL2 if you
  ever want it — you simply do not need it for this.)
- **Experienced, with real compute (AWS/Azure, a gaming rig, a university cluster).** Larger
  local models via **Ollama / LM Studio / vLLM**, fronted by **Open WebUI** or **LibreChat**
  (Docker is fine at this tier); or the plain **API route** for the best quality; or the
  repo's Hermes/OpenClaw adapters plus the Docker-MCP compute-server model
  (docker-and-environments.md) for agentic, tool-using control.

Every tier "installs the skill" the same way — **one file plus one persona prompt** — which
is exactly why the whole skill is also shipped as that single consolidated file.
