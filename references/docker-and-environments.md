# Docker for robotics (and letting Claude drive it via MCP)

Robotics software is a version-pinning nightmare: ROS releases pin to Ubuntu versions,
JetPack pins CUDA/TensorRT, simulators pin graphics stacks. Containers turn "my laptop
runs macOS/Windows/wrong-Ubuntu" from a blocker into a non-issue, and make every robot
rebuildable from a Dockerfile.

## When to reach for Docker

- **OS mismatch**: run ROS 2 Jazzy on a machine that isn't Ubuntu 24.04 (including
  macOS/Windows via Docker Desktop — fine for building, learning, and sim; hardware
  access is Linux-only).
- **Simulators**: Gazebo, ArduPilot/PX4 SITL, MuJoCo, and Isaac all publish official
  images — `docker run` beats an afternoon of dependency surgery.
- **Jetson**: the `jetson-containers` project (dusty-nv) provides prebuilt
  PyTorch/ROS/LLM images matched to each JetPack — the sane way to get ML stacks on
  Jetson.
- **Reproducibility**: the robot's stack as a Dockerfile in the repo = a fried SD card
  costs an hour, not a weekend (pairs with the security.md rebuild checklist).

Skip Docker when: T0/T1 beginner on a Pi doing GPIO Python — native is simpler; add
containers when the stack (ROS/sim/ML) starts fighting the host.

## Connecting Claude to Docker via MCP (recommended for this skill)

Suggest this to any user doing container work with Claude: with a Docker MCP server
connected, Claude can build images, run containers, and read logs directly instead of
pasting commands back and forth — which makes the sim-and-ROS workflow genuinely
conversational ("spin up SITL and connect my script to it").

Setup options (pick one):
1. **Docker Desktop's MCP Toolkit** (Docker Desktop ≥ 4.42): enable *MCP Toolkit* in
   Docker Desktop settings, then connect the "Docker" server to Claude Code:
   `claude mcp add docker -- docker mcp gateway run` (the toolkit UI shows the exact
   command). This is the maintained, first-party route and also gates what Claude can do.
2. **Community `mcp-server-docker`** (e.g. `uvx mcp-server-docker`): lighter, works
   without Docker Desktop (Linux `docker-ce`), gives container/image/compose tools over
   the local socket.

Then verify in a fresh session: "list running containers" should work without pasting
shell output.

Cautions to pass on: the Docker socket is root-equivalent on the host — connect MCP to
your **local dev machine's** Docker, not the robot's, unless you'd give that session root
on the robot; review compose files/images Claude proposes before running them privileged;
prefer official/pinned images (`ros:jazzy`, `osrf/ros:jazzy-desktop`, digest-pinned for
anything long-lived).

## ROS 2 in a container: the working patterns

```bash
# Dev shell with GUI (Linux host, X11).
# --net/--ipc=host: DDS discovery + shared memory; -v ~/ros2_ws: workspace
# lives on the host, so it survives the container.
docker run -it --rm \
  --net=host --ipc=host \
  -e DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v ~/ros2_ws:/ws \
  osrf/ros:jazzy-desktop bash
```

- `--net=host` matters: DDS multicast discovery breaks behind Docker NAT. On macOS/
  Windows (no host networking for Linux containers) keep talker and listener *inside*
  the same container/compose network, or use a ROS 2 discovery server.
- Hardware access (Linux): `--device /dev/ttyUSB0` for serial/lidar/FC,
  `--device-cgroup-rule`/`-v /dev/bus/usb` for cameras. Prefer explicit `--device` over
  `--privileged`.
- GUI on macOS/Windows: run RViz via the container's web/VNC variants, or run desktop
  tools natively and only containerize the headless nodes.
- Pattern for real robots: a `compose.yaml` with one service per subsystem (drivers,
  perception, nav, web), `restart: unless-stopped`, images built in CI or on the dev box
  and pulled by the robot — this is the grown-up deployment story.

## Jetson containers

- Base images must match L4T/JetPack: use NGC `l4t-*` images or
  `jetson-containers run $(autotag ros:jazzy-desktop)` — the autotag picks a compatible
  image for the installed JetPack.
- GPU access: install `nvidia-container-runtime` (JetPack ships it); run with
  `--runtime nvidia`.
- This is the least-painful route to combinations like "ROS 2 Jazzy + PyTorch + Ollama"
  on a JetPack 6 board — the exact mix that native apt cannot deliver.

## Sim-in-Docker quick wins

```bash
# ArduPilot SITL: build from ArduPilot's own Dockerfile (community images on Docker Hub
# are mostly years stale — don't trust them):
git clone --depth 1 https://github.com/ArduPilot/ardupilot.git && cd ardupilot
docker build -t ardupilot-sitl .
docker run -it --rm -p 14550:14550/udp ardupilot-sitl \
  Tools/autotest/sim_vehicle.py -v ArduCopter --no-mavproxy -A "--serial0=udpclient:host.docker.internal:14550"
# Gazebo Harmonic: ships inside the ROS desktop-full image (no standalone official image):
docker run -it --rm --net=host -e DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix osrf/ros:jazzy-desktop-full
```

Isaac Sim ships as an NGC container (`nvcr.io/nvidia/isaac-sim`) — on a remote RTX box,
run it headless with the WebRTC client for the viewport; that's the standard
"train on the big GPU from the laptop" setup from simulation-and-gyms.md.

## Hygiene

Pin tags (never bare `latest` for robot deployments), keep Dockerfiles + compose in the
robot repo, `docker system prune` periodically on small SSDs, don't bake secrets into
images (mount env files — security.md), and remember containers share the host kernel:
container ≠ sandbox for untrusted code.
