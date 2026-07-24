# Wheeled Robot Swarm — worked example

A **3-robot** differential-drive swarm that holds formations and drives coordinated patterns, with
the swarm's hardest problem actually solved: **localisation**. Each robot wears an **ArUco fiducial**,
one **overhead webcam** reads them all, a laptop knows every robot's pose, and a **distance sensor**
on each robot handles local avoidance. Designed and simulated end-to-end with the Robot Builder skill.

📺 **Video walkthrough:** *(add your YouTube link here)*

> ✅ This is the skill's **achievable-swarm default**: localisation is a ~$25 webcam + printed paper
> tags, not a motion-capture rig. Indoor, slow, safe.
> ⚠️ Proven in **simulation**; firmware is **untested reference code** (bench-test wheels-up first).
> **Not sponsored**, no vendor affiliation; prices approximate.

## What's here

| Path | What it is |
|---|---|
| [`SWARM_BUILD.md`](SWARM_BUILD.md) | Design, how localisation works, full **US/UK/AU** BOM (~$37/robot, ~$146 for three + webcam), safety, build order. |
| [`BUILD_INSTRUCTIONS.md`](BUILD_INSTRUCTIONS.md) | Assembly, wiring, flashing, camera setup, wheels-up bring-up. |
| [`wheeled_swarm_sim.py`](wheeled_swarm_sim.py) | Physics sim: 3 robots localised by an overhead camera + fiducials (odometry between frames) + distance-sensor avoidance. Mission *scatter → triangle → translate → rotate → line → park*. |
| `wheeled_telemetry.png` | A run's telemetry — formation error, min separation (0 collisions), and localisation error (~4 mm, bounded by the camera). |
| [`firmware/robot/`](firmware/robot/robot.ino) | ESP32 robot firmware — receives (v, ω) over ESP-NOW, drives the DRV8833, reads the VL53L0X for a local emergency stop, fails safe on link loss. |
| [`firmware/coordinator_bridge/`](firmware/coordinator_bridge/coordinator_bridge.ino) | Spare ESP32 that relays the laptop's per-robot commands over ESP-NOW. |
| [`coordinator/swarm_coordinator.py`](coordinator/swarm_coordinator.py) | Laptop coordinator — **ArUco detection** from the webcam → the same formation controller as the sim → (v, ω) to the bridge. `--sim` previews with no hardware. |
| [`engineering/swarm-robot-calcs.xlsx`](engineering/swarm-robot-calcs.xlsx) | Weight / drive / power sheet with live formulas (AUW, cruise speed, torque margin, run time). ([`gen_calcs.py`](engineering/gen_calcs.py)) |
| [`cad/chassis.stl`](cad/chassis.stl) | Printable base plate — motor mounts, caster + ToF slots, deck holes, fiducial recess ([`gen_chassis.py`](cad/gen_chassis.py)). |
| [`cad/make_tags.py`](cad/make_tags.py) + `aruco_id*.png` | Generate + the printable ArUco tags. |

## Run the simulator

```bash
pip install numpy matplotlib imageio imageio-ffmpeg
python wheeled_swarm_sim.py 3      # -> wheeled_topdown.mp4, wheeled_telemetry.png, wheeled_metrics.json
```

Verified: **0 collisions (24 cm min sep), 1.3 cm formation hold, ~4 mm localisation error.** The
camera+fiducial fusion keeps position error bounded where odometry alone would drift away.

## Preview the coordinator with no hardware

```bash
cd coordinator && python swarm_coordinator.py --sim
```

> Built with the [Robot Builder skill](../../README.md). The skill now solves **localisation first**
> and prefers this wheeled + fiducials + overhead-camera design over a flying swarm whose indoor
> positioning can't be supplied cheaply.
