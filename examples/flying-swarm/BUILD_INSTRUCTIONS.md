# Build instructions — ESP32 brushed micro-quad (swarm unit)

Step-by-step assembly, wiring, flashing and bench bring-up for **one** drone. Build and prove
one before you make five. Pair this with [`SWARM_BUILD.md`](SWARM_BUILD.md) (parts + costs),
[`engineering/swarm-drone-calcs.xlsx`](engineering/swarm-drone-calcs.xlsx) (weight/thrust/power),
and [`cad/whoop_frame.stl`](cad/whoop_frame.stl) (the frame).

> ⚠️ **Read first.** This design is **proven in simulation only — not built or flight-tested on
> hardware**, and the firmware is **untested reference code**. Nothing here is sponsored. Work with
> **props OFF** until the very last step, keep LiPos in a fire bag, fly netted/indoors, and follow
> your local rules (CASA / FAA / CAA). You build and fly entirely at your own risk.

## 0. Bench, tools, safety
- Soldering iron + fine solder, flush cutters, tweezers, multimeter, a LiPo-safe bag, a small scale.
- **Never** charge a LiPo unattended; storage-charge (~3.8 V/cell) when idle; bin any puffed pack.
- Keep a hand near the battery lead during every powered test so you can yank it.

## 1. Print the frame
- File: `cad/whoop_frame.stl` (75 mm wheelbase, sized for 8.5 mm motors). Regenerate/tweak with
  `cad/gen_frame.py`.
- **Material** PLA (easy) or PETG (tougher). **Layer** 0.2 mm. **Walls** 3 perimeters. **Infill**
  40–50 % gyroid. **Supports** none — print deck-down. Expect **~2.5–5 g**.
- Test-fit a motor in each tube (should press in snugly, ~8.6 mm bore). Ream lightly if tight.

## 2. Wiring
Power the whole craft from the **1S LiPo** (3.7–4.2 V).

**Flight brain + IMU (I2C):**

| MPU-6050 | → ESP32 |
|---|---|
| VCC | 3V3 |
| GND | GND |
| SDA | I2C SDA (e.g. GPIO6 on XIAO-C3 — set in `drone.ino`) |
| SCL | I2C SCL (e.g. GPIO7) |

Power a XIAO-class ESP32-C3 from the pack on its **BAT/+** pads (it runs directly off 1S); feed the
MPU-6050 from the board's **3V3**.

**Each motor (×4) — low-side N-channel MOSFET (SI2302):**

```
 VBAT(+) ──●───────────────► motor (+)
           │            ┌──► motor (−) ──► MOSFET DRAIN
   Schottky▼ (1N5819)   │
           │            │
 motor(+)──┘            │        ESP32 GPIO ──[100 Ω]── MOSFET GATE
                        │                                  │
                       GND ◄── MOSFET SOURCE          [10 kΩ] to GND (gate pulldown)
```
- One Schottky flyback diode **across each motor** (cathode → VBAT+, anode → motor−/drain) to catch
  the brushed motor's inductive kick.
- Gate series resistor ~100 Ω; gate pulldown ~10 kΩ so the motor stays OFF at boot/reset.
- Motor pins in `drone.ino`: `MOTOR_PIN[4] = {M1 FR, M2 RR, M3 RL, M4 FL}` — match your wiring.
- Common ground everywhere (battery −, MOSFET sources, ESP32 GND, IMU GND).

## 3. Flash the drone firmware
- Arduino IDE (or `arduino-cli`) with the **ESP32 core** installed. Open `firmware/drone/drone.ino`.
- Select your board + port, **Upload**.
- Open Serial Monitor @ 115200. **Copy the `Drone MAC` it prints** — you'll paste it into the bridge.
- Flash each drone in turn; keep a list: drone 0 → MAC, drone 1 → MAC, …

## 4. Bench bring-up — PROPS OFF
Do all of this with **no props fitted**.
1. **IMU sanity:** temporarily add a `Serial.print` of `pitch`/`roll` — tilt the board, angles should
   track and read ~0 when level.
2. **Motor direction & order:** with a bridge sending a low throttle (Step 5) or a tiny test sketch,
   confirm each of M1–M4 spins, spins the **correct way** for its position, and matches the mix in
   `drone.ino`. Swap any two motor leads to reverse a motor. Fix `MOTOR_PIN[]` order if a corner is wrong.
3. **Axis signs:** nudge each axis setpoint and confirm the *right* motors speed up to correct. If a
   correction makes it worse, flip that axis's sign in the X-mix. **This is the step that stops
   crashes — do not skip it.**

## 5. Flash the bridge + run the coordinator
1. On a **spare ESP32**, open `firmware/coordinator_bridge/coordinator_bridge.ino`, paste your drones'
   MACs into `DRONE_MAC[]`, upload. Note its serial port.
2. Preview the whole mission with **no hardware**:
   ```bash
   cd coordinator && python3 swarm_coordinator.py --dry-run --drones 5
   ```
3. Drive real drones (props still off for the first go):
   ```bash
   python3 swarm_coordinator.py --port /dev/tty.usbserial-XXXX --drones 5   # pip install pyserial
   ```
   Watch the motors respond to the mission. **`Ctrl-C` disarms all drones.**

> **Localization is the open problem.** `swarm_coordinator.py` closes the position loop against an
> internal model in `--dry-run`. For real formation flight you must feed **real positions** into
> `get_state()` — optical-flow + height sensor, UWB anchors, or motion capture. Without it, the swarm
> holds attitude but drifts in position.

## 6. First hover, then the swarm
1. **One drone, props on, tethered, in a net.** Lowest throttle that gives lift. Re-check the engineering
   sheet's hover throttle (~42 %) and T/W (~2.4:1).
2. **Tune** `Kp_ang` / `Kd_ang` in `drone.ino`: raise `Kp` until it holds level, add `Kd` to stop the
   oscillation, a touch of `Ki` to kill steady drift.
3. **Add drones one at a time**, re-running the coordinator, until the full 3–5 unit mission from the
   simulation flies for real.

Log what worked (gains, wiring, weights) in a `BUILD_LOG.md` as you go — a fried board should never
cost you the knowledge.
