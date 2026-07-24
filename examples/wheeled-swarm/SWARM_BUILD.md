# Wheeled Robot Swarm — Build Guide

*Designed with the **Robot Builder** Claude skill · github.com/ShaunPrice/robot-builder-skill*

A **3-robot** swarm of small differential-drive rovers that hold formations and drive coordinated
patterns — for about the price of one hobby drone, and with the hard problem actually **solved**:
each robot wears an **ArUco fiducial**, one **overhead webcam** reads them all, and a laptop knows
every robot's position. A **distance sensor** on each robot handles local collision avoidance.

> ✅ **Why this is the achievable swarm.** The single thing that sinks most swarm projects is
> *localization* — how each robot knows where it and its neighbours are. Here it's cheap and real:
> the tags on the robots **are** the positioning system (a ~$25 webcam + printed paper tags). It's
> indoor, slow, can't fall out of the sky, and needs no radios-on-the-walls or motion-capture rig.
>
> ⚠️ **Status:** proven in **simulation** so far ([`wheeled_swarm_sim.py`](wheeled_swarm_sim.py)) —
> the firmware is untested reference code. **Not sponsored**, no vendor affiliation; prices approximate.

## How the swarm knows where everything is

1. **One overhead webcam** looks down at the play area (a table, a floor, a taped-off rectangle).
2. **Each robot wears a printed ArUco tag** (a unique black-and-white square) on its top.
3. On the laptop, **OpenCV detects every tag** and returns its centre and rotation → each robot's
   **(x, y, heading)** in one shared frame. That's a cheap, real "indoor GPS."
4. The **coordinator** ([`coordinator/swarm_coordinator.py`](coordinator/swarm_coordinator.py))
   turns those poses into a **velocity command (v, ω)** for each robot and sends it over **ESP-NOW**.
5. Each robot's **VL53L0X distance sensor** gives a local emergency stop if something's right in
   front — safety that doesn't depend on the camera or the network.

The camera closes the position loop; each robot is a thin actuator plus a safety reflex. That split
is what makes it work with $8 brains and no wheel encoders.

## Simulate first

[`wheeled_swarm_sim.py`](wheeled_swarm_sim.py) flies the whole mission in software — with the camera,
odometry drift, and distance-sensor avoidance modelled — before you buy anything. Result (3 robots):
**0 collisions, 1.3 cm formation hold, ~4 mm localisation error** (the camera keeps odometry drift
bounded). Mission: *scatter → gather into a triangle → translate → rotate → reform as a line → park.*

## Bill of materials — ONE robot

A **DIY 4-wheel robot** on a 3D-printed chassis. Because we fix these exact parts, all three robots
are **identical**. **AU $ prices are live from Core Electronics** (verified 2026‑07‑24 — check current);
US/UK are approximate from Adafruit / The Pi Hut (usually cheaper than AU).

| Part | Core (AU) | Qty | AU $ ea | AU $ | US $ approx |
|---|---|---:|---:|---:|---:|
| DC Gearbox **TT motor** 200 RPM 3–6 V | Adafruit | 4 | 7.35 | 29.40 | ~10 |
| **TT wheel** 65 mm | Adafruit | 4 | 4.95 | 19.80 | ~6 |
| **ESP32 dev board** (brain **+** ESP-NOW radio) | XIAO ESP32‑C3 | 1 | 10.65 | 10.65 | ~7 |
| **DRV8833** dual motor driver (2 left + 2 right motors) | Adafruit | 1 | 11.95 | 11.95 | ~5 |
| **HC‑SR04** ultrasonic distance sensor (local avoidance) | Core | 1 | 1.95 | 1.95 | ~2 |
| 4×AA holder + NiMH cells (or 2× 18650) | — | 1 | ~7 | ~7 | ~5 |
| Jumper wires + headers + heatshrink | — | 1 | ~5 | ~5 | ~4 |
| **3D-printed chassis** ([`cad/chassis.stl`](cad/chassis.stl)) | filament | 1 | ~1 | ~1 | ~1 |
| Printed **ArUco tag** ([`cad/make_tags.py`](cad/make_tags.py)) | paper | 1 | free | 0 | 0 |
| **PER ROBOT** | | | | **≈ AU $87** | **≈ US $40** |

### Shared gear (buy once for the whole swarm)

| Part | AU $ | Notes |
|---|---:|---|
| USB overhead webcam (720p+) | ~40 | The localisation system — or use a phone / a webcam you own |
| Webcam mount / small tripod | ~18 | Looks straight down at the play area |
| Ground-station laptop | — | Runs the coordinator (you have one) |

### What it costs, end to end

| | AU $ |
|---|---:|
| **One robot** | ~$87 |
| **3-robot swarm + webcam** | **~$300** (~$260 if you already own a webcam) |

*Prefer no soldering/printing? Two turnkey ESP32 4-wheel options at Core: **Waveshare WAVE ROVER**
(WS‑25376, $179.95, 4WD + onboard ESP32) or **ACEBOTT ESP32 Smart Car** (CE10126, $129.95, mecanum,
ultrasonic included).*

## Safety (gentle, but not zero)

- **Batteries:** if you use LiPo instead of AA, treat it with respect — charge on a LiPo bag, never
  a puffed pack. AA/NiMH is the simpler, safer first choice here.
- **Wheels off the ground / robot held** for the first powered test, and **verify each wheel spins
  the right way** before it can drive off the table.
- **Play area with a lip or on the floor** — a camera-tracked robot that loses its tag (glare,
  occlusion) will hold its last command; keep runs short and keep a hand near the power.
- **One kill for all:** the coordinator's `Ctrl-C` disarms every robot; each robot also fails safe
  (motors off) if it stops hearing the coordinator for 400 ms.

## Build order

1. **Simulate** the swarm (no hardware) — prove the coordination.
2. **Print** the tags and a chassis; **flash one robot**, wheels up, verify motors + ToF.
3. **Set up the camera** looking down; confirm the coordinator detects all three tags.
4. **Drive one robot** from the coordinator, then add the second and third.
5. **Run the mission** — the same one you saw in simulation, now for real.

---

**Repo:** https://github.com/ShaunPrice/robot-builder-skill (this build lives in `examples/wheeled-swarm`).
Built with the Robot Builder skill — localisation solved *first*, then the platform chosen to serve it.
