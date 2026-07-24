# Robotic arms and manipulation: reach, grasp, and don't get pinched

The "robots that reach and grasp" domain. An arm is a chain of actuators ending in a hand;
it is the most *concentrated* robot you can build — all the cost and control theory of a
mobile robot packed into one meter of workspace, with none of the "drive away from the
problem" escape hatch. Two mounting stories: **bench-mounted** (fixed base, a table-top
manipulator) or **mobile manipulation** (an arm riding a rover — the hard mode, covered at
the end). Start bench-mounted; the base frame not moving is a gift.

## Anatomy and degrees of freedom

An arm is joints in series: base yaw → shoulder pitch → elbow pitch → one or more wrist
joints → gripper. Count the joints and you have the DOF:

- **4-DOF** (SCARA-ish, or a cheap servo arm): reaches a point, limited orientation. Fine
  for pick-and-place onto a flat surface where the hand always points down.
- **6-DOF**: the honest minimum for full position **and** orientation — the hand can reach
  a pose from any angle. This is what "a real arm" means; buy 6 if you can.
- **7-DOF** (redundant): an extra joint means many arm configurations reach the same pose,
  so it can dodge obstacles and singularities. Lovely, and overkill for a first build.

Three specs decide everything, and vendors quote all three — **reach** (max radius, e.g.
280 mm), **payload** (mass at full reach, *including the gripper* — read the fine print),
and **repeatability** (how tightly it returns to a taught point, e.g. ±0.5 mm). Buy one
tier below the reach and payload you imagine you need: arms get expensive as the cube of
their capability, and a 250 g payload does more than beginners expect.

## The actuator ladder (the honest cost story)

The joints *are* the arm. Everything else is brackets. Mirrors the drive-motor and
flight-actuator ladders — pick the rung, and the arm's whole character follows.

| Rung | Actuator | ~2026 USD | Feedback | Verdict |
|---|---|---|---|---|
| 0 | Hobby servo (SG90 ~$2, MG996R ~$4) | $2–4/joint | None (open-loop) | Backlash, no load sense — toy/learning arms only |
| 1 | Smart serial servo (Feetech STS3215 ~$10–15; Dynamixel XL330 ~$25, XM430 ~$90) | $10–90/joint | Position + load, daisy-chain | The hobby sweet spot |
| 2 | Stepper + belt/harmonic (Annin AR4 DIY 6-axis ~$2k) | ~$2k/arm | Encoders/steps | Precision, real payload, a real build |
| 3 | Quasi-direct-drive BLDC (force control) | $100–300/joint | Torque | Research frontier — compliant, contact-rich, dear |
| 4 | Industrial harmonic-drive + servo (UFACTORY xArm, Franka Research 3) | $5k–$30k+ | Everything | Turnkey, safe, out of hobby budget |

Rung 0 teaches you *why* rung 1 exists: an SG90 has no idea where it is or what it's
holding, so backlash and missed positions are unfixable in software. **Smart serial
servos** are the answer for 90% of hobby arms — the Feetech STS3215 (the servo behind the
LeRobot SO-100/SO-101) gives you position *and* load feedback over a single daisy-chained
bus, closing its own position loop internally, for the price of a coffee. Dynamixels are
the premium version: cleaner, ROS-native, and priced like it.

## Platforms by tier

- **Learning / cheap (T1):** the **LeRobot SO-101** (~$115–250 to build, Feetech servos) is
  the current darling — a printable, imitation-learning-native arm with a leader/follower
  teleop pair. Below it, generic 4-DOF servo arm kits (~$50–100) teach kinematics and
  disappoint at everything else.
- **Intermediate (T2):** **Elephant Robotics myCobot 280** (6-DOF, `pymycobot`, ROS) is the
  plug-and-play favorite; **Dobot Magician** and **WLkata Mirobot** are closed but tidy for
  education; the **Trossen/Interbotix PincherX / ReactorX** line (Dynamixel, ROS-native,
  **MoveIt 2 out of the box**) is the pick if ROS is your destination.
- **Advanced build (T3):** the **Annin Robotics AR4** — a ~$2k stepper 6-axis you assemble,
  with genuine precision and a few hundred grams of payload. This is the "I want to *build*
  an arm" answer.
- **Pro (T4):** **UFACTORY xArm / Lite6** and **Franka Research 3** — force-limited,
  collision-aware, and priced as capital equipment. See parts-and-budgets.md (arms already
  live in the T3/T4 rows).

## Kinematics: use the library, always

**Forward kinematics** (joint angles → hand pose) is straightforward trigonometry down the
chain. **Inverse kinematics** (desired pose → joint angles) is the hard direction: multiple
valid solutions, no solution outside the workspace, and **singularities** where the math
blows up (the classic wrist-aligned "gimbal" pose). This is the arm's EKF: do not
hand-roll it. Use **MoveIt 2**'s IK, **ikpy**, **PyBullet**, or the vendor SDK. Hand-solve
a 2–3 DOF planar arm *once*, as a learning exercise, to feel the geometry — then never
again. (The chain is described by **DH parameters**, four numbers per joint; the library
reads them from your URDF.)

## Software

- **ROS 2 + MoveIt 2** is the standard: motion planning, collision avoidance, and IK in one
  stack, working with Interbotix and many arms. This is the path to mobile manipulation and
  Nav2 integration — see ros.md.
- **Vendor SDKs** (`pymycobot`, Dobot SDK, xArm SDK) are the fast on-ramp — a dozen lines to
  move a joint — with less planning power. Start here, graduate to MoveIt when you need
  collision-aware paths.
- **LeRobot** is the modern "vibe-code an arm to do a task" path: teleop-**record**
  demonstrations → train an **imitation** policy (ACT, diffusion policy) → run it
  autonomously. It connects straight to ai-ml.md (imitation and VLA models) and is the most
  fun a beginner can have with a manipulator.

## Grippers and end effectors

- **Parallel-jaw servo gripper** — the default; two fingers, one servo, taught or
  current-limited closing force. Handles most objects.
- **Vacuum / suction** (venturi off a compressor, or a small electric pump) — unbeatable on
  flat, rigid, non-porous objects (boxes, glass, sheet metal); useless on soft or leaky
  ones.
- **Soft / compliant grippers** (silicone fingers, Fin-Ray) — forgiving of pose error and
  fragile objects; low precision.
- **Custom 3D-printed** fingers for one specific part, and a **quick-change plate** so you
  can swap tools without rewiring. The gripper is where a generic arm becomes *your* arm.

## The grasping ladder (honest, like the AI ladder in ai-ml.md)

1. **Taught fixed poses** (teach-and-repeat): drive the arm to a point, record the joint
   angles, replay. No vision, boringly reliable, and the correct answer for any task where
   parts arrive in the same place. Most working hobby arms never leave this rung.
2. **Fiducial-guided** (AprilTag/ArUco): a marker gives a precise object pose → offset to a
   grasp. Poor-man's vision, rock-solid for docking and jigs (see sensors.md).
3. **Vision-guided**: YOLO detection + depth (RGB-D from ai-ml.md / sensors.md) → box center
   + median depth → grasp pose. The first rung that copes with objects that move.
4. **Learned** (LeRobot ACT / diffusion / VLA): the policy proposes grasps from pixels. The
   frontier, brittle off-distribution, and — like every learned controller — a *proposer*,
   not an authority (see the safety section and ai-ml.md's three-loop rule).

## Sensors and control

Joint **encoders live inside the smart servos** — you get position and a load estimate for
free. A wrist **force/torque sensor** unlocks contact tasks (insertion, wiping, "push until
it touches") but costs more than a hobby arm; **motor current is a cheap force proxy** that
gets you 80% of the way (a jump in current means the gripper hit something). Cameras mount
**eye-in-hand** (on the wrist, moves with the tool — great for close-in alignment) or
**eye-to-hand** (fixed, watching the whole workspace); see sensors.md. Control-wise, each
joint runs a **PID** loop (see control-and-stability.md), the planner hands down an
interpolated **trajectory**, and smart servos close their own position loop so you command
setpoints, not PWM.

## Safety (enforced — an arm is not a rover)

An arm has no "drive away" escape and no natural rest: it can strike **anywhere in its
spherical workspace**, fast, and a planned move can swing the elbow into a place you
weren't watching. Every joint is a **pinch/crush point**. These are hard rules:

- **Prove it slow.** Run *all* new motion at reduced speed and torque — this is the arm's
  analog of props-off / wheels-off-the-ground. A taught path at 10% speed reveals the
  collision that full speed would deliver into your hand.
- **Know your class.** **Force-limited cobots** (Franka, xArm) sense contact and stop;
  everything cheaper (any servo or stepper arm) does **not** and must be treated as able to
  hurt you — cage it, or keep your body out of its reach envelope during autonomous runs.
- **E-stop wired to servo/motor power**, not through software — a hardware cut the planner
  cannot override or out-vote (the same rule as big ground robots in ground-robots.md).
- **Hands out of the workspace during autonomous or learned runs.** Watch, don't reach.
- **A learned/imitation/VLA policy is just another proposer** and MUST run behind the
  deterministic layer: workspace (joint-limit) clamps, velocity/torque caps, and the E-stop
  (ai-ml.md's "AI proposes, the fast loop disposes"). The policy picks grasps; the limits
  decide what the motors are *allowed* to do.

## Mobile manipulation (an arm on a rover — hard mode)

Bolting an arm to a mobile base multiplies the problems, not adds them:

- **Power budget**: arm servos are hungry and stall hard; size the base battery and BEC for
  the arm's **stall** current, not its idle draw (see parts-and-budgets.md / ground-robots.md
  power architecture).
- **Reach vs. stability**: an extended arm throws the combined **center of gravity** past
  the wheelbase and tips the robot — the classic mobile-manipulation faceplant. Keep the arm
  tucked while driving; only extend with a stable base, and widen the wheelbase or ballast
  low if you must reach far.
- **One TF tree**: the arm's base frame must be published into the robot's **TF** tree
  (`base_link → arm_base → ... → gripper`) so MoveIt plans in the same world Nav2 drives in
  (see ros.md). A VLA-driven mobile manipulator wants a real Jetson for onboard inference
  (see compute-platforms.md).
