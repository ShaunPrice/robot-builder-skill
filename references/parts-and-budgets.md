# Parts selection by budget and skill level

Prices are approximate USD (2026). **Convert before tiering**: AU street prices run
~1.5–1.7× the USD number (Pi 5 4GB ≈ A$105, Orin Nano Super ≈ A$430+), UK/EU ~1.1–1.3×
in local currency. A "$250 AUD" user is a ~$160 USD user — tier accordingly, and sanity-check
a local vendor (e.g. Core Electronics in AU) before finalizing a list. Always reserve
20–30% of the budget for batteries, charger, tools, spares, and connectors.

## The tier table (start here)

| Tier | Budget | Skill floor | What you get | Typical build |
|---|---|---|---|---|
| T0 "Drive it" | < $100 | Beginner | Controller-only fun, no code required (code optional) | RC car kit, micro:bit/ESP32 robot kit |
| T1 "Code it" | $100–300 | Beginner | Programmable rover with camera | Pi 4/5 or ESP32 rover kit + Pi Camera |
| T2 "Sense it" | $300–800 | Intermediate | Autonomy-capable ground/water robot, or entry aircraft | Pi 5 rover + lidar or depth cam; ArduPilot boat; 5" FPV quad |
| T3 "Think it" | $800–2,500 | Intermediate+ | Real edge-AI robot | Jetson Orin Nano rover + RealSense/OAK-D; PX4 dev drone |
| T4 "Research it" | $2,500+ | Advanced | Lab-grade | Jetson AGX Orin, robot arm, VIO drone, BlueROV2 |

Rule of thumb: **buy one tier below what the user thinks they want** for a first robot.
Skills transfer up; wasted money doesn't.

## T0 — Controller-only (<$100)

No soldering, no Linux. Great for kids and total beginners.

- **RC car/tank kits**: entry hobby-grade (not toy-grade) RTR cars start ~$70–100
  (nicer ones $120+, spilling into T1 money — fine if driving *is* the goal), or a
  tracked chassis + off-the-shelf ESC + RC receiver.
- **Coding-optional kits**: ELEGOO Smart Robot Car (Arduino, ~$60–80), SunFounder or
  Freenove kits, micro:bit robots (Cutebot, ~$40 + micro:bit), mBot (~$90).
- What they learn: driving, charging discipline, how servos/ESCs/receivers connect.
- Upgrade path: every T0 chassis can later take a Pi or ESP32 — buy a kit with space.

## T1 — First programmable robot ($100–300)

- **Compute**: Raspberry Pi 5 4GB (~$60) or Pi 4 4GB (~$55). ESP32 (~$8) if they prefer
  Arduino-style. Pi Zero 2 W (~$18) for tiny builds.
- **Chassis**: 2WD/4WD robot chassis kit with TT motors (~$15–25), or a better kit like
  Waveshare/SunFounder Pi rovers (~$60–150 incl. electronics).
- **Motor driver**: TB6612FNG (~$5) or DRV8871 (~$6 each). *Avoid the L298N* — it wastes
  ~2 V and half the battery as heat; it only survives in tutorials by inertia.
- **Camera**: Pi Camera Module 3 (~$25) or any UVC USB webcam.
- **Power**: USB power bank for the Pi + 6×AA NiMH or 2S LiPo for motors (separate rails;
  common ground). **For kids and first-timers prefer NiMH/AA/USB-bank power** — no fire
  risk, no charging discipline needed; graduate to LiPo at T2. A 5 V/5 A UBEC (~$10) lets
  one battery run both rails later.
- **Controller**: any Bluetooth gamepad (8BitDo, Xbox, DualSense).
- **Must-buy sundries**: jumper wires, breadboard, multimeter (~$15 one is fine), small
  screwdriver set, side cutters, velcro straps, zip ties.

## T2 — Sensors and autonomy ($300–800)

Everything in T1 plus:

- **Lidar**: RPLIDAR A1/C1 (~$70–100) — the classic SLAM starter. LDROBOT LD19 (~$90).
- **Depth camera** (choose lidar *or* depth first, not both): OAK-D Lite (~$150, has an
  onboard NPU — great on a Pi), or used RealSense D435 (~$150–250).
- **Rangefinders**: TF-Mini / TF-Luna ToF (~$20–40) for bump-level sensing; HC-SR04
  ultrasonic (~$3) works but is noisy.
- **IMU**: BNO055 (~$25, does its own fusion) or MPU-9250/ICM-20948 (~$10).
- **GPS** (outdoor): u-blox M8N/M10 module (~$25–40).
- **Better chassis**: metal gearmotors with encoders (JGA25/JGB37, ~$12–18 each) — encoders
  are what make real odometry (and therefore SLAM/Nav2) possible. A proper 4WD aluminium
  chassis or a tracked one (~$60–150).
- **Soldering iron** if they don't have one: Pinecil (~$26) or TS101 — genuinely good.
- Water option: this budget builds a solid ArduPilot autonomous *surface* boat
  (see water-robots.md). Air option: a 5" FPV freestyle quad kit or a build-from-parts
  Betaflight quad lives here (see air-robots.md) — but flying skills cost sim time, not money.

## T3 — Edge AI ($800–2,500)

- **Compute**: NVIDIA **Jetson Orin Nano Super devkit (~$249)** — the default AI-robot
  brain: 67 TOPS, runs YOLO in TensorRT at high FPS and small LLMs/VLMs locally. Jetson
  Orin NX 16GB (~$700 on carrier) if they need more headroom.
- **Depth**: Intel RealSense D435i (~$300–350, the *i* has an IMU — worth it) or D455;
  OAK-D Pro (~$250–400) if they want depth + onboard NN in one USB device.
- **Lidar upgrade**: RPLIDAR S2/S3, or Livox Mid-360 (~$750) for 3D.
- **Platform**: build on the T2 rover, or buy a dev platform: Yahboom/Hiwonder Jetson
  rovers (~$400–900), LeRobot SO-101 arm (~$200–350) for manipulation, or a 250-class
  PX4 dev drone (Holybro X500 V2 kit + Pixhawk 6C, ~$600–900).
- **RTK GPS** (cm-accurate outdoor): u-blox ZED-F9P based, ~$200–300 + base/NTRIP.
- **Power**: real LiPo setup — 3S/4S packs, ISDT/ToolkitRC charger (~$50–80), LiPo bag,
  XT60 connectors, battery checker/alarm (~$5).

## T4 — Research grade ($2,500+)

Jetson AGX Orin (~$2,000), BlueROV2 (~$4,500+), Unitree Go2 (~$1,800+ for Air), commercial
VIO modules (ModalAI VOXL), robot arms with force sensing, Ouster/Livox 3D lidar. At this
tier, work backwards from the mission; don't buy hardware speculatively.

## Skill-level modifiers

- **Beginner**: prefer kits over parts; nothing that requires soldering to first success
  (crimped/plug connectors exist for almost everything now); Pi over Jetson (bigger
  community, more forgiving); ground over air.
- **Intermediate**: parts over kits (cheaper, teaches more); encoders + IMU from day one;
  can go straight to T2.
- **Advanced**: skip to the compute/sensor list matching their mission; the interesting
  choices are Jetson tier, depth-vs-lidar, and autopilot ecosystem (see domain files).

## Domain surcharges (honest numbers)

- **Water** adds waterproofing cost: penetrators, epoxy, enclosures. Surface boat ≈ ground
  robot +$50–100. Submersible ROV is a different sport: $500 DIY minimum, realistically
  $1,000+ (see water-robots.md).
- **Air** adds crash budget: assume the first quad gets rebuilt twice. Budget +50% in
  props/arms/spares, plus a radio (RadioMaster Pocket/Boxer ~$65–130) and simulator time.
  Rockets: motors are consumable (~$5–30/flight, certification needed for big ones).
- **Every domain**: shipping on batteries is restricted in many countries — buy LiPos from
  a domestic vendor.

## Where to buy

- **Global**: official Raspberry Pi resellers, SparkFun, Adafruit, Pololu (motors/drivers —
  excellent docs), Mouser/Digi-Key (components), GetFPV/RaceDayQuads (drones), Blue
  Robotics (marine), HobbyKing (RC), AliExpress (cheap, slow, QC lottery — fine for
  chassis/brackets, risky for chargers/batteries).
- **Australia**: Core Electronics (Pi/Jetson/sensors, local support), Little Bird, Phaser
  FPV / Mantis FPV (drones), local hobby shops for LiPos.
- Advise against no-name LiPo chargers from marketplace sellers — chargers are a
  fire-safety item; buy known brands (ISDT, ToolkitRC, SkyRC).

## The universal starter toolkit (~$60–100, buy once)

Multimeter, soldering iron + solder + flux, side cutters, wire strippers, M2/M2.5/M3
hex drivers, precision screwdrivers, hot glue or E6000, heat-shrink assortment, XT60
pairs, silicone wire (18–22 AWG), zip ties, velcro battery straps, isopropyl alcohol.
