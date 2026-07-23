# Compute platforms: microcontroller → Pi → Jetson → autopilot

Choosing the robot's brain(s). Most robots beyond T1 end up with **two** brains: a
real-time layer (microcontroller or flight controller) and a "thinking" layer (Pi/Jetson).
That split is the single most useful architecture idea in hobby robotics.

## The two-brain pattern

```
[Pi / Jetson]  ── USB/UART ──  [MCU or flight controller]
 perception,                     motor PWM, encoders, IMU,
 planning, AI,                   failsafes, RC passthrough
 networking                      (hard real-time, crashes never)
```

- The high-level computer can crash, reboot, or garbage-collect without the robot losing
  motor control or failsafes.
- Protocols: plain serial (custom or Firmata), **micro-ROS** (MCU appears as ROS 2 nodes),
  or **MAVLink** (when the low level is an ArduPilot/PX4 autopilot).
- Beginner version: skip the MCU, drive motors from the Pi directly (fine for T1). Add the
  MCU when you add encoders/PID or anything safety-relevant.

## Microcontrollers (the reflexes)

| Board | ~Price | Why pick it |
|---|---|---|
| ESP32 / ESP32-S3 | $5–10 | Wi-Fi+BT built in, dual core, huge community. Default choice. Can even be the *only* brain of a Wi-Fi robot |
| Raspberry Pi Pico 2 (W) | $5–7 | PIO state machines are magic for encoders/PWM; great docs; MicroPython or C |
| Arduino Uno R4 / Nano | $10–25 | Easiest tutorials; 5 V logic tolerant; slow |
| Teensy 4.x | $24–32 | 600 MHz beast — when one MCU must do many encoders + control loops |
| STM32 "Blackpill" | $6 | Cheap ARM; steeper toolchain |

Firmware styles: Arduino C++ (portable, most examples), MicroPython/CircuitPython (fastest
iteration, fine for ≤~100 Hz loops), PlatformIO (proper projects, version-controlled).

## Single-board computers (the thinker, budget tier)

- **Raspberry Pi 5** (4/8/16 GB, $60–120): the default robot SBC. Real OS, ROS 2 runs
  well, camera stack is excellent. No CUDA — heavy vision runs at low FPS on CPU, so pair
  with an **AI-accelerated camera (OAK-D)**, a **Hailo AI HAT (Hailo-8L 13 TOPS ~$70, or Hailo-8 AI HAT+ 26 TOPS ~$110)**, or
  accept small models (YOLOv8n at ~5–10 FPS CPU).
- **Pi 4**: fine, cheaper, slower. **Pi Zero 2 W**: tiny builds, camera streaming, light
  logic only.
- Alternatives (Orange Pi 5, Rock 5B): more raw speed, NPUs with fiddly toolchains, far
  less community. Only for users who enjoy that.
- Power: Pi 5 wants 5 V/5 A — from a battery use a quality buck converter/UBEC rated
  ≥5 A continuous (undervoltage = mystery crashes; this bites almost everyone).

## NVIDIA Jetson (the thinker, AI tier)

Jetson = ARM CPU + real NVIDIA GPU + CUDA/TensorRT. It's what you buy when models must run
*on* the robot.

| Model | TOPS | ~Price | Fit |
|---|---|---|---|
| Orin Nano Super devkit | 67 | $249 | The hobby AI default. YOLO @ 30–100+ FPS in TensorRT, small LLMs/VLMs (≤8B quantized) locally |
| Orin NX 8/16 GB | 70–157 | $400–700 | More headroom, same software |
| AGX Orin 32/64 GB | 200–275 | $1,000–2,000 | Multiple cameras + big models; research rigs |

Jetson realities to warn users about:
- **Flash to NVMe, not microSD** (see getting-started.md). Budget an SSD.
- **JetPack version pins everything**: CUDA, TensorRT, PyTorch wheels must match the
  JetPack/L4T version. Install PyTorch from NVIDIA's Jetson wheels or use NGC/`jetson-containers`
  Docker images — `pip install torch` from PyPI will not have CUDA on Jetson.
- `jtop` for monitoring; `sudo nvpmodel -m 0` + `sudo jetson_clocks` for max performance
  (mind the power budget on battery); Orin Nano Super mode needs the 25 W profile.
- Peripherals are 3.3 V logic like the Pi, but the GPIO library differs (`Jetson.GPIO`).
- Ubuntu-based, so ROS 2 installs natively and well.

Cloud vs edge: training happens off-robot (PC with GPU, or cloud); inference happens
on-robot. Don't let users plan on "the robot calls a cloud vision API" for anything
motion-critical — see ai-ml.md for latency math.

## Flight controllers / autopilots (the third kind of brain)

For air and water (and GPS-waypoint ground rovers), don't reinvent state estimation —
use an autopilot board running mature firmware:

| Firmware | Vehicles | Character |
|---|---|---|
| **ArduPilot** | Copter, Plane, Rover, Sub, Heli, Boat — everything | Most versatile, best for autonomy missions, huge docs. Default recommendation for this skill |
| **PX4** | Copter, planes, VTOL | Research/industry flavor, tight ROS 2 integration (uXRCE-DDS) |
| **Betaflight** | FPV multirotors only | Manual flight performance, racing/freestyle. Not an autonomy platform |

Hardware: Pixhawk 6C/6X (~$200–350), Holybro Kakute/SpeedyBee (~$40–80, Betaflight or
ArduPilot depending on board), Matek boards (great ArduPilot value ~$60–120). All contain
IMU/baro; add GPS+compass module for outdoor autonomy.

**Companion pattern**: Pi/Jetson connects to the autopilot over UART/USB speaking MAVLink.
- Python: `pymavlink` or `MAVSDK-Python` (async, clean) — arm, set modes, push waypoints,
  stream position.
- ROS 2: `mavros` (ArduPilot) or PX4's uXRCE-DDS bridge.
- The autopilot always retains failsafes (RC override, geofence, battery RTL) — the
  companion is advisory. This is the air/water version of "AI never gets direct actuator
  authority".

## Choosing, quickly

- T0–T1 ground: ESP32 **or** Pi alone.
- T2 ground/water autonomy: Pi 5 (+ optional MCU for encoders/PID).
- Any serious vision/AI on-robot: Jetson Orin Nano Super.
- Anything that flies (beyond a toy): flight controller running ArduPilot/PX4/Betaflight;
  add Pi/Jetson companion only when the mission needs vision/AI.
- Sub/boat: ArduPilot (ArduSub/Rover) + Pi companion is the BlueROV-proven stack.
