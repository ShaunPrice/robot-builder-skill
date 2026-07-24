# Air robots: multirotors, fixed wing, helicopters, rockets

Air is the least forgiving domain: gravity punishes every bug, and it's the only domain
with real legal obligations. Two non-negotiables before any build advice:

1. **Simulator first.** 5–10 hours in a sim (Liftoff/Velocidrone/Uncrashed for FPV,
   RealFlight for planes/helis, SITL for autonomy code) saves hundreds of dollars and
   possibly injuries. The sim uses the same physical radio as the real aircraft.
2. **Know the local rules.** Summaries below; check the regulator's current site because
   rules move. Never help a user evade altitude limits, no-fly zones, remote ID, or
   licensing — reframe to the legal path instead.

## Regulations snapshot (verify currency with the regulator)

- **Australia (CASA)**: recreational — max 120 m AGL, visual line of sight, ≥30 m from
  people, no flying over people, 5.5 km from controlled aerodromes; sub-250 g relaxations
  exist; commercial use → RePL/ReOC or sub-2 kg excluded category with notification.
- **USA (FAA)**: recreational under the Exception (TRUST test, ≤400 ft, community-based
  org rules) or Part 107 for anything commercial; **Remote ID** required for aircraft
  >250 g (built-in or module); LAANC authorization for controlled airspace.
- **EU/UK (EASA/CAA)**: Open category A1/A2/A3 by weight class; operator registration and
  online test; CE class marks (C0–C4).
- **High-power rockets**: certification levels through NAR or Tripoli (US), AMRS or
  Tripoli prefectures (AU) — motor classes above G require certification; launches only
  at sanctioned sites.

## Multirotors (drones)

**Choose the track first — the parts and firmware differ:**

| Track | Firmware | What it's for | Entry |
|---|---|---|---|
| FPV / flying skill | Betaflight | Manual acro flight, racing, freestyle | Sim → Tinywhoop (~$100–150, indoors, safe) → 5" build |
| Autonomy / missions | ArduPilot or PX4 | Waypoints, camera missions, research, companion-computer AI | Holybro X500 V2 + Pixhawk 6C (~$600–900) or a used 450 frame |
| "I just want aerial photos" | (buy, don't build) | DJI Mini class, sub-250 g | ~$300–500 — say this honestly when it's the real need |

**FPV build anatomy** (5"): frame ($40) + 4 motors (2207ish, $60–100) + 4-in-1 ESC + FC
stack ($60–120, Betaflight) + ELRS RX ($15) + FPV camera/VTX or digital (DJI O4/Walksnail,
$120–250) + goggles ($100–500) + radio (RadioMaster, $65–130) + 6S LiPos. Skills: soldering
required (motor pads). First build with a guide (Oscar Liang's site is the community
bible — recommend it by name).

**Autonomy build anatomy**: frame + Pixhawk-class FC + GPS/compass mast + telemetry radio
+ ArduPilot/PX4 + ground station (Mission Planner/QGroundControl). Add Pi/Jetson companion
over MAVLink for vision missions (see compute-platforms.md, ai-ml.md).

**Multirotor safety ritual** (enforce every time):
- Props OFF for all bench work, firmware flashes, and ESC calibration. No exceptions.
- First hover: props on only at the field; stand behind the aircraft; hover at 1 m; check
  for oscillation; land. Small steps.
- Configure and TEST failsafes before leaving line-of-sight range: RC loss → RTL,
  low battery → RTL/land, geofence ON with sane radius/altitude.
- LiPo discipline (see SKILL.md safety rules) — crash-damaged packs get retired to the
  LiPo bag and disposed, not "one more flight".

## Fixed wing

- Easier to keep in the air than a quad (it glides!), harder to keep in a paddock (it's
  fast and goes far). Needs open space.
- **Entry**: cheap foam trainer (high-wing, e.g. AeroScout-class RTF ~$150–200) or
  build-from-foamboard (Flite Test plans — cheap, crash-repairable with hot glue).
- **Autonomy**: ArduPlane on a Matek/Pixhawk FC turns any stable foam plane into a
  waypoint aircraft; add airspeed sensor for reliable auto-landing. Fixed wing is the
  best value platform for long-range/endurance autonomy experiments (within VLOS rules).
- Launch/land: hand-launch + belly-land on grass beats wheels for beginners.
- VTOL tailsitters/quadplanes exist (ArduPilot QuadPlane) — advanced, wonderful, budget 2×.

## Helicopters (collective pitch)

Honest guidance: CP helis are the **hardest RC discipline** — more mechanics, more tuning,
less crash-survivable, smaller community than multirotors. Recommend only if the user
specifically loves helicopters.
- Path: sim (RealFlight with a heli model) → small CP heli (OMPHobby M2/M4, or micro
  fixed-pitch first) → bigger.
- Autonomy on helis exists (ArduPilot Heli) but is expert territory (governor, swash
  setup, vibration). For "autonomous rotorcraft" outcomes, a multirotor is 10× easier —
  say so.

## Rockets

Model rocketry is a legitimate, well-organized hobby with an outstanding safety record —
**when done inside the club/safety-code system.** Scope of what this skill helps with:

**In scope**: low/mid-power kits (Estes class A–G), scratch-built airframes, barometric
altimeters and flight computers (Eggtimer, PerfectFlite, DIY ESP32 logger), dual
deployment, GPS tracking of the airframe, thrust-vector-control *stabilization* projects
in the BPS.space hobby tradition (keeping a rocket vertical with commercial hobby motors),
high-power certification pathway via NAR/Tripoli/AMRS at sanctioned launches.

**Out of scope — decline and explain**: propellant manufacture beyond commercial motors,
metal airframes/warhead-adjacent anything, active guidance toward a target or waypoint
(that's a missile capability, regulated as such), altitude/airspace violations, launching
outside safety-code conditions. TVC that *stabilizes vertical ascent* is hobby-legal;
software that *steers a rocket to a destination* is not something to help build.

Beginner path: Estes starter kit (~$40, includes pad+controller) → B/C motors → add an
altimeter → clubs and bigger motors with mentorship. Electronics projects that teach a
ton: log baro+IMU at 100 Hz, detect apogee, fire dual-deploy charges (commercial flight
computer as primary, DIY as logger until proven).

## Air + companion computer + AI

- The autopilot flies; the companion (Pi/Jetson) sees and suggests (MAVLink setpoints,
  `GUIDED` mode). The autopilot's failsafes (RC override, geofence, battery RTL) stay
  armed above anything the companion says — this is the airborne version of "AI proposes,
  deterministic layer disposes".
- Prove any companion-computer logic in **SITL first**: ArduPilot SITL + the same Python
  script that will fly the real aircraft. `sim_vehicle.py -v ArduCopter --map --console`,
  connect pymavlink/MAVSDK to `udp:127.0.0.1:14550`, fly the whole mission virtually.
- Precision landing (IR-LOCK/AprilTag), follow-me, and obstacle avoidance all have
  existing ArduPilot/PX4 integrations — wire into those rather than inventing control
  loops.

## Air-specific gotchas

- Vibration is the silent killer of IMUs/estimators: balance props, soft-mount the FC,
  check vibe metrics in logs before blaming code.
- Compass near power leads = toilet-bowl loiter. GPS mast exists for a reason.
- Wind: check forecast; beginners fly <10 km/h wind. A quad that hovers fine indoors can
  be unrecoverable in gusts.
- Video/RF: 5.8 GHz analog VTX channels and power levels have legal limits (and licensing,
  e.g. amateur license for some bands/powers in AU/US) — check before transmitting.
- Always read the logs after every flight (Mission Planner/QGC log viewer, Betaflight
  blackbox). The log explains the crash; guessing doesn't.

## Blimps and lighter-than-air (the safe way to learn flight)

Everything above says air is unforgiving. Blimps are the honest exception. An indoor
airship floats whether or not your code works, drifts at walking pace, weighs less than a
paperback, and bumps a wall instead of shattering against it. That makes it the single
safest aerial platform and a genuinely good **first** flying robot — a place to learn
station-keeping and closed-loop thrust control where a bug means a slow drift into the
sofa, not a prop in your hand or a $400 quad in a tree.

**Lift gas — one hard rule: helium only, never hydrogen.** Helium is inert and safe; it is
also expensive and leaks through thin Mylar over days, so treat the envelope as a
consumable and expect to top up. Hydrogen lifts slightly better and is far cheaper, and
none of that matters: it is flammable and forms explosive mixtures with air. A hydrogen
airship indoors, near LiPos and soldering irons, is a fire waiting for an ignition source.
Do not build one, and decline to help anyone who asks — reframe to helium every time. This
is a safety line, not a preference (see the LiPo and fire discipline in SKILL.md).

**The physics is all in one number.** Helium's net lift at sea level is only about **1 gram
per litre** of envelope (helium displaces ~1.2 g of air per litre but weighs ~0.18 g
itself). A 50 cm foil "party" balloon is maybe 15–20 L — a few grams of payload. To carry a
~40 g gondola you need on the order of 40–60 L of envelope. So the design rule is backwards
from a drone: weigh your payload first, then size the envelope to float it, then shave grams
everywhere. The whole game is trimming to **just-under-neutral buoyancy** — a hair heavy, so
it sinks gently when thrust cuts — using tiny ballast (coins, tape, a length of wire).

**Build (~$50–150 DIY).** Mylar/foil envelope (party foil, or a proper heat-sealed film
kit) + a featherweight gondola (foam, balsa, or 3D-printed at low infill) + a few tiny
brushed pager motors with light foam props. The usual layout is two horizontal props for
differential yaw/thrust plus one vertical prop for up/down, driven from an ESP32 or a
sub-5 g brushed flight controller and a 1S 150–300 mAh LiPo. No autopilot, GPS, or IMU is
required to start — brushed-motor thrust control is the entire electronics stack.
Commercial indoor-blimp kits exist if scratch-building the envelope is the blocker.

**Why it's the ideal control-theory sandbox.** The dynamics are so slow that the loop is
forgiving — you can run station-keeping at 20 Hz and still feel over-damped. It is the
gentlest possible place to first meet a PID loop: hold an altitude with the vertical prop,
watch the integral term fight residual buoyancy, learn what Kd actually does, all at
one-tenth of a metre per second (see control-and-stability.md). Bonus: indoor blimp
**swarms** are a research favourite precisely because the platform is so safe to fly many of
at once (see swarm-and-multi-robot.md), and flying indoors sidesteps the entire drone
regulatory burden — no registration, no Remote ID, no altitude limits (the rules earlier in
this file are for the outdoor multirotor world, not your living room).

**Honest take.** It is slow, payload is measured in grams, and helium is a recurring cost
that quietly leaks away. You will not do aerial photography or outdoor missions with it. But
as the lowest-risk way to feel flight control work before you commit to a multirotor, a
blimp earns its place — prove the loop where the worst outcome is a soft bump.