<#
  Robot Builder - beginner dev-environment bootstrap for Windows.

  Sets up the safe, universal starting point: WSL2 + Docker Desktop + a working ROS 2
  container. It does NOT install a CUDA/Isaac stack (opt-in, machine-specific - see
  references/hardware-requirements.md) and never touches a robot's Pi/Jetson.

  Usage (in an ADMIN PowerShell):
      .\bootstrap-windows.ps1          # interactive: shows each step, asks before installing
      .\bootstrap-windows.ps1 -Yes     # unattended

  Every command here is also documented step-by-step in references/getting-started.md and
  references/docker-and-environments.md - this script is a convenience, not a black box.
#>
param([switch]$Yes, [switch]$WithChatbot)

$ErrorActionPreference = "Stop"
$RosImage = if ($env:ROS_IMAGE) { $env:ROS_IMAGE } else { "osrf/ros:jazzy-desktop" }

function Say ($m){ Write-Host "`n> $m" -ForegroundColor Cyan }
function Info($m){ Write-Host "  $m" }
function Ask ($m){ if ($Yes){ return $true }; $a = Read-Host "  $m [y/N]"; return ($a -match '^(y|yes)$') }
function Have($c){ return [bool](Get-Command $c -ErrorAction SilentlyContinue) }

# --- must be admin (WSL + Docker Desktop install need it) ---
$admin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()
         ).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
if (-not $admin){ Write-Host "Run this in an ADMIN PowerShell (right-click > Run as administrator)." -ForegroundColor Yellow; exit 1 }

Say "Robot Builder setup - Windows"
Info "Target: WSL2 + Docker Desktop + the ROS 2 image '$RosImage'. Nothing else is installed."

# --- WSL2 (Docker Desktop's Linux backend) ---
$wsl = (wsl.exe --status) 2>$null
if ($LASTEXITCODE -ne 0){
  Say "Enabling WSL2 (Windows Subsystem for Linux) + Ubuntu..."
  if (Ask "Run 'wsl --install' now? (a reboot may be required afterwards)"){
    wsl.exe --install
    Info "If Windows asks you to reboot, do so, then re-run this script to finish."
  } else { Info "Skipping. Enable WSL2 manually, then re-run."; exit 1 }
} else { Say "WSL2 is already available - good." }

# --- Docker Desktop via winget ---
if (Have "docker"){
  Say "Docker is already installed - good."
} elseif (Have "winget"){
  Say "Installing Docker Desktop via winget (official package)..."
  if (Ask "Proceed?"){
    winget install -e --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements
    Info "Start Docker Desktop from the Start menu and let it finish first-run setup (enable the WSL2 backend)."
  } else { Info "Skipping. Install Docker Desktop yourself, then re-run."; exit 1 }
} else {
  Info "winget not found. Install Docker Desktop from docker.com/products/docker-desktop, then re-run."
  exit 1
}

# --- wait for the Docker daemon ---
Say "Waiting for the Docker engine to be ready (start Docker Desktop if it isn't running)..."
$ok = $false
foreach ($i in 1..60){ docker info *> $null; if ($LASTEXITCODE -eq 0){ $ok=$true; Info "Docker engine is up."; break }; Start-Sleep 2 }
if (-not $ok){ Info "Docker isn't responding. Open Docker Desktop, wait for it to start, then re-run."; exit 1 }

# --- ROS 2 image ---
Say "Pulling the ROS 2 image (first time is a few hundred MB)..."
docker pull $RosImage

Say "Verifying ROS 2 runs inside the container..."
docker run --rm $RosImage ros2 --help *> $null
if ($LASTEXITCODE -eq 0){
  Write-Host "`n[OK] Success - Docker and ROS 2 are working." -ForegroundColor Green
} else {
  Info "The image pulled but the ROS 2 check failed. Try: docker run -it --rm $RosImage bash"
  exit 1
}

if ($WithChatbot){
  Say "Optional: local no-Docker chatbot backend (Ollama + a small model)..."
  if (-not (Have "ollama")){
    if (Have "winget"){ if (Ask "Install Ollama via winget?"){ winget install -e --id Ollama.Ollama --accept-source-agreements --accept-package-agreements } }
    else { Info "Install Ollama from ollama.com, then re-run with -WithChatbot." }
  }
  if (Have "ollama"){ Info "Pulling a small local model (llama3.2:3b, ~2 GB)..."; ollama pull llama3.2:3b }
  Info "Install the AnythingLLM desktop app from anythingllm.com - the no-Docker chat UI."
  Write-Host @"
  Your local mentor (offline, no Docker, no subscription):
    1. Open AnythingLLM, create a Workspace, point it at Ollama (model: llama3.2:3b).
    2. Set the workspace system prompt to builds\hermes\system-prompt.md.
    3. Upload robot-builder-complete.md as the workspace knowledge.
"@
}

Write-Host @"

Next steps:
  * Open a ROS 2 shell:   docker run -it --rm $RosImage bash
  * Then inside it:       ros2 topic list
  * Full dev-shell (workspace + GUI) - see references/docker-and-environments.md

Ask the mentor: "set up a ROS 2 workspace and run the talker/listener demo".
"@
