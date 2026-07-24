# Instrumentation & control: PID to self-balancing, bipeds, and flight stability

This is the "make it behave" module. Everything here sits in the FAST and MID loops of the
three-loop architecture (see ai-ml.md) — deterministic code, tuned with data.

## Instrumentation first (you can't control what you can't measure)

- **The measurement chain**: sensor → wiring → ADC/driver → filter → units → timestamp.
  Debug in that order. Most "control" problems are measurement problems wearing a costume.
- **Sample fast enough**: control loop ≥10× faster than the dynamics you're taming.
  Balancing robot: 100–500 Hz. Drone rate loop: 1–8 kHz (the FC handles it). Rover
  velocity PID: 20–50 Hz is fine.
- **Filter deliberately**:
  - *Complementary filter* (one line: `angle = α·(angle + gyro·dt) + (1−α)·accel_angle`)
    fuses gyro (smooth, drifts) with accelerometer (noisy, absolute) — perfect for
    balancing robots, and teaches the concept behind every fancier filter. α is
    dt-dependent: it encodes a time constant τ via `α = τ/(τ+dt)` — the folklore 0.98
    assumes ~100 Hz; at 200 Hz the same τ (~0.5 s) needs α ≈ 0.99. Copying a coefficient
    without matching the loop rate quietly changes the filter.
  - *Kalman/EKF*: what autopilots and `robot_localization` run internally. Use the
    libraries; hand-rolling an EKF is a course, not a build step.
  - Low-pass everything from accelerometers near motors; but every filter adds **lag**,
    and lag is poison to stability — filter as little as you can get away with.
- **Calibrate**: gyro bias at rest on every boot; accel level offset; encoder
  ticks-per-meter by driving a measured distance; ESC/servo endpoints. Store constants in
  config files in the repo, not magic numbers in code.
- **Beware aliasing and jitter**: read sensors on a timer, not "as fast as the loop
  spins"; measure real `dt` and use it; log timestamps and plot them — a control loop
  with 30% timing jitter tunes like a haunted house.

## PID without tears

```python
error = setpoint - measurement
integral += error * dt                      # clamp this (anti-windup)!
derivative = (error - prev_error) / dt      # or derivative-on-measurement to avoid setpoint kick
output = Kp*error + Ki*integral + Kd*derivative
```

- **Manual tuning that works**: zero everything. Raise Kp until it responds briskly and
  just starts to oscillate; halve it. Add Kd to kill overshoot/oscillation. Add a little
  Ki last, only to remove steady-state error. Change one gain at a time; log and plot
  every run.
- **The traps**: integral windup (clamp the integral, and reset it on mode changes),
  derivative amplifying sensor noise (filter the D term), motor deadband (add a
  feedforward offset so small outputs actually move the motor), and loop-rate changes
  invalidating gains (gains are only meaningful at a fixed, stated dt).
- **Cascaded loops** — the pattern behind almost every real robot: a fast inner loop
  controls the fast variable, a slower outer loop commands the inner one.
  Drone: rate ← attitude ← velocity ← position. Balancer: motor/velocity ← tilt angle ←
  travel speed. Tune inner loops first, always.
- **Feedforward**: if you can predict most of the needed output (gravity, drag, known
  setpoint change), add it directly and let PID clean up the remainder — smaller gains,
  better behavior.

## Self-balancing robots (the best control-theory teacher, ~$80 on top of T1)

A two-wheel inverted pendulum: MPU6050-class IMU + 2 encoder gearmotors + decent driver +
an MCU running a 100–200 Hz loop (ESP32/Pico — not a Pi with Linux jitter; this is the
canonical reason for the two-brain pattern).

Build sequence:
1. Read tilt at 200 Hz via complementary filter; print/plot it; verify sign conventions by
   hand-tilting.
2. Inner PID: tilt angle → motor output. Tune (Kp→Kd→tiny Ki) with the robot held over
   foam. It will oscillate, then shiver, then stand. Enormously satisfying.
3. Outer loop: desired tilt ← velocity error (so it stops drifting across the room), then
   steering by differential output, then (optional) position hold from encoders.
4. Cutoffs: kill motors beyond ±30–45° tilt (it has fallen; stop grinding).

**Oscillation triage** (in order of likelihood when a balancer shakes or falls):
1. Kd too small relative to Kp — no damping (typical working ratio: Kd ≈ Kp/20–Kp/50 at
   these loop rates, then tune).
2. Unclamped integral — winds up in ~1–3 s, then diverges: the classic "stands briefly,
   then violently falls" signature. Clamp it, or zero Ki until the rest works.
3. dt jitter — loop not on a hardware timer, or dt assumed instead of measured.
4. Vibration/filter lag — accel noise reaching the D term, or over-filtered angle
   arriving late.
5. Motor deadband — small corrections do nothing, then overshoot (add feedforward
   offset).

Common failures beyond triage: gains tuned at one battery voltage misbehave at another
(scale output by measured voltage); vibration-corrupted accel (foam-mount the IMU);
backlash in cheap gearmotors; sign errors after remounting the IMU.
Kits exist (Elegoo Tumbller, Osoyoo) if wiring from scratch is a blocker — the tuning
lessons are identical.

## Legged robots: quadrupeds and bipeds (honest guidance)

- **Difficulty ladder**: wheeled → self-balancer → quadruped → biped. Each step is ~10×
  the control complexity. Don't let a beginner start at biped; point them at the ladder.
- **Hobby quadrupeds**: servo-driven kits (Petoi Bittle ~$300, SpotMicro 3D-print +
  12 servos, ~$300–500 DIY) walk with scripted gaits (trot/creep) — great mechatronics
  education, quasi-static control (always statically stable-ish). Unitree Go2 (~$1,800+)
  for a real dynamically-stable platform.
- **Hobby bipeds**: servo walkers (17-DOF humanoid kits, ~$150–400) do slow,
  quasi-static walking: keep the center of mass over the support foot (the ZMP idea),
  shift weight → step → repeat. They do not balance dynamically — manage expectations.
- **Dynamic legged locomotion** (real walking/running) is today done with **RL in
  simulation**: train a policy in Isaac Lab/MuJoCo with domain randomization, deploy to
  hardware. This is the strongest reason in the whole skill to learn the simulation
  stack — see simulation-and-gyms.md. Open projects worth naming: MIT Mini Cheetah
  derivatives, ODRI Solo, Berkeley Humanoid Lite, ToddlerBot — advanced-tier builds
  ($3k+, machining/strong servos), but the sim training is free to learn *now*.
- Actuators are the real cost: hobby servos (position-only, no torque sense) cap you at
  quasi-static gaits; quasi-direct-drive actuators (the Mini-Cheetah trick) are what make
  dynamic legs possible, and they're $100–300 *per joint*.

## Flight control and stability

**Multirotors** — the FC runs the cascade (rate←attitude←position); your job is tuning
and vibration hygiene:
- Betaflight: fly the defaults first (they're good); then small Kp/Kd steps on one axis at
  a time; use blackbox logs, not vibes. Propwash oscillation, hot motors, and D-term
  noise are the classic symptoms — filtering settings and soft-mounting fix more than
  gain changes do.
- ArduPilot/PX4: run **AutoTune** — it flies test twitches and writes gains better than
  hand-tuning for camera/mission craft. Verify vibration metrics in logs are in range
  first, or autotune tunes the vibration, not the airframe.
- Instability checklist before touching gains: balanced props? FC soft-mounted? wiring
  taut (flapping wires = noise)? correct motor order/direction? Then logs.

**Fixed wing** — stability is mostly *built*, not coded:
- **CG is 90% of it**: balance at the marked point (typically 25–33% of mean wing chord).
  Nose-heavy flies badly; tail-heavy flies once. Check CG before every maiden.
- Static stability comes from CG-ahead-of-neutral-point, dihedral (roll), and tail volume
  (pitch/yaw) — kits already embody this; scratch designers should copy a proven planform
  before inventing one.
- Trim flights first (manual, trim level flight), then let ArduPlane's TECS/L1
  controllers do energy and lateral management; feed them a real airspeed sensor for
  reliable auto behavior.

**Rockets** — passive stability, precisely: center of pressure (CP) must sit 1–2 body
calibers *behind* CG (use OpenRocket — free — to simulate before flying); over-stable
rockets weathercock into wind, under-stable ones somersault. Fins do this passively at
speed; TVC hobby projects actively hold vertical during the slow initial climb
(stabilization only — see the legal line in air-robots.md). Spin-stabilization is the
third classic answer for small rockets.

## When PID isn't enough (pointers, not rabbit holes)

LQR (optimal gains for linear systems — the balancing robot's "pro mode"), MPC (predictive,
constraint-aware — how bigger drones and rovers plan), and learned policies (RL — see
simulation-and-gyms.md). Teach these only when a tuned PID visibly hits its ceiling;
for 90% of hobby robots, cascaded PID + feedforward is the ceiling.

## Hexapods (six-legged robots)

The best-kept secret in legged robotics: a hexapod is **statically stable**, so it is the
one legged form a beginner can actually learn on without the fall-over frustration. Split
the six legs into two tripods (legs 1-3-5 and 2-4-6); at least one tripod is always planted,
and three ground contacts define a support triangle. Keep the center of mass inside that
triangle and the robot cannot topple — it can freeze mid-gait, hold a pose, or lose a leg
mid-step and stay upright. That means you get to learn gaits and per-leg inverse kinematics
*in isolation*, without also fighting dynamic balance the way a biped forces you to (see the
difficulty ladder above — hexapods sit a rung to the side of it, not further up it).

- **Anatomy**: the classic build is **18 servos — 3 DOF per leg × 6 legs**. Per leg the
  joints are coxa (hip yaw, swings the leg forward/back), femur (lift), and tibia (extend).
  Each leg is therefore a small 3-DOF arm, and you solve **per-leg inverse kinematics** to
  place each foot at a commanded (x, y, z): coxa angle from `atan2(y, x)`, then a planar
  2-link solve for femur/tibia. This is the same math as a tabletop arm — cross-reference
  manipulation-and-arms.md and reuse it six times.
- **Gaits** (the fun part, and pure kinematics — no balance controller needed):
  - *Tripod* — alternate the two tripods; three legs swing while three support. Fast,
    always statically stable, the one to code first.
  - *Ripple* and *wave* — move one (ripple: overlapping) or one-at-a-time (wave) leg, five
    on the ground at all times. Slow and maximally stable, good for rough ground or heavy
    payloads. A gait is just a phase table: per leg, when to lift and where to plant.
- **Kits and cost tiers**:
  - **Freenove Hexapod** (~$100-150, 18× MG90/MG996-class servos, ESP32 or Pi) — the honest
    beginner entry; you will fight the servos, but the price is right.
  - **Hiwonder SpiderPi** (~$400-600, bus servos + Pi + camera) — mid-tier with vision.
  - **Trossen PhantomX MK-III** (~$1,000+, Dynamixel AX/MX serial servos) — the "it just
    works" tier: contactable torque, feedback, and a clean ROS story.
- **The real challenge is power and wiring, not the gait.** Eighteen servos stalling
  together pull tens of amps in spikes. **Do not run servo power off the Pi's 5V rail** —
  that is how you brown out and reboot mid-step (see the power-architecture note in
  ground-robots.md). Use a dedicated servo **BEC/UBEC** sized for the stall case (a 5-6V
  6-10A UBEC minimum; the big kits want more), a fat common-ground star, and bulk
  capacitance across the rail. Drive the servos through a **PCA9685** 16-channel PWM board
  (you need two for 18 channels) or, better, a **serial-servo bus** (Dynamixel, Hiwonder,
  Feetech) so one data line addresses every joint and you get position feedback for free.
  Budget for the current spikes up front — undersizing the BEC is the number-one hexapod
  build failure.
- **Honest take**: a hexapod is the form to *learn* legged locomotion on — gaits, IK, and
  servo power management, all without the tuning agony of dynamic balance. It is genuinely
  beginner-friendly in a way nothing else on legs is. Once it walks, the quadruped and then
  the biped are the harder, dynamic-balance rungs (covered above) — and that is where the
  "prove it before it can hurt you" discipline and RL-in-simulation path start to matter.
