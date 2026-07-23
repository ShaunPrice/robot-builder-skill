# Ground robots: rovers, tanks, RC cars

The best first domain: failures are cheap, iteration is fast, and everything learned here
transfers to water and air.

## Drive types

| Type | Steering | Pros / cons | Best for |
|---|---|---|---|
| **Differential drive** (2 powered wheels + caster, or 4WD skid-steer) | Wheel speed difference | Simple math, turns in place / 4WD skids scrub tires & smear odometry | Indoor autonomy, SLAM, the default |
| **Tracked** | Skid steer | Great off-road, looks awesome / odometry poor (tracks slip) | Outdoor rough ground |
| **Ackermann** (RC car style) | Front steering servo | Fast, efficient / can't turn in place, needs steering geometry in the planner | Outdoor speed, GPS waypoint rovers |
| **Mecanum/omni** | Wheel vector sum | Moves any direction / expensive, hates carpet and dirt | Flat-floor demos, competition |

Beginner: differential. Outdoor/GPS: Ackermann (or big 4WD). Nav2 supports diff and
Ackermann; mecanum needs a holonomic-aware config.

## Motors and drivers

- **TT motors** (yellow gearbox, ~$2): fine for T0/T1; no encoders; stall easily.
- **Metal gearmotors with encoders** (JGA25/JGB37, Pololu): the T2 default. Pick RPM by
  speed target: wheel circumference × RPM ÷ 60 = m/s. 100–200 RPM on 65 mm wheels =
  0.34–0.68 m/s — indoor-sensible.
- **Brushless** (hobby ESCs or ODrive/moteus for real torque control): T3+, faster and
  more efficient, more complexity.
- **Drivers**: TB6612 (≤1.2 A/ch), DRV8871 (3.6 A), BTS7960 (43 A, big bots), Cytron
  MDD/MDDS series (clean, well-documented). Match driver current to motor **stall**
  current, not running current. Avoid L298N (voltage drop, heat).
- **Servos** (steering/pan-tilt): SG90 (light duty), MG996R (steering), digital metal-gear
  for anything that matters. Power servos from a 5–6 V BEC, never the Pi's 5 V pin.

## Power architecture (the thing that actually breaks)

```
Battery (2S/3S LiPo or NiMH or USB bank)
 ├── Motor driver → motors           (direct battery voltage)
 └── Buck/UBEC 5 V ≥3–5 A → Pi/MCU  (regulated logic rail)
        └── COMMON GROUND with driver (signal reference)
```

- One battery + buck is neat; two batteries (bank for Pi, pack for motors) is bulletproof
  for beginners. Either way: grounds tied together.
- Add a master switch and a fuse (or at least an XT60 you can yank).
- Symptoms of getting this wrong: Pi reboots when motors start, SD corruption, "random"
  brownouts. It is always the power architecture.

## Software ladder for a rover

1. **Teleop** (gamepad → PWM). Plain Python. Add the 500 ms watchdog immediately.
2. **Calibrated motion**: encoders → measured speed → PID per wheel → the robot drives
   straight and turns accurately. (This is where the MCU earns its keep.)
3. **Odometry**: integrate encoder ticks (+ IMU yaw — encoders lie during skid) → pose.
4. **ROS 2**: wrap steps 1–3 as the motor node; add lidar/depth; slam_toolbox → map;
   Nav2 → click-to-navigate. See ros.md.
5. **Behaviors/AI**: person following, patrol routes, LLM tasking — see ai-ml.md.

Outdoor/GPS rovers: consider running **ArduPilot Rover** on a flight controller instead
of hand-rolling — you get waypoint missions, geofences, failsafes, and a ground station
for free; the Pi/Jetson rides along for vision (see compute-platforms.md).

## Chassis pragmatics

- Buy flat aluminium/acrylic chassis with slotted holes, or 3D print (PETG > PLA for
  outdoor/heat).
- Layout: battery low and centered (stability), lidar up top with 360° clearance, camera
  at the front with an unobstructed view that includes the ground ~30 cm ahead, antennas
  away from power wiring.
- Wheels: bigger wheels = faster + better over bumps but less torque. Keep wiring
  serviceable — connectors, not solder, between modules; label both ends.

## Ground-specific gotchas

- Carpet eats small casters; thresholds eat small wheels. 65 mm+ wheels indoors.
- Skid-steer 4WD odometry is bad by physics — lean on IMU yaw + lidar scan matching.
- Direct sunlight blinds IR depth cameras — plan lidar or geometry for outdoor daytime.
- Cliff (stairs!) detection: downward ToF/IR sensor before letting a robot roam an upper
  floor. Nav2 will happily path a robot down a staircase it can't see.
- Big robots (>5 kg, >1 m/s) can hurt people: physical E-stop button wired to motor
  power — not through software — is mandatory at that scale.
