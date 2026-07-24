# Core Electronics parts list — DIY 4-wheel ESP32 swarm robot (3D-printed chassis)

All prices **AUD, inc GST**, from core-electronics.com.au (verified 2026‑07‑24 — check current). Because
**we** specify the exact parts and print the chassis, all three robots are **identical**: one ESP32
brain, **four wheels**, one distance sensor, one fiducial. This is the cheapest and most "maker" path.

## The robot — build 3 identical (per-robot bill)

| # | Part | Brand / Core | Qty | Price ea | Line |
|---|---|---|---:|---:|---:|
| 1 | **DC Gearbox "TT" Motor — 200 RPM, 3–6 V** | Adafruit | 4 | $7.35 | $29.40 |
| 2 | **TT Motor Wheel — 65 mm** | Adafruit (or Kitronik pair $7.60) | 4 | $4.95 | $19.80 |
| 3 | **ESP32 dev board** (brain **+** ESP‑NOW radio) | XIAO ESP32‑C3 | 1 | $10.65 | $10.65 |
| 4 | **DRV8833 dual motor driver** (drives the 2 left + 2 right motors) | Adafruit | 1 | $11.95 | $11.95 |
| 5 | **HC‑SR04 ultrasonic distance sensor** (local avoidance) | Core Electronics | 1 | $1.95 | $1.95 |
| 6 | 4×AA battery holder + AA cells (or 2× 18650) | — | 1 | ~$7 | ~$7.00 |
| 7 | Jumper wires + headers + heatshrink | — | 1 | ~$5 | ~$5.00 |
| 8 | **3D‑printed chassis** (`cad/chassis.stl` — we supply it) | filament | 1 | ~$1 | ~$1.00 |
| 9 | **ArUco fiducial** — printed on paper, stuck on top | — | 1 | free | $0 |
| | **PER ROBOT** | | | | **≈ $87** |

> The chassis holds four TT motors (one at each corner, skid‑steer), the ESP32 + driver on the deck, the
> ultrasonic sensor at the front, and a flat pad on top for the ArUco tag. It's the same differential /
> skid‑steer control our simulator and firmware already use — the two left wheels are one "side," the two
> right wheels the other.

## Shared — buy once for the swarm
| Part | Price |
|---|---:|
| Overhead USB webcam (720p+) — *or a phone / a webcam you already own* | ~$40 |
| Webcam mount / small tripod | ~$18 |
| Ground‑station laptop (runs the coordinator) | you have one |

## Totals
| | AUD |
|---|---:|
| **One robot** | ~$87 |
| **3‑robot swarm + webcam** | **≈ $300** (≈ $260 if you already have a webcam) |

Roughly **half the cost** of the turnkey options, and every robot is guaranteed identical.

---

### If you'd rather not solder / print (turnkey alternatives)
- **Waveshare WAVE ROVER** (WS‑25376, **$179.95**) — full‑metal 4WD with an **onboard ESP32**, in‑situ
  rotation (matches our control), open‑source. Rugged, one SKU. ~$210/robot with batteries. Needs a
  distance sensor added (HC‑SR04 $1.95).
- **ACEBOTT ESP32 Smart Car** (CE10126, **$129.95**) — ESP32 + **4 mecanum wheels**, ultrasonic sensor
  **included**, no soldering, tutorials. ~$150/robot. Trade‑off: mecanum (holonomic) needs mecanum
  mixing instead of our differential firmware.

> Tell me which robot to lock in (I recommend the **DIY 4‑wheel printed** build for cost + consistency)
> and I'll align the firmware pins + chassis + a new video to exactly that robot.
