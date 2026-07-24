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

Approximate **2026 street prices**, local currency per region. Electronics from **Core Electronics
(AU) / Adafruit (US) / The Pi Hut (UK)**; the webcam from anywhere. Always check current pricing.

| Part | What it does | US $ | UK £ | AU $ |
|---|---|---:|---:|---:|
| ESP32 dev board | Robot brain **and** ESP-NOW radio | 8 | 7 | 11 |
| 2 × TT gear motor + wheel | Drive | 6 | 5 | 9 |
| DRV8833 motor driver | Lets the ESP32 drive the motors | 5 | 5 | 9 |
| VL53L0X time-of-flight sensor | Local obstacle / collision stop | 6 | 6 | 11 |
| Ball caster | Third contact point (front) | 2 | 2 | 4 |
| 4 × AA holder + NiMH cells | Power | 6 | 5 | 9 |
| Jumper wires + headers | Wiring | 3 | 3 | 5 |
| 3D-printed chassis | Holds it together ([`cad/chassis.stl`](cad/chassis.stl)) | 1 | 1 | 1 |
| Printed ArUco tag | The fiducial ([`cad/make_tags.py`](cad/make_tags.py)) | — | — | — |
| **PER ROBOT** | | **≈ $37** | **≈ £34** | **≈ AU $59** |

### Shared gear (buy once for the whole swarm)

| Part | US $ | UK £ | AU $ | Notes |
|---|---:|---:|---:|---|
| USB overhead webcam (720p+) | 25 | 22 | 40 | The localisation system |
| Ceiling / tripod camera mount | 10 | 9 | 18 | Looks straight down at the area |
| Ground-station laptop | — | — | — | Runs the coordinator (you have one) |

### What it costs, end to end

| | US $ | UK £ | AU $ |
|---|---:|---:|---:|
| **One robot** | ~$37 | ~£34 | ~$59 |
| **3-robot swarm + shared gear** | **~$146** | **~£133** | **~$235** |

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
