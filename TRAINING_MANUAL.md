# Robot Builder — Training Manual

Welcome! This manual gets you (the human) set up with the **robot-builder** skill and
shows you how to get the most out of building robots with Claude as your mentor.

## 1. What this skill does

Robot Builder turns Claude into a robotics mentor that can:

- Recommend **exactly what parts to buy** for your budget and skill level
- Walk you through **assembly, wiring, SD-card flashing, and first boot**
- Pair **game controllers and RC radios**, including controller-only (no-code) robots
- Level you up through **Raspberry Pi → NVIDIA Jetson**, depth cameras, lidar, GPS
- Teach and troubleshoot **ROS 2**, SLAM, and autonomous navigation
- Teach **instrumentation and control**: PID from scratch, filters, self-balancing
  robots, quadrupeds and bipeds, flight and rocket stability
- Set up **simulators and training gyms** (Gazebo, ArduPilot/PX4 SITL, MuJoCo, Isaac
  Lab, Gymnasium RL) so code and learned policies are proven before hardware
- Run robot stacks in **Docker** — and connect Claude to Docker via MCP so it can build
  and run containers for you
- Cover **ground robots, boats/ROVs, and aircraft** (drones, fixed wing, helicopters,
  model rockets — all within the law and safety codes)
- **Secure your robot** when it touches Wi-Fi, the internet, or the cloud
- Add **AI/ML**: robot vision (YOLO, depth), LLM task planning, and the techniques and
  hard limits of putting models on robots

## 2. Installing the skill

**Claude Code (CLI / desktop / VS Code)** — personal install, all projects:

```bash
mkdir -p ~/.claude/skills
cp -r robot-builder ~/.claude/skills/
```

Restart Claude Code (or start a new session). Verify: ask *"what skills do you have for
building robots?"* — it should mention `robot-builder`. You can also invoke it explicitly
with `/robot-builder`.

**Project install** (share with a team via git): put the folder at
`.claude/skills/robot-builder/` inside the project repo and commit it.

**Claude.ai (web/app)**: package the folder as a `.skill` file (zip the `robot-builder`
directory) and upload it under Settings → Capabilities/Skills, or simply attach the
`SKILL.md` and reference files to a Project's knowledge.

## 3. Your first session (10 minutes)

Start a conversation like one of these — plain language is fine:

> "I have $250 and I've never built anything electronic. I want a robot I can drive
> around and later program. What should I buy?"

> "I've got a Raspberry Pi 5 and a soldering iron. Help me build a rover that can map my
> house."

> "My kid and I want to build something for the pool — a little boat or submarine?"

> "I bought a Jetson Orin Nano. Walk me through making a robot that follows me."

Claude will ask about your **budget, experience, and goal**, then produce a shopping list
and a build plan. Push back freely — "cheaper", "no soldering", "I already own X" — the
plan adapts.

## 4. How the mentorship works: the build ladder

Every project climbs the same nine rungs. Expect Claude to hold you to the order —
each rung de-risks the next:

1. **Scope & shop** — tiered part list for your budget
2. **Bench setup** — flash the SD card / firmware, pair the controller, first boot
3. **First motion** — teleop with wheels off the ground / props off
4. **Sensors** — camera, depth, lidar, GPS, one at a time, each verified
5. **Compute** — Pi/Jetson companion setup
6. **Control** — calibration, filters, PID — the robot behaves precisely
7. **Autonomy** — ROS 2 + Nav2, or autopilot missions, proven in simulation first
8. **AI/ML** — vision first, then learned policies and LLM planning, always behind a safety layer
9. **Connectivity** — remote access and cloud, secured from the start

Good habits the skill will encourage (let it):
- `git init` your robot code on day one; commit every working step
- Keep a `BUILD_LOG.md` — Claude will offer to update it after each milestone
- End every session with the robot doing something new, however small

## 5. Safety — the short version

The skill enforces these; here's why you should too:

- **LiPo batteries** cause real fires. Never charge unattended, use a LiPo bag, retire
  puffed/crashed packs.
- **Props off** for all drone bench work. Propellers cause most drone injuries.
- **Wheels up / props off / thrusters dry** whenever running new motion code.
- **Failsafes before field use**: signal-loss stop, battery limits, and for aircraft:
  geofence + return-to-launch, tested.
- **Aircraft and rockets are regulated** (CASA in Australia, FAA in the US, EASA in
  Europe; NAR/Tripoli/AMRS for rockets). The skill knows the outlines and will keep you
  on the legal path — it will not help evade limits, and neither should you.
- **AI never gets direct motor control.** Models suggest goals; deterministic code with
  hard limits executes them. This is the golden rule of robot AI.

## 6. Security — the short version

The day your robot joins Wi-Fi:
- Unique password + SSH keys (set during SD-card flashing — the skill shows you where)
- **Never port-forward the robot to the internet.** Use Tailscale/WireGuard for remote
  access — 10 minutes to set up, and the skill will walk you through it
- Keep robots on a guest/IoT network if you can
- Keep API keys and Wi-Fi passwords out of your git repo (the skill will nag — let it)

## 7. A suggested learning path (8 weeks, beginner)

Weeks 1–5 fit a T1 budget (~$200 USD / ~A$300). Weeks 6–8 add ~$120 USD of T2 parts
(encoder gearmotors + an entry lidar) — order them around week 4, or stop at week 5 with a
fully driveable camera robot and upgrade later.

| Week | Milestone | Ask Claude |
|---|---|---|
| 1 | Parts ordered; sim/tools while shipping | "Here's my budget — final shopping list?" |
| 2 | Pi flashed, SSH working, LED blinks | "Walk me through flashing and first boot" |
| 3 | Motors turn on the bench | "Wire the motor driver with me" |
| 4 | Gamepad teleop + watchdog stop | "Connect my Xbox controller and write teleop" |
| 5 | Camera streaming; first YOLO detection | "Make the robot see" |
| 6 | Encoders + straight-line driving | "Add odometry" |
| 7 | ROS 2 installed; teleop through ROS | "Move my robot into ROS 2" |
| 8 | Lidar SLAM map of a room | "Map my house" |

Then, in whatever order excites you: Nav2 autonomy → follow-me with depth → a
self-balancing robot (the best control-theory teacher, ~$80 of parts) → your robot in
Gazebo/SITL simulation → an RL policy in a training gym → LLM tasking → a second domain
(boat? plane? quadruped?). "Master" isn't a rung — it's having climbed the ladder in more
than one domain.

## 8. Getting good answers

- **Give numbers**: budget, what you own, room sizes, payload, country.
- **Paste exact errors** — whole tracebacks, not paraphrases.
- **Describe wiring precisely** when stuck ("driver IN1 → GPIO 17, motor battery is 2S,
  grounds joined") — most robot bugs are power or wiring.
- **Say your comfort level honestly.** "I've never soldered" changes the recommended
  parts, not the destination.
- **Ask "why"** whenever a part or step seems arbitrary. The skill is built to explain.

## 9. What's in the box

```
robot-builder/
├── SKILL.md                     # the mentor's playbook + routing
├── TRAINING_MANUAL.md           # this file
├── evals/evals.json             # test prompts used to QA the skill (not loaded at runtime)
└── references/
    ├── parts-and-budgets.md     # what to buy, by budget × skill × domain
    ├── getting-started.md       # SD cards, firmware, controllers, first motion
    ├── compute-platforms.md     # MCUs, Pi, Jetson, flight controllers
    ├── sensors.md               # cameras, depth, lidar, IMU, GPS, encoders
    ├── ros.md                   # ROS 2 from zero to Nav2
    ├── ground-robots.md         # rovers, tanks, RC cars
    ├── water-robots.md          # boats, ROVs, AUVs
    ├── air-robots.md            # drones, planes, helis, rockets + regulations
    ├── control-and-stability.md # PID, filters, balancers, bipeds, flight/rocket stability
    ├── simulation-and-gyms.md   # Gazebo, SITL, MuJoCo, Isaac Lab, RL gyms, sim2real
    ├── docker-and-environments.md # containers for ROS/sim/Jetson + Docker MCP setup
    ├── security.md              # network, internet, and cloud security
    └── ai-ml.md                 # vision, LLMs, learning-based control, limits
```

Each reference file is a self-contained **sub-skill**: Claude loads only the modules your
current question needs, so the mentor stays fast while the full library covers novice
through master. (They're kept inside one skill rather than many separate ones so a single
question like "make my drone follow me" can draw on air + vision + control + safety at
once.)

## 10. Optional power-up: let Claude drive Docker

Much of the advanced stack (ROS on a Mac/Windows laptop, simulators, Jetson ML images)
runs best in containers. If you install Docker and connect a **Docker MCP server**,
Claude can build images, start SITL/Gazebo containers, and read their logs for you
directly instead of trading copy-pasted commands:

1. Install Docker Desktop (Mac/Windows) or docker-ce (Linux) and enable the
   **MCP Toolkit** in Docker Desktop's settings, then connect its Docker server to
   Claude Code (the Toolkit shows the exact `claude mcp add …` command), or use a
   community server like `uvx mcp-server-docker`.
2. New session, ask "list my running containers" to verify.
3. Then try: *"Spin up ArduPilot SITL in Docker and connect a pymavlink script that flies
   a square."*

Security note: the Docker socket is effectively root on that machine — connect it on your
dev computer, not on the robot, and review anything Claude proposes to run privileged.
Details in `references/docker-and-environments.md`.

You can read the references directly — they're written for humans too — but the normal
mode is conversational: describe what you want, and Claude pulls the right material.

Happy building. Wheels up (literally — keep them off the ground until the code works).
