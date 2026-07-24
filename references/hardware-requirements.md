# Host hardware requirements: the machine YOU build on

The robot has its own brain — a Pi, a Jetson, or a flight controller (see
compute-platforms.md). *This* file is about the other computer: your development and
training machine, the laptop or desktop where you flash cards, write code, run simulators,
and train models. New builders assume robotics needs a monster workstation. It mostly does
not. Around 90% of everything in this skill — flashing an SD card, blinking a GPIO pin,
writing ROS nodes, flying SITL, tuning a PID — runs fine on an ordinary laptop with no
discrete GPU. A hungry 10% (Isaac Sim, reinforcement learning, vision-model *training*,
big local LLMs) needs a real NVIDIA GPU, and that you can rent by the hour or SSH into one
desktop box (see docker-and-environments.md for serving it as a connectable machine).

## Task → hardware table

| Task | Minimum | Recommended | GPU / VRAM | Cloud option |
|---|---|---|---|---|
| SD-card flash, basic Python, GPIO | Any laptop (Mac/Win/Linux) | Same | None | n/a |
| Arduino / ESP32 / PlatformIO | Any laptop + a USB port | Same | None | n/a (needs the physical board) |
| ROS 2 development | Ubuntu LTS native, or Docker on Mac/Win (docker-and-environments.md); 8 GB RAM | 16 GB RAM, Ubuntu native | None for the basics | Cloud Ubuntu VM for headless nodes |
| Gazebo simulation | Linux + 16 GB RAM | Linux + a mid GPU (smoother rendering) | Any GPU helps; not required | Linux GPU VM (RunPod/Lambda) |
| ArduPilot / PX4 SITL | Any CPU, any OS | 4-core CPU | None | Any cheap CPU VM |
| YOLO inference-dev | CPU (slow, a few FPS) | Any NVIDIA GPU | 4 GB+ helps a lot | Colab free tier |
| YOLO / vision **training** | NVIDIA GPU 8 GB VRAM | RTX 3060 12 GB (the sweet spot) | 8–12 GB NVIDIA | Colab / RunPod / vast.ai |
| RL training (PyBullet / MuJoCo) | Multi-core CPU (small tasks) | NVIDIA GPU for speed | Optional, helps a lot | Rent a GPU for long runs |
| Isaac Sim / Isaac Lab | **NVIDIA RTX**, 3070-class 8 GB+ | RTX 4090/5090 24–32 GB | RTX **required** — the hard wall | NGC image on a cloud RTX box |
| Local LLM / VLA inference | Jetson Orin 8 GB (7–8B Q4) on-robot; NVIDIA GPU on desktop | Bigger GPU, or Apple-Silicon Mac 32 GB+ unified | Sized to the model | Hosted API for non-motion use |
| LLM fine-tuning | Big NVIDIA GPU (24 GB+) | Multi-GPU or rent | 24 GB+ | Rent — almost always cheaper |
| Blender render | Any GPU | CUDA/OptiX NVIDIA, or Mac Metal | Helps enormously | Cloud render |
| Browser 3D drafting (design-and-3d.md) | Any browser | Same | None | n/a — runs in the tab |

## The OS story, honestly

- **macOS** — a genuinely great dev machine, and quietly excellent at *local LLMs*: unified
  memory lets a 32 GB+ Apple-Silicon Mac run 7–13B models well via Ollama, llama.cpp, or
  MLX, no discrete GPU needed. The catch is **no CUDA**. That means no native Isaac Sim and
  no CUDA training on the Mac itself. The fix: run ROS 2 in Docker (docker-and-environments.md),
  and reach for a Linux or cloud box whenever you need CUDA. A Mac is a fine cockpit; it is
  not your training rig.
- **Windows** — the solid all-rounder. WSL2 + Docker gives you clean ROS 2, and Windows
  *has* CUDA, so vision training and Isaac Sim run natively on the same machine. If you own
  one Windows box with an RTX card, you can do essentially everything in this skill on it.
- **Linux / Ubuntu LTS** — the reference platform. Native ROS 2, native CUDA, every simulator
  targets it first, and it is what actually ships on the robot's Pi/Jetson. Anything serious
  eventually lives here. Match the Ubuntu LTS to your ROS 2 release (ros.md).

One trap that catches everyone doing hardware-in-the-loop work: **passing real USB devices
into containers — serial adapters, lidar, depth cameras — is Linux-native only.** Docker
Desktop on Mac and Windows runs Linux containers inside a VM that cannot easily reach host
USB, so `--device /dev/ttyUSB0` simply is not there. Do driver-level and hardware-in-the-loop
development on a Linux box, or on the Pi itself. Mac/Windows Docker is for building,
learning, and pure simulation — not for talking to a plugged-in lidar.

## Renting a GPU instead of buying one

For the GPU-hungry 10%, you do not need to own a 5090. Rent one by the hour:

- **Google Colab** — free tier for small YOLO/RL experiments; Pro for longer sessions.
  Zero setup, dies on idle — fine for learning, poor for multi-day runs.
- **RunPod / Lambda / vast.ai** — rent an RTX 4090/A100/5090 for roughly $0.30–$2/hour;
  Isaac Sim and long training runs go here. Lambda and RunPod are tidier; vast.ai is
  cheapest and rawest.
- Keep cloud credentials **scoped and short-lived** — a leaked training key can run up a
  bill or worse. The security.md rules apply to cloud GPUs exactly as they do to the robot.
- **The robot never depends on cloud for control.** Cloud is for *training*; inference for
  anything motion-critical runs on-robot (ai-ml.md latency math, and the "AI proposes, a
  deterministic layer disposes" rule in security.md and ai-ml.md). A dropped connection must
  never be able to stall a control loop.

## VRAM cheat-sheet (rough, for planning)

| Model / task | Approx VRAM | Notes |
|---|---|---|
| YOLOv8n/s **inference** | 2–4 GB | Runs on almost anything; CPU works, just slowly |
| YOLOv8m/l **training** | 8–12 GB | RTX 3060 12 GB is the value pick |
| YOLOv8x training / big batches | 16–24 GB | Or shrink batch size and wait |
| 7–8B LLM, 4-bit (Q4) | ~6–8 GB | Orin Nano 8 GB or any modern GPU; Mac 16 GB unified |
| 13B LLM, Q4 | ~10–12 GB | Mac 32 GB unified is comfortable here |
| 70B LLM, Q4 | ~40–48 GB | Multi-GPU, a 48 GB card, or a 64 GB+ Mac; usually rent |
| LLM LoRA fine-tune (7B) | ~16–24 GB | Full fine-tune needs far more — rent |
| Isaac Lab parallel RL | 8 GB starts, 24 GB+ scales | More VRAM = more parallel envs = faster policies |

Quantization (Q4/Q5/Q8) is the main lever: a Q4 model needs roughly a quarter of the VRAM
of the same model at 16-bit (Q8 is about half), for a small quality cost. When a model
"won't fit", quantize before you rent.

## Bottom line

Buy nothing extra to *start*. Your existing laptop flashes cards, writes ROS and MCU code,
runs SITL and Gazebo, and does YOLO inference-dev — that covers most of the build ladder.
When you hit the GPU-hungry 10% — Isaac, RL at scale, vision-model training, large local
LLMs — you have three honest choices: rent a cloud GPU by the hour, buy one desktop RTX box
and SSH into it, or (for local LLMs specifically) lean on an Apple-Silicon Mac's unified
memory. The one genuine hard wall is Isaac Sim/Lab: it needs an NVIDIA RTX GPU and will not
run on macOS at all — plan to rent or to use a Linux/Windows RTX machine for that work.

See compute-platforms.md (the robot's own brain), docker-and-environments.md (reproducible
stacks and serving a remote GPU box you can connect to), simulation-and-gyms.md (what each
simulator actually demands), ai-ml.md (on-robot vs off-robot inference), and security.md
(scoping cloud credentials and keeping control off the network).
