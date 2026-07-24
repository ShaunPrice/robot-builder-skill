# Low-Cost Flying Robot Swarm — Build Guide

*Designed with the **Robot Builder** Claude skill · github.com/ShaunPrice/robot-builder-skill*

A 3–5 unit swarm of tiny ESP32 quadcopters you can **simulate first, then build for about the
price of one shop-bought drone.** Every coordination behaviour is proven in a physics simulator
before a single motor is bought — the skill's rule for anything that flies.

> ⚠️ **Status & disclosure.** This design has been **fully developed and proven in simulation, but
> has *not* been built or flight-tested on real hardware.** Treat it as a software-tested blueprint —
> a head start, not a guarantee. If you build it, do so at your own risk: props off on the bench,
> LiPos in a fire bag, fly netted, and follow your local drone rules.
> **Nothing here is sponsored, and the author has no affiliation with any vendor mentioned** — they're
> simply where the parts happen to be. Prices are approximate; always check current pricing.

---

## 1. What we're building — and why this platform

| Platform | Per-unit | Skill level | Why / why not |
|---|---|---|---|
| **ESP32 brushed micro-quad** ⭐ *our hero* | **~US $40** | Intermediate | Cheapest *credible* flyer that can run open firmware + a mesh radio. Runs [Espressif **ESP-Drone**](https://github.com/espressif/esp-drone) (open source). ESP-NOW mesh is built into the chip — no extra radio. |
| Indoor **blimp** swarm | ~US $50–120 | Beginner | The *safest* many-at-once flyer (helium, slow, can't hurt anyone). Pick this if you want zero-risk. Same ESP32 + ESP-NOW brain. |
| **Crazyflie 2.1+** | ~US $225 | Intermediate | Turnkey research swarm with official positioning + swarm libraries. Buy this if budget isn't the constraint. |

We use the **ESP32 micro-quad** because it hits the brief — *low-cost* and *flying* and *swarm-native* —
and because the flight brain (ESP32) **is** the swarm radio: ESP-NOW is a connectionless 2.4 GHz mesh
baked into every ESP32, so drones talk to each other and to your laptop with no extra hardware.

> **Reality check the skill makes you face:** a *swarm* of quads is an **intermediate** build. If you
> have never flown or soldered, build **one** of these first (or start with the blimp). The simulator
> below lets you develop the whole swarm *before* you can fly one — which is exactly the point.

---

## 2. How the swarm coordinates and localizes

**Coordination — centralized (recommended for hobby swarms).** Your laptop is the *coordinator*: it
holds the mission (take off → formation → pattern → land), computes where each drone should be, and
sends each one a target over ESP-NOW at ~10–20 Hz. Each drone runs its own fast inner loop (attitude +
position hold) and only needs a setpoint. This is far easier than fully-distributed flocking and is how
most small research swarms actually run.

- **cohesion** — each drone steers to its assigned slot in the formation
- **separation** — if two drones get within ~1 m, an avoidance push overrides the slot pull
- **altitude lanes** — each drone flies in its own height band, so crossing paths can never be a collision
  *(this is the trick that took our simulation from colliding to a clean 0.65 m minimum separation)*

**Localization — the hard part, be honest about it:**

| Where you fly | How each drone knows where it is | Cost/effort |
|---|---|---|
| **Outdoors** | GPS module per drone (add a ~US $15 M10 GPS) — easy, but needs the bigger *autonomy* quad, not the micro | Easy |
| **Indoors** | Optical-flow + height sensor (drift-prone), **UWB anchors** (Crazyflie Loco ~US $300 for the set), or a motion-capture rig | Hard / $$$ |

For the tutorial swarm we fly **indoors with the simulator as the source of truth**, and use optical-flow
hold on real hardware — good enough for formation demos in a room. Precise outdoor formations are the
GPS-quad upgrade path.

---

## 3. Simulate first (this is the whole point)

Before buying anything, the coordinated flight is proven in a **multi-drone physics simulator** — real
per-drone dynamics (thrust/accel limited, 20 Hz control loop) plus the centralized coordinator above:

```
arm → take off → V-formation cruise → orbit a waypoint as a ring → regroup → land
```

Result from the actual run (5 drones): **minimum separation 0.65 m (zero collisions), formation hold
settling to 2 cm.** The telemetry plot — inter-drone distance always above the safety line, formation
error spiking at each reconfiguration then re-converging — *is* your proof the coordination logic works.

Two ways to simulate, both covered by the skill:
- **Python swarm sim** (what we used) — fastest way to prove *coordination logic*; runs on any laptop.
- **Multi-vehicle SITL** (ArduPilot `sim_vehicle.py` / PX4) — runs the *real autopilot firmware*, N copies
  at once, for the GPS-quad version. Higher fidelity, more setup.

---

## 4. Bill of materials — ONE drone

Prices are approximate **2026 street prices, inc. tax where applicable**, in the local currency of each
region. AU prices marked ✓ are live from Core Electronics; the rest are typical retail — **always check
current pricing.** Vendors: **US** = Adafruit / Amazon / an FPV shop (GetFPV, RaceDayQuads); **UK** =
The Pi Hut / Pimoroni / an FPV shop (Unmanned Tech, Quadco); **AU** = **Core Electronics** (brain +
sensors + tools) / an FPV shop (Phaser FPV, RC Hobbies) for the propulsion parts.

### Brain + sensing — *buy from Core Electronics (AU) / Adafruit (US) / Pi Hut (UK)*

| Part | What it does | US $ | UK £ | AU $ |
|---|---|---:|---:|---:|
| ESP32 dev board (WROOM / S3 / XIAO-C3) | Flight brain **and** ESP-NOW swarm radio | 8 | 7 | 10.65 ✓ |
| MPU-6050 IMU module | Gyro + accelerometer (knows which way is up) | 4 | 4 | 4.60 ✓ |
| Jumper wire + header + heatshrink | Wiring | 3 | 3 | 5 |

### Propulsion + power — *buy from an FPV / whoop shop*

| Part | What it does | US $ | UK £ | AU $ |
|---|---|---:|---:|---:|
| 4 × 8.5 mm coreless (brushed) motors | Spin the props | 10 | 9 | 16 |
| 4 × 65 mm props (+ a spare set) | Lift | 3 | 3 | 5 |
| Whoop frame, 65–75 mm | Holds it together | 5 | 4 | 8 |
| 4 × SI2302 MOSFET (or tiny brushed driver board) | Lets the ESP32 switch motor current | 3 | 3 | 5 |
| 1S LiPo, 300–450 mAh 30C+ (buy 3–4) | Flight battery *(high-discharge — not a protected pack)* | 4 | 3.5 | 6 |
| BT2.0 / PH2.0 battery pigtail | Connector | 1 | 1 | 2 |
| **PER DRONE** | | **≈ $41** | **≈ £35** | **≈ AU $62** |

> ⚠️ **Do not** substitute Core's general-purpose 1100 mAh protected LiPo — a quad needs a high-C-rate
> whoop pack that can dump 10–15 A in bursts; a protected pack's cutoff will brown out the motors.

### Swarm of 5 airframes: **≈ US $205 / £175 / AU $310**

## 5. Shared gear — buy ONCE for the whole swarm

| Part | US $ | UK £ | AU $ | Notes |
|---|---:|---:|---:|---|
| 1S multi-port LiPo charger (6-ch whoop, e.g. ISDT / GNB) | 25 | 22 | 40 | Charge all packs at once |
| LiPo-safe charging bag | 10 | 9 | 15 | **Non-negotiable safety item** |
| Soldering iron (if you don't own one — Pinecil V2) | 30 | 28 | 55 | Core stocks the Pinecil |
| Spare motors + props | 10 | 9 | 16 | You *will* break some |
| Ground-station laptop | — | — | — | Runs the Python coordinator (you already have one) |
| **SHARED TOTAL** | **≈ $75** | **≈ £68** | **≈ AU $126** | Less if you own an iron |

## 6. What it costs, end to end

| | US $ | UK £ | AU $ |
|---|---:|---:|---:|
| **One drone** | ~$41 | ~£35 | ~$62 |
| **5-drone swarm + shared gear** | **~$280** | **~£243** | **~$436** |

A five-aircraft coordinated swarm for roughly the price of **one** mid-range camera drone.

---

## 7. Safety (the skill enforces these — so do we)

- **LiPo batteries are the most dangerous item here.** Charge on the LiPo bag, never unattended, never a
  puffed/damaged pack, storage-charge to ~3.8 V/cell when idle.
- **Props OFF for every bench test** until the code is proven. Treat an armed quad like a running blender.
- **Failsafes before first flight:** radio-loss behaviour and low-battery cutoff configured and tested.
- **Fly indoors / in a netted space** for the swarm; outdoors turns tiny quads into a regulated aircraft
  question (CASA in AU, FAA in US, CAA/EASA in UK — sub-250 g each helps, a swarm still needs sense).
- **Helium only for the blimp alternative — never hydrogen.**

## 8. Build order (each step proven before the next)

1. **Simulate the swarm** (Section 3) — no hardware, prove the coordination.
2. **Flash ONE drone** with ESP-Drone, props off, verify it arms and the IMU reads level.
3. **First hover** (one drone, props on, in a net) — tune hold.
4. **Two drones + ESP-NOW** — prove they take a setpoint from the laptop coordinator.
5. **Formation of 3–5** — port the simulated coordinator to the real radio link.
6. **The mission** — take off → formation → pattern → land, matching your simulation.

---

**Repo (skill + this guide + the simulator):** https://github.com/ShaunPrice/robot-builder-skill

*Built with the Robot Builder skill. Buy the parts once the design is settled — that's the cheapest way
to avoid a wrong purchase.*
