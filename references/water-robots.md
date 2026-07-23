# Water robots: surface boats, ROVs, and AUVs

Water builds are 50% robotics, 50% plumbing. The electronics are the same as ground/air;
the craft is in keeping water out and getting signals through it.

## Pick the class first

| Class | Difficulty | Budget floor | Notes |
|---|---|---|---|
| **Surface vessel (ASV/boat)** | ≈ ground robot + waterproofing | ~$200 | GPS + radio work normally. **Start here** |
| **Tethered ROV** | Hard | ~$500 DIY, $4.5k+ BlueROV2 | No GPS/radio underwater → tether for control + video |
| **AUV (untethered sub)** | Very hard | $1k+ | Dead-reckoning nav (DVL costs $$$); advanced users only |

## Surface boats (the recommended entry)

- **Hull**: modify an RC boat, a boogie board/kayak-foam catamaran (very stable, huge
  payload), or 3D-print + epoxy. Catamaran > monohull for sensor platforms.
- **Propulsion**: two fixed thrusters/props, differential steering — no rudder needed, and
  the code is identical to a differential-drive rover. Cheap: brushed "underwater
  thrusters" (~$20–40). Real: Blue Robotics T200 (~$200 each).
- **Brains**: ArduPilot **Rover in boat mode** on a Pixhawk/Matek board = GPS waypoint
  missions, loiter, RTL out of the box; Pi companion optional for cameras/AI.
- **Waterproofing tiers**: electronics in a food container with cable glands (pond-grade) →
  IP67 box + proper cable glands (lake-grade) → sealed tube + penetrators (real).
- **Radio**: 2.4 GHz RC works at surface level; telemetry via 915 MHz (AU: 915–928 MHz
  ISM) or 4G. Range over water is excellent (flat, no obstacles).
- **Safety**: positive buoyancy always (foam!), bright colors, tether/retrieval line for
  early tests, never test where you can't retrieve it, and a "dead-man" failsafe: comms
  loss → motors idle + hold position (or head home).

## ROVs (underwater)

Physics you cannot argue with:
- **Radio and GPS do not work underwater.** Control + video go down a **tether**
  (Fathom-style neutrally buoyant Ethernet, or cheap Cat5 for pool builds).
- **Pressure**: ~1 atm extra per 10 m depth. Enclosures must be rated; flat lids bow and
  leak — cylinders and domes win. Blue Robotics watertight enclosures + penetrators are
  the hobby standard; DIY = PVC pipe + epoxy potting (test to depth with weights and
  paper towels inside, no electronics, for an hour, before ANY electronics dive).
- **Buoyancy**: trim to slightly positive (dead ROV floats home). Foam up top, ballast
  below → self-righting.
- **The proven stack (BlueROV architecture)**: Pixhawk running **ArduSub** + Pi companion
  streaming camera over the tether + surface laptop running QGroundControl with a
  gamepad. DIY this stack with T200-clone thrusters ≈ $600–1,000.
- **Thrusters**: 6-DOF needs 6–8; a starter ROV flies fine with 4 (2 forward/turn,
  2 vertical). Brushless + ESC potted or flooded-design (water-cooled by design — never
  run "wet" thrusters dry for more than seconds).
- **Corrosion**: rinse EVERYTHING in fresh water after salt use; sacrificial anodes on
  metal parts; marine grease on threads; stainless ≠ immune.

## Sensors underwater

- **Depth**: pressure sensor (Bar30). Essential, cheap, accurate.
- **Heading**: compass/IMU only (no GPS) — calibrate away from thruster magnets; expect
  drift.
- **Sonar**: Ping1D altimeter (~$300) for height-off-bottom; Ping360 (~$2k) for imaging.
- **Camera**: any camera behind a dome port; add LED lights below ~5 m or in murk
  (Lumen lights or potted COB LEDs).
- **Position underwater** (hard problem): tether + surface GPS, USBL beacons ($$$), or
  dead reckoning (drifts). Be honest: hobby AUV navigation is approximate at best.

## Water-specific electrical rules

- Fuse the battery. A shorted LiPo inside a sealed tube is a pressure vessel experiment.
- Leak probes (sponge/pin sensors, ~$30) wired to an alarm/auto-surface behavior.
- Connectors: WetLink/cobalt-style penetrators or potted cables. "IP68" marketing
  connectors are for splashes, not submersion cycles.
- Isolate the tether electrically (Ethernet magnetics help); galvanic + electrical noise
  issues are real in salt water.
- Salt water is conductive: a single drop on the PCB while powered can be fatal to the
  board — silicone conformal coat the electronics as cheap insurance.

## Software notes

- ArduSub/ArduPilot gives depth hold, heading hold, stabilize modes — don't hand-roll.
- Vision underwater: green/turbid water kills contrast and range; lights + close range +
  simple models (color/marker tracking) beat fancy models here. White-balance correction
  (underwater images are blue/green shifted) markedly improves detector performance —
  fine-tune on underwater imagery if the mission is serious (see ai-ml.md).
- Simulate first: ArduSub SITL exists; practice missions in the sim and in a pool before
  open water.
