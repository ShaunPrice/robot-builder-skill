# Swarms and multi-robot systems

The moment you have more than one robot, the interesting problem stops being any single
robot and becomes the *space between* them: how they talk, how they know where the others
are, and who decides who does what. A swarm is a coordination + comms + shared-localization
problem wearing a robot costume. Get those three right and ten cheap rovers do useful work;
get them wrong and you have ten expensive rovers taking turns crashing into each other.

## First decision: how will each robot know where it (and its neighbours) are?

Answer this **before you choose a platform** — it is the decision the whole swarm lives or dies
on, and the one most likely to sink a beginner's project. Every coordinated behaviour (holding a
formation, "don't collide", "cover this area") assumes each robot knows, at least roughly, its own
pose and its neighbours'. **If you can't name how that happens, you don't have a swarm design yet —
you have a wish.** Choose the localization method first, then pick the platform that serves it.

**The achievable default for a first swarm — steer here unless there's a specific reason not to:**
a small **wheeled ground swarm (start with 3) with a fiducial marker (ArUco / AprilTag) on top of
each robot and one overhead webcam.** OpenCV reads every tag's ID and pose from the ceiling camera,
so a laptop knows each robot's (x, y, heading) in one shared frame — a cheap, real "indoor GPS" —
and the coordinator turns that into targets. Add a **distance sensor (ToF VL53L0X or ultrasonic) per
robot** for local, camera-independent collision avoidance. Localization cost: one ~$25 webcam plus a
printed paper tag per robot. It is indoor, it cannot fall out of the sky, there are no regulations,
and — crucially — the localization is actually *solved*, not hand-waved.

**Why not a flying swarm first?** An indoor *flying* swarm has no cheap localization answer: GPS
does not work indoors, and holding formation needs UWB beacons or motion capture (expensive) or
drift-prone optical flow. So an indoor drone swarm is an **advanced** project, not a beginner one.
If a user asks for one, say so, and offer either the wheeled swarm above (learn coordination cheaply
first) or an **outdoor GPS** drone swarm (where localization is just per-drone GPS). Never design an
indoor flying swarm around a localization method you cannot actually supply — that is precisely the
hole that strands a project at unit two.

## Design completeness check — loop before you commit

A swarm design is not finished when it sounds cool; it is finished when every one of these has a
concrete, buildable answer. Before presenting a design, walk the checklist — and **if any box is
empty or hand-wavy, change the design and walk it again. Loop until all five hold:**

1. **Localization** — how does each robot know its own pose and its neighbours'? A *named* method,
   within the user's budget and skill — not "we'll figure it out later".
2. **Comms** — which link carries which messages, at what rate, with latency margin? (Radio matched
   to message rate — see Comms below.)
3. **Collision avoidance** — what stops two units hitting each other *locally*, independent of the
   coordinator? (A per-robot sensor/rule, not just the plan.)
4. **Coordinator / architecture** — centralized or decentralized, and who decides what? One clear
   place to reason about and to E-stop.
5. **Achievability** — can *this* user build N of these at their skill level and budget, and is it
   legal and safe where they will run it?

The failure this catches is the common one: a design complete on four of five and silently unsolved
on **localization**. That is not a smaller problem — it is the whole problem. If localization has no
answer the design is not achievable; say so plainly and pivot (usually to the wheeled + fiducials
default above) rather than shipping a plan with a hole in it.

## Start with two, and make each unit cheap

Two rules save more grief than anything else in this file.

- **Start with 2–3 units, never ten.** Every coordination bug, comms dropout, and
  localization drift shows up at N=2. If two robots can hold a formation and hand off a
  task cleanly, adding units is mostly tuning. If they can't, adding units multiplies the
  chaos. Prove the pattern small, then scale.
- **Cost multiplies, so keep the per-unit build cheap.** A $200 rover is a $2,000 swarm at
  ten units — and you *will* break some learning to coordinate. Favour ESP32-class brains
  (compute-platforms.md), one shared design you can build in a batch, and spares. Push the
  expensive sensing (a good depth camera, a lidar) onto one "leader" or a fixed overhead
  rig rather than every unit, if the task allows.

The honest version: a real swarm is a manufacturing exercise as much as a robotics one. Ten
identical robots means ten sets of the same wiring, the same flash step, the same
calibration. Script the flashing and calibration early (getting-started.md) — doing it by
hand ten times is where enthusiasm goes to die.

## ROS 2 for multi-robot (the ground/water path)

ROS 2 handles multiple robots on one graph, but you must keep them from stepping on each
other's topics (ros.md):

- **Per-robot namespaces**: launch every node under `/robot1`, `/robot2`… so each has its
  own `/robot1/cmd_vel`, `/robot1/scan`, `/robot1/odom`. This is the standard, and it lets
  one operator station subscribe to all of them.
- **ROS_DOMAIN_ID separation** when robots should *not* see each other's traffic at all:
  different domain IDs partition DDS discovery entirely (T1's perception runs on its own
  domain for exactly this reason). Use namespaces for a cooperating fleet on one network;
  use domain IDs to isolate independent robots sharing the air.
- **Multi-robot Nav2**: each robot runs its own Nav2 stack in its namespace. The map is the
  design decision — either a **shared map** (one SLAM process, or a pre-built map all robots
  localize into) so they share a coordinate frame, or **per-robot maps** that you must then
  align, which is harder than it sounds.
- Watch Wi-Fi load: full lidar scans and camera topics from several robots saturate a home
  access point fast. Keep heavy data on-robot; publish only what the coordinator needs.

## Coordination patterns: centralized vs decentralized

| Pattern | How it works | Good when | Trap |
|---|---|---|---|
| **Centralized** | A server/coordinator holds global state, assigns tasks, deconflicts paths | Small fleets, known area, you want optimal-ish behaviour | Single point of failure; comms to the server is the bottleneck |
| **Leader–follower** | Followers hold an offset from a leader's pose | Formations, convoys, simple demos | Leader failure = fleet stops; error compounds down a chain |
| **Behaviour-based / flocking** | Each robot follows local rules (boids: separation, alignment, cohesion) from neighbours only | Large numbers, robustness, "swarm-like" emergent motion | Emergent ≠ controllable; hard to guarantee a specific outcome |
| **Potential fields** | Robots repelled by each other/obstacles, attracted to goals | Coverage, dispersion, simple collision-avoidance | Local minima (robots stuck in a standoff) |

Most hobby swarms are happiest **centralized** — a laptop as the coordinator assigning
goals, each robot running local obstacle avoidance. It is easy to reason about, easy to
debug (you can log every decision in one place), and easy to E-stop. Reach for
decentralized/behaviour-based rules when the *number* of units or comms range makes a
central brain impractical, or when emergent flocking *is* the goal (light shows, research).

## Comms: bandwidth and latency are the real limits

| Link | Range | Bandwidth | Cost/effort | Use for |
|---|---|---|---|---|
| **Wi-Fi** | ~room / yard | High | Trivial (it's already there) | Indoor fleets, ROS 2 traffic; scales poorly past a handful on one AP |
| **ESP-NOW** | ~50–200 m LOS | Low (short packets) | ~free on ESP32 | Cheap mesh of tiny robots: positions, commands, heartbeat |
| **LoRa** | km | Very low (bytes/sec) | ~$10/node | Long-range, outdoor, sparse updates (agriculture, area coverage) |
| **UWB** | ~10–50 m | Low | ~$15–40/node | *Ranging* — and it doubles as relative localization (below) |

The instinct is to pick a link by range; pick it by **what you actually need to send**. A
flocking swarm needs a few numbers per neighbour at 10–20 Hz — ESP-NOW is perfect and
Wi-Fi is overkill. A camera-sharing fleet needs Wi-Fi and will still choke past three or
four units. Latency matters as much as bandwidth: a coordination loop that reacts to
neighbour positions falls apart if those positions arrive 500 ms late, exactly like an
over-filtered control loop (control-and-stability.md). Budget the message *rate* first, then
choose the radio that carries it with margin.

## Localization: the actual hard part

For robots to cooperate they must share a coordinate frame — each must know, at least
roughly, where the others are. This is where multi-robot projects live or die, and indoor
relative localization is genuinely the crux. Options, honestly ranked by pain:

- **Shared SLAM map** (indoor, no extra hardware): all robots localize into one map, so
  poses are comparable. Elegant, but map drift and per-robot localization error stack up,
  and merging separately-built maps is a research-grade chore.
- **UWB ranging** (indoor, the pragmatic winner): anchors on the walls give absolute
  position; tag-to-tag ranging gives *relative* position directly. This is the most
  reliable affordable answer for "robots know where their neighbours are" indoors, and the
  radio carries data too. Budget for the beacons.
- **Motion capture** (lab only): OptiTrack/Vicon give sub-millimetre truth to every unit at
  high rate — how most published swarm videos are actually made. Correct, and priced like a
  car. Great if you have a lab; not a garage answer.
- **GPS-RTK** (outdoor): centimetre-level absolute position per robot, so relative position
  is just subtraction. The clean outdoor answer for agriculture/coverage; needs a base
  station and clear sky.
- **Fiducials / vision** (cheap — the recommended *starter* for slow ground robots): ArUco /
  AprilTags on each robot plus one overhead camera gives every robot's pose in a shared frame — a
  real "indoor GPS"; or robots read tags on each other for direct relative pose (sensors.md).
  Cheapest path to relative pose and the achievable default for a first wheeled swarm (see *First
  decision*). Keep the lighting even and the tags in the camera's field of view; camera frame rate
  caps how *fast* the robots can safely move.

Be clear-eyed with users, and split the indoor answer by speed. Outdoors, GPS-RTK largely solves
it. Indoors for **slow ground robots**, an overhead camera + fiducials is the cheap answer that
actually works — that is the recommended starter. Indoors for **fast or flying** robots, where a
ceiling camera can't keep up and there is no floor to sit on, you are back to the cost of UWB
beacons or motion capture — there is no free, accurate, *high-rate* indoor option, and pretending
otherwise is how a swarm project stalls at unit two.

## Simulate the coordination first

Prove the *coordination logic* in sim before it can drive real motors into each other
(simulation-and-gyms.md):

- **Gazebo multi-robot**: spawn several namespaced robots in one world; run the actual ROS 2
  coordination and Nav2 stacks against them. Same topic names as real, so switching to
  hardware is a launch-file argument.
- **ArduPilot/PX4 SITL** scales to multiple instances (different ports/system IDs) for
  multi-vehicle flight — test formations and deconfliction with the real firmware before
  anything leaves the ground.
- **ARGoS** is purpose-built for large swarms (hundreds/thousands of simple robots) and runs
  far faster than Gazebo at that scale — the right tool when the *number* is the point.
- Test the failure cases in sim on purpose: drop a unit mid-mission, sever a comms link,
  inject position error. A swarm that only works when everything works is not finished.

## Safety: N robots, N failure modes, one big red button

Every safety rule in this skill still applies per robot — and coordination adds failure
modes that don't exist for a single machine. Enforce, don't suggest:

- **Collective E-stop.** One command must stop *every* unit, and it must not depend on the
  coordinator being alive or the network being healthy. A broadcast stop plus an
  independent per-robot hardware kill (RC-loss failsafe, a physical switch) is the belt and
  braces. Test it with the fleet moving, before you trust the fleet.
- **Per-unit geofences.** Each robot enforces its own area limit locally, so a bad command
  or a lost neighbour can't send it across the room or the field. The limit lives on the
  robot, not in the coordinator's plan.
- **Plan for the rogue or dropped unit.** Decide up front what the others do when one robot
  stops answering: freeze, return home, or close the gap — but never "assume it's where the
  plan says". A silent unit is an obstacle now, not a teammate.
- **"AI/planner proposes, a deterministic layer disposes" — per robot.** A central optimizer
  or learned policy assigning goals is a *proposer*; each robot still passes every command
  through its own velocity limits, collision avoidance, geofence, and watchdog before it
  reaches a motor (ai-ml.md). No coordinator gets direct actuator authority over the fleet.
- **Many robots on one network is an attack surface.** Ten robots means ten sets of
  credentials, ten SSH keys, ten things to patch — and one compromised unit can spam the
  shared comms. Change every default, key-based auth only, isolate the fleet's network,
  never port-forward the coordinator (security.md).

## Where swarms actually earn their keep

- **Research and education**: the honest primary use. Kilobots, Crazyflie decks, and
  ARGoS-scale sims are how people *learn* distributed robotics — and it's a deep, rewarding
  field to learn.
- **Light shows / choreography**: hundreds of drones flying scripted paths — visually
  spectacular, and mostly a precise-localization + timing problem (usually RTK or indoor
  positioning), not much autonomy.
- **Agriculture**: several cheap rovers covering rows, GPS-RTK doing the localization heavy
  lifting outdoors.
- **Area coverage / search**: mapping, monitoring, or searching a region faster with N units
  than one — the classic "many cheap beats one expensive" argument, when your localization
  and comms actually hold up at N.
