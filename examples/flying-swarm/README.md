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
| [`swarm_sim.py`](swarm_sim.py) | A self-contained multi-drone **physics simulator** + centralized formation controller. Flies the mission *arm → take off → V-formation → ring orbit → regroup → land* and renders it, so you can prove the coordination logic with zero hardware. |
| `swarm_telemetry.png` | Telemetry from an actual run — minimum inter-drone distance (never crosses the 0.5 m safety line → **zero collisions**) and formation error (settles to **2 cm**). |

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
