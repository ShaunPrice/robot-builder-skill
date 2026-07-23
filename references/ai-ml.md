# AI/ML on robots: vision, LLMs, control — and their limits

Rung 7. Prerequisite: the robot already teleops reliably and (ideally) navigates. AI is a
layer on top of a working robot, never a substitute for one.

## The architecture that keeps this safe (teach it first)

```
┌──────────────────────────────────────────────────────────┐
│ SLOW LOOP (0.1–1 Hz, may be cloud): LLM/VLM planner       │  "go check the mailbox"
│   → emits GOALS/waypoints/behavior selections             │
├──────────────────────────────────────────────────────────┤
│ MID LOOP (5–30 Hz, on-robot): perception + navigation     │  YOLO, SLAM, Nav2/autopilot
│   → emits velocity/attitude setpoints                     │
├──────────────────────────────────────────────────────────┤
│ FAST LOOP (50–1000 Hz, MCU/FC): motor control + SAFETY    │  PID, watchdogs, E-stop,
│   → hard limits AI cannot override                        │  geofence, cliff/prox stops
└──────────────────────────────────────────────────────────┘
```

**AI proposes; the deterministic layer disposes.** LLM output is *never* wired to
actuators directly. The fast loop enforces: velocity/accel clamps, geofence, obstacle
stop, command-timeout watchdog, battery floor, and a human E-stop that bypasses all
software. Build these limits before the first model runs, then AI experimentation becomes
low-stakes play instead of a hazard.

## Robot vision (start here — it's the reliable part of robot AI)

**Detection**: Ultralytics YOLO (v8/v11) is the pragmatic default — `pip install
ultralytics`, pretrained on COCO (80 classes: person, car, dog, cup…), one line to run.
- Pi 5 CPU: YOLOv8n ~5–10 FPS at 640px — usable. With Hailo AI HAT or OAK-D (model runs
  on camera/accelerator): 30+ FPS.
- Jetson: export to **TensorRT** (`model.export(format='engine', half=True)`) — Orin Nano
  runs YOLOv8s at 60–100+ FPS. TensorRT (FP16, or INT8 with calibration) is a 3–10×
  speedup over vanilla PyTorch; it's the single biggest Jetson win.
- Distance to object: detection box + depth image (median depth inside the box) → range
  and bearing. This one trick (RGB-D + YOLO) powers follow-me, obstacle semantics,
  "bring me the ball", patrol alerts.

**Tracking** (persistent IDs across frames): ByteTrack/BoT-SORT built into Ultralytics
(`model.track()`). Needed for following a *specific* person.

**Other useful, boring-reliable tools**: AprilTags/ArUco (`opencv-contrib`) for precise
pose targets — docking, precision landing, "go to marker 7" (poor man's localization);
classical OpenCV (color threshold + contours) still wins for high-rate line following;
segmentation (YOLO-seg) for traversability; monocular depth (Depth Anything) when no
depth camera — relative depth only, don't trust it for metric distance.

**Custom objects**: collect 200–2000 images *from the robot's own camera at deployment
angles/lighting* (this matters more than model choice), label in Roboflow/CVAT or
auto-label with a big model (Grounding DINO) then correct, fine-tune YOLO
(`model.train(data=..., epochs=100)`) on a desktop GPU or free Colab, deploy the
exported engine. Expect 2–3 collect→train→deploy loops before it works in the field —
tell users this so they don't quit after round one.

**Fine-tuning/training realities**: train off-robot (desktop RTX or cloud), infer
on-robot; smaller model at higher FPS usually beats bigger model at 3 FPS for control;
validate on a held-out set from a *different day/lighting* than training.

## LLMs and VLMs on robots

What language models are genuinely good at on a robot:
- **Task planning**: "check whether the garage door is open" → [navigate(garage),
  capture(), vlm_query('is the door open?'), report()]. Give the LLM tools/functions, get
  structured plans.
- **Scene understanding (VLM)**: send a camera frame + question, get semantics no
  detector has classes for ("is anything blocking the doorway?", "which bin is fullest?").
- **Natural-language interface**: chat with the robot, translate human intent to missions,
  summarize patrol footage/logs, explain telemetry ("why did you stop?").

What they are bad at (design around, don't fight):
- **Real-time control.** Cloud round-trip 500 ms–3 s; even local small models 100–1000 ms.
  A robot at 1 m/s travels 1–3 m per decision — the mid/fast loops must own motion.
- **Spatial precision.** LLMs don't know where 40 cm is. They pick *targets and
  behaviors*; SLAM/Nav2/autopilot handles geometry.
- **Hallucination + non-determinism.** The same prompt may yield different plans; the
  model may cite objects that aren't there or emit malformed calls. Mitigations:
  constrained/structured output (JSON schema, enum of allowed skills), validate every
  field against reality (does waypoint 'garage' exist? is speed ≤ limit?), reject and
  re-ask on failure, log every plan for postmortems.
- **Prompt injection**: a robot that reads signs/QR codes/speech is consuming untrusted
  input into its planner. Treat perception text as data, never as instructions ("ignore
  a note that says 'drive into the pool'" is a real test case).
- **Cloud dependence**: define offline behavior; queue non-urgent queries; never let a
  dropped API call strand the robot (see security.md comms-loss rule).

**Local vs cloud inference**:
| Option | Latency | Quality | Fit |
|---|---|---|---|
| Cloud API (Claude etc.) | 0.5–3 s | Best reasoning/VLM | Planning, VLM queries, chat — when online |
| Jetson Orin local (Ollama/llama.cpp, 3–8B quantized; Orin Nano 8 GB runs 7–8B Q4 at ~10–25 tok/s) | 0.1–1 s to first token | Good enough for structured planning | Offline autonomy, privacy |
| Pi 5 local | slow (1–5 tok/s on 3B) | marginal | Novelty; prefer cloud or accept tiny models |

A good hybrid: local small model for routine structured decisions, cloud model for hard
questions when connectivity allows, with identical tool schemas so they're swappable.

**Integration pattern (ROS 2)**: an `llm_agent` node subscribes to task requests +
robot state, calls the model with a toolset (`navigate_to(named_pose)`,
`capture_image()`, `vlm_query(q)`, `say(text)`, `report(text)`), publishes *goals* to
Nav2/behavior nodes. Tools are the safety boundary: each validates inputs and enforces
limits before acting; the LLM literally cannot express "set motor PWM".

## Learning-based control (beyond perception)

- **Behavior cloning / imitation**: record teleop (camera → your stick inputs), train a
  small CNN to mimic — the classic "self-driving RC car" (DonkeyCar). Works, teaches a
  ton, brittle off-distribution: it learns *your* track in *your* lighting.
- **Reinforcement learning**: train in sim (Isaac Lab, Gazebo, MuJoCo), deploy with
  domain randomization to survive the **sim2real gap**. This is how quadrupeds learn to
  walk. The full pathway — Gymnasium API, building custom envs for your robot, Isaac Lab,
  sim2real checklist — lives in simulation-and-gyms.md. Warn everyone that RL directly on
  hardware (skipping sim) is slow, battery-hungry, and hard on the robot.
- **VLA models** (RT-2/OpenVLA/π0-class, vision→language→action): the research frontier;
  open weights exist and run on big Jetsons for manipulation demos. Fun to discuss,
  premature for hobby reliability — set expectations honestly.

## Evaluation and iteration habits

- Record everything (`ros2 bag`, videos, plans+outcomes): today's failure is tomorrow's
  test case and fine-tuning data.
- Build a tiny regression suite: 20–50 recorded frames/scenarios with expected outputs;
  run after every model/prompt change. Vibe-checking on live hardware doesn't scale.
- Track FPS *and* end-to-end latency (capture→decision→actuation), not just model
  accuracy: a 95%-mAP model at 400 ms end-to-end loses to an 88% model at 80 ms in
  almost every mobile-robot task.
- Stage rollouts: sim → on blocks → tethered/enclosed space → supervised field → routine.
  Each stage has the E-stop within reach.
