# Simulation and training gyms

Simulation is where robots crash for free, where autonomy code gets tested before it
touches hardware, and where modern control policies (legged locomotion, agile flight) are
*trained*. Every T2+ builder should run at least one simulator; every RL ambition
requires one.

## Pick the right simulator for the job

| Simulator | Best for | Hardware needs | Notes |
|---|---|---|---|
| **Gazebo (Harmonic+)** | ROS 2 robots: rovers, boats, arms | Any Linux PC | The ROS-native default; your URDF + plugins ≈ your real robot |
| **ArduPilot / PX4 SITL** | Anything with an autopilot (drones, planes, boats, rovers, subs) | Anything (CPU-only) | Fly the *actual autopilot firmware* virtually; the single highest-value sim for aircraft |
| **Webots** | Beginners; batteries-included robot models | Modest | Easiest install, good docs, less ROS-idiomatic |
| **PyBullet** | Quick Python physics, RL experiments | Modest | `pip install pybullet`, loads URDF directly; aging but frictionless |
| **MuJoCo** | Contact-rich dynamics, RL research standard | Modest (CPU) / GPU via MJX | Free/open source now; the physics quality benchmark |
| **Isaac Sim / Isaac Lab** | Photoreal sensors + massively parallel RL (legged, manipulation) | **RTX GPU required** (RTX 3070+ to start; 4090/5090-class ideal) | Thousands of robots in parallel; steepest install, biggest payoff |
| **Genesis** | Emerging ultra-fast Python-native sim/RL | GPU | Watch this space; promising, younger ecosystem |
| **OpenRocket** | Rocket stability/altitude prediction | Any | Not optional for rocketry — sim before every new design |
| **FPV sims (Liftoff, Velocidrone), RealFlight** | *Pilot* training (human skills) | Gaming PC | Different purpose: train the human, not the code |

Rules of thumb: ROS ground/water robot → Gazebo. Autopilot vehicle → SITL. RL → start
PyBullet/MuJoCo, graduate to Isaac Lab. Human flying skills → FPV sim/RealFlight.

## Digital twin: your robot in Gazebo

The payoff of writing a URDF (ros.md) is that the same file becomes the simulated robot:

1. Add inertial values (mass, inertia — estimates fine) and collision shapes to the URDF.
2. Attach plugins: `gz-sim-diff-drive-system` (accepts `/cmd_vel`, publishes odom), lidar
   and camera sensor plugins publishing the same topic names as the real drivers.
3. Bridge Gazebo↔ROS topics with `ros_gz_bridge`.
4. Now slam_toolbox, Nav2, your follow-me node — the *identical* code — run against sim.
   Develop on the desk, deploy to the robot. Keep topic names/frames identical between
   sim and real so switching is a launch-file argument, not a code change.

Worked example flow to offer users: build the rover URDF → drive it in an empty world →
add walls (Gazebo building editor) → map with slam_toolbox → Nav2 goals — the entire
autonomy stack proven before the real robot's battery is even charged.

## SITL: simulated aircraft, real firmware

```bash
# ArduPilot: after cloning ardupilot and installing prereqs
sim_vehicle.py -v ArduCopter --map --console      # a virtual quad appears
# connect QGroundControl / Mission Planner / pymavlink to udp:127.0.0.1:14550
```

- Plan missions, test failsafes (kill the virtual RC! drain the virtual battery!), and
  run the *same companion-computer scripts* that will fly the real aircraft — pymavlink
  code can't tell sim from real.
- PX4 equivalent: `make px4_sitl gz_x500` (Gazebo-backed).
- Gate for real flights: a new mission or companion script flies clean in SITL first.
  This rule prevents most autonomy crashes.
- HITL (hardware-in-the-loop, real FC + simulated physics) exists but SITL covers 95% of
  needs with none of the wiring.

## Training gyms (RL): from Gymnasium to Isaac Lab

**The Gymnasium API** is the lingua franca — every RL library speaks it:

```python
import gymnasium as gym
class BalancerEnv(gym.Env):
    def reset(self, seed=None): ...   # → obs, info        (randomize start state!)
    def step(self, action): ...       # → obs, reward, terminated, truncated, info
```

Path for a hobbyist who wants "my robot learns X":
1. **Sanity-check the loop** on a built-in env: `CartPole-v1` (which *is* the
   self-balancing robot, abstracted) with stable-baselines3 PPO — 20 lines, trains in
   minutes on CPU. Teaches obs/action/reward/rollout mechanics.
2. **Wrap your own sim** (PyBullet/MuJoCo loading your URDF) as a Gymnasium env: obs =
   [tilt, tilt_rate, wheel_vel…], action = wheel torques, reward = upright bonus −
   tilt² − effort penalty. Train PPO/SAC. Reward shaping is where all the craft lives —
   iterate in small steps and log everything (wandb/tensorboard).
3. **Scale up in Isaac Lab** when episodes are expensive (legged locomotion): thousands
   of parallel envs on an RTX GPU, walking policies in hours. Use the shipped example
   tasks (Anymal/Go2/humanoid) as templates rather than starting blank.
4. **Cross the sim2real gap** deliberately:
   - Domain randomization: randomize mass, friction, latency, sensor noise, motor
     strength every episode — policies that survive randomization survive reality.
   - Match the *interface*: same obs the real robot can actually measure (no oracle
     state), same control rate, an action filter/rate-limit identical in both.
   - Add sensor delay/actuation lag models — the #1 unmodeled reality.
   - Deploy behind the same safety layer as everything else (tilt cutoffs, torque
     clamps, E-stop): a policy is just another proposer in the ai-ml.md architecture.

**Honest expectations**: RL for locomotion/acrobatics = proven and spectacular; RL for
"do my whole mission end-to-end" = research. For navigation-shaped problems, Nav2 +
behavior code beats a learned policy at hobby scale. Behavior cloning (ai-ml.md) is often
the cheaper first rung of "learning".

## Where to run heavy sims

Isaac Sim/Lab and big MuJoCo runs want a desktop RTX box (an RTX 3070+ gaming PC is
enough to start; more VRAM = more parallel envs). Headless training on a remote GPU
machine over SSH is the comfortable pattern — train there, copy the policy (`.onnx`/
`.pt`) to the robot for inference (Jetson runs exported policies easily; they're tiny
compared to LLMs). No GPU at all → stay in PyBullet/MuJoCo-CPU and train smaller tasks,
or rent a cloud GPU by the hour for training bursts (keep credentials scoped —
security.md rules apply to cloud GPUs too).

Containers are the sane way to install the heavy ones — Isaac ships official NGC images,
Gazebo comes inside the `osrf/ros:*-desktop-full` images, ArduPilot SITL builds from the
repo's own Dockerfile (MuJoCo is just `pip install mujoco` — no container needed); see
docker-and-environments.md before fighting a native install.
