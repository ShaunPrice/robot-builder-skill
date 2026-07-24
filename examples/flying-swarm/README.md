# Flying Robot Swarm — worked example

A 3–5 unit swarm of low-cost **ESP32 micro-quadcopters**, designed and *simulated*
end-to-end with the Robot Builder skill before any hardware is bought.

📺 **Video walkthrough:** *(add your YouTube link here)*

> ⚠️ **Simulation only — not yet flown.** Everything here has been developed and proven in
> **simulation**; it has **not** been built or flight-tested on real hardware. It's a
> software-tested blueprint, not a guarantee — build and fly at your own risk. **Not sponsored;
> no affiliation with any vendor mentioned.**

## What's here

| File | What it is |
|---|---|
| [`SWARM_BUILD.md`](SWARM_BUILD.md) | The full build guide — platform choice, how the swarm coordinates & localizes, complete bill of materials with **US / UK / AU** vendors and costs, safety, and the build order. |
| [`BUILD_INSTRUCTIONS.md`](BUILD_INSTRUCTIONS.md) | Step-by-step assembly, wiring diagram, flashing and bench bring-up for one drone (props-off procedure included). |
| [`swarm_sim.py`](swarm_sim.py) | A self-contained multi-drone **physics simulator** + centralized formation controller. Flies the mission *arm → take off → V-formation → ring orbit → regroup → land* and renders it, so you can prove the coordination logic with zero hardware. |
| `swarm_telemetry.png` | Telemetry from an actual run — minimum inter-drone distance (never crosses the 0.5 m safety line → **zero collisions**) and formation error (settles to **2 cm**). |
| [`firmware/drone/`](firmware/drone/drone.ino) | Per-drone ESP32 flight controller — MPU-6050 → complementary filter → angle/rate PID → X-mix → brushed motors, with an ESP-NOW setpoint receiver and link-loss failsafe. |
| [`firmware/coordinator_bridge/`](firmware/coordinator_bridge/coordinator_bridge.ino) | A spare ESP32 that relays the laptop's per-drone setpoints to each drone over ESP-NOW. |
| [`coordinator/swarm_coordinator.py`](coordinator/swarm_coordinator.py) | Laptop coordinator — runs the *same* formation controller as the sim, turns it into attitude/throttle setpoints, and streams them to the bridge. `--dry-run` previews the whole mission with no hardware. |
| [`engineering/swarm-drone-calcs.xlsx`](engineering/swarm-drone-calcs.xlsx) | Motor / weight / power spreadsheet with **live formulas** — AUW, thrust-to-weight, hover throttle, peak-current check, and flight-time estimate. Yellow cells are inputs. ([`gen_calcs.py`](engineering/gen_calcs.py) regenerates it.) |
| [`cad/whoop_frame.stl`](cad/whoop_frame.stl) | 3D-printable X-quad frame — 75 mm wheelbase, 8.5 mm motor tubes, board deck. Parametric source: [`cad/gen_frame.py`](cad/gen_frame.py). |

> ⚠️ The firmware is **untested reference code** — bench-test with props **off** and verify motor
> directions/axis signs before fitting props. Real formation flight also needs position feedback
> (optical-flow / UWB / mocap) wired into the coordinator; see `BUILD_INSTRUCTIONS.md`.

Reference engineering numbers (from the spreadsheet, for the ~41.5 g reference build): **T/W ≈ 2.4:1**,
hover ≈ **42 %** throttle, peak-current margin ≈ **1.7 A** on a 300 mAh 30C pack, endurance ≈ **6.9 min**.

## Run the simulator

```bash
pip install numpy matplotlib imageio imageio-ffmpeg
python swarm_sim.py 5          # N drones (default 5)
```

Outputs `swarm_flight.mp4` (3-D), `swarm_topdown.mp4`, `swarm_telemetry.png`, and
`swarm_metrics.json`. The trick that makes crossing flight paths collision-free is
**altitude deconfliction** — each drone flies its own height lane, and the lanes
collapse as the swarm descends so they still land on their distinct formation spots.

## Why this platform

Each drone's brain — the **ESP32** — is also its swarm radio (ESP-NOW mesh is built
into the chip), so a coordinated flyer costs about **US $40** per unit. See
[`SWARM_BUILD.md`](SWARM_BUILD.md) for the reasoning, the cheaper indoor-blimp
alternative, and the turnkey Crazyflie option.

> Built with the [Robot Builder skill](../../README.md). Aircraft get simulator time
> first, always — that's the whole point of this example.
