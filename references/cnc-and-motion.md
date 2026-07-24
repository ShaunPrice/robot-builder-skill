# CNC & gantry motion: routers, lasers, plotters — precise tool positioning

The Cartesian cousin of robotics. A CNC machine shares the entire electronics family with the
rest of this skill — steppers, drivers, ESP32/Arduino motion controllers — and the same
motion concepts (acceleration, homing, open vs closed loop, the cascade of setpoints). What
differs is the *goal*: not mobility or manipulation, but precise positioning of a **tool**
for material removal, marking, or deposition. Makers cross between the two constantly — a
3D-printer motion platform and a self-balancing robot run the same MCU and the same PID
ideas (see control-and-stability.md). Read this module when the build is a machine that holds
still and moves a spindle, laser, pen, or hotwire through a workpiece.

**In scope**: hobby CNC routers, diode and CO2 laser engravers, 3D-printer motion platforms,
pen plotters/drawbots, PCB mills, hotwire foam cutters. **Out of scope** (point elsewhere):
production machining, metallurgy and tooling selection for metal, and industrial VMC
operation — those are a trade, not a weekend build. This module gets you a safe, working
hobby machine and the vocabulary to grow.

## Machine types and honest entry costs

Buy one tier below what you think you want — a rigid small machine that cuts cleanly teaches
more than a big flexible one that chatters. 2026 USD, machine only (add extraction, safety
gear, and endmills/lenses).

| Machine | Entry cost | Firmware | Cuts / marks | Notes |
|---|---|---|---|---|
| Pen plotter / drawbot | ~$50–100 | GRBL | Ink on paper | Cheapest way to learn motion control; zero cutting hazard |
| **3018 CNC router** | ~$120–300 | GRBL | Wood, plastic, PCB, *light* aluminium | The classic entry. Frame flex is its ceiling — expect it |
| Diode laser engraver | ~$150–500 | GRBL | Engrave wood/leather; cut thin ply, *dark* acrylic | Eye safety paramount; clear acrylic is transparent to blue diodes and won't cut — see below |
| Larger router (Shapeoko 5 Pro, Onefinity) | ~$1,500–3,000 | grblHAL / GRBL | Hardwood, aluminium, sign work | Rigidity you can feel; the real hobby step-up |
| DIY MPCNC / LowRider v3 | ~$300–1,500 | Marlin / FluidNC | Large-format wood, foam, light routing | Print-and-buy-tubes; big envelope, modest rigidity |
| 3D printer repurposed as motion platform | (already owned) | Marlin / Klipper | Pen, drag-knife, light engraving laser | Learn G-code and steps/mm on hardware you have |

The 3018 is to CNC what the wheeled rover is to robotics (see ground-robots.md): it fails
cheaply, iterates fast, and everything transfers upward. Start there unless you specifically
need a laser or already own a printer.

## Motion hardware — the parts that decide precision

**Steppers**: NEMA17 (42 mm, ~1.5–2 A/phase) drives almost all hobby CNC, lasers, and
printers — enough torque for the loads, cheap, universally supported. NEMA23 (57 mm,
2.5–4.5 A) is for larger routers and heavier gantries; it needs external drivers and a
higher-voltage supply. Match the motor to the axis mass and cutting force, not to ambition.

**Open vs closed loop** — this is the CNC version of the encoder question in sensors.md. A
plain **open-loop** stepper has no idea where it actually is: if it hits resistance and skips
steps, it loses position *silently* and every subsequent move is wrong, ruining the part with
no error raised. A **closed-loop** stepper (integrated encoder, ~$30–50 per axis) detects and
corrects lost steps, or faults out honestly. On a router that pushes into hardwood or
aluminium, closed-loop is worth it on at least X and Y — it converts "silent scrap" into "the
machine stopped and told you." Lasers and plotters see almost no cutting force and stay fine
open-loop.

**Drivers**:
- **A4988 / DRV8825** — basic, cheap, loud, run hot; fine for a first plotter or 3018, but
  crude microstepping and audible whine.
- **TMC2208 / TMC2209** — the quiet choice for light NEMA17 axes (plotters, lasers, 3018,
  printer-class motion): near-silent (StealthChop), cooler, and the 2209 adds **sensorless
  homing** (StallGuard) to skip limit switches on light axes. Under real cutting load run
  SpreadCycle, not StealthChop. They top out around 2 A RMS — step up to external drivers
  (DM542 and up) for NEMA23 and heavy gantries.
- **External drivers** (DM542, closed-loop servo-stepper drivers) for NEMA23 and up — the
  onboard driver chips can't pass that current.

**Mechanics** — how rotation becomes linear travel:

| Transmission | Precision | Speed | Cost | Use |
|---|---|---|---|---|
| Lead screw (Tr8/ACME) | High | Slow | Low | Z axes, small routers, PCB mills |
| Belt (GT2) | Lower (belt stretch) | Fast | Low | Lasers, plotters, large gantries |
| Ball screw | Highest | Medium | High | Rigid routers, anything cutting metal |

Guideways matter as much as the screw: **linear rails** (MGN12/HGR) are stiff and repeatable;
**V-wheels on extrusion** are cheap and self-aligning but flex and wear. Rigidity is
everything in cutting — a precise driver bolted to a flexible frame still chatters. Spend on
rails and screws before you spend on electronics.

## Firmware landscape — the flight-controller equivalent

Just as air-robots.md maps airframes to autopilots (Betaflight/ArduPilot/PX4), CNC has a
firmware family, and picking the right one up front saves a rebuild:

| Firmware | Runs on | Axes | Best for |
|---|---|---|---|
| **GRBL** | Arduino/AVR (Uno, Nano) | 3 | The hobby CNC/laser standard; config via `$` params. Rock-solid, ubiquitous |
| **FluidNC** | ESP32 | 3 (up to 6 motors, incl. ganged) | The modern ESP32 member of the GRBL family — WiFi, SD card, web UI. Extra motors are ganged/secondary axes (e.g. dual-Y), not 6 independent ones |
| **grblHAL** | 32-bit (Teensy, STM32, RP2040) | up to ~6 | 32-bit GRBL: more horsepower on faster ARM boards, plugins, tool changers, closed-loop |
| **Marlin** | AVR/32-bit | 3+ | 3D printers; usable on printer-derived CNC/plotters |
| **Klipper** | Host (Pi) + MCU | 3+ | Printers; host-side, very fast, **input shaping** to cancel ringing |
| **LinuxCNC / Mach3-4** | PC + interface board | 4+ | The serious step up — real-time PC control, closed-loop, big machines |

For a new build, **FluidNC on an ESP32** is the sweet spot: everything GRBL does plus WiFi
job sending and SD offline runs. Keep plain GRBL if you're buying a machine that ships with
it and works. LinuxCNC is where hobby ends and semi-professional begins — reach for it only
when a GRBL-class machine visibly hits its ceiling.

## G-code as the mission language

The toolchain is a pipeline, exactly analogous to how a robot mission goes intent → planner →
setpoints (see ai-ml.md):

```
CAD  →  CAM  →  G-code  →  Sender  →  Firmware  →  Steppers
(shape) (toolpaths) (moves) (streams) (executes) (moves tool)
```

- **CAD** (the shape): Fusion 360, FreeCAD, Inkscape (for 2D/laser/plotter), or the CAM tool's
  own drawing.
- **CAM** (shape → toolpaths, with feeds/speeds/depths): Fusion 360 (free personal tier),
  FreeCAD Path (fully open), Carbide Create (friendly, router-focused), **LightBurn** (the
  standard for lasers — layers, power/speed per color, camera alignment).
- **G-code**: the plain-text list of moves (`G0` rapid, `G1` feed, `M3` spindle/laser on).
  Human-readable — open it and look before you run it.
- **Sender** (streams G-code to the machine): Universal Gcode Sender (UGS), bCNC, cnc.js,
  or LightBurn for lasers. FluidNC's own web UI also sends.

**G-code is generated, and generated programs are fallible** — a bad CAM setting produces a
toolpath that plunges too deep or exits the work envelope. That is the CNC form of the
"AI/generated program proposes, a deterministic layer disposes" pattern from ai-ml.md: the
firmware's soft limits, hard limit switches, and the hardware E-stop are the layer that
disposes. Never trust a G-code file you haven't range-checked and air-cut.

## Config essentials (get these right once, per machine)

- **Steps/mm calibration**: tell the firmware how many motor steps equal 1 mm on each axis
  (`$100–$102` in GRBL). Command a 100 mm move, measure the actual travel, correct the value,
  repeat. Uncalibrated steps/mm means every dimension is subtly wrong — the CNC analog of
  un-calibrated encoder ticks-per-meter (see control-and-stability.md).
- **Homing + limit switches**: mechanical or hall switches at axis ends give the machine an
  absolute origin on startup. Set homing direction and pull-off. TMC2209 sensorless homing
  removes the switches on light axes.
- **Soft vs hard limits**: *soft limits* (`$20`) reject a move that would exit the configured
  envelope before it starts — set the machine's travel accurately and they catch bad G-code.
  *Hard limits* (`$21`) stop instantly when a physical switch trips — the backstop when soft
  limits are wrong. Enable both; they are your deterministic guardrails.
- **Work coordinate systems (G54–G59)**: machine coordinates are fixed to home; the **work
  coordinate system** sets where *your stock* sits. Zero G54 to the corner/top of the
  material — this is where most first cuts go wrong (cutting air, or into the table).
- **Feeds & speeds**: feed rate (mm/min) and spindle RPM matched to material and tool. Too
  slow burns/melts, too fast breaks the cutter. Start from the tool maker's chart and a
  conservative depth-of-cut; a lighter cut on a flexy hobby frame beats a deep one that
  chatters.
- **Acceleration & jerk** (`$120–$122`): how hard axes ramp. Too high skips steps on
  open-loop machines and rings the frame; too low is sluggish. Same tradeoff as accel limits
  in the fast loop (see control-and-stability.md).

## Safety — this is genuinely dangerous, and these are hard rules

A CNC machine moves a cutting or burning tool through material under program control with
no situational awareness. Treat it with the seriousness this skill gives to spinning props
and LiPo packs. An **E-stop wired to cut power to spindle/laser and motors — not through
software — must be within reach before the first job runs.** A frozen sender or a bad line of
G-code will not stop the machine; your hand on the E-stop will.

**Routers and spindles**:
- Eye protection always — thrown chips and broken endmills become projectiles. A snapped
  carbide cutter leaves at speed.
- **No gloves, no loose clothing, no dangling hair or lanyards near rotation** — a spinning
  tool or leadscrew that catches fabric pulls your hand in faster than you can react. This is
  the rule people break and lose fingers over.
- Secure workholding (clamps, tape+glue, vise). Stock that lifts or spins ("throws") is a
  leading router injury.
- Never reach toward a spinning tool to clear chips or check the cut — pause the program and
  let it stop first.

**Lasers** (diode and CO2 — treat with extra respect):
- **Instant, permanent eye damage.** For a **diode** laser, wear tinted goggles rated for its
  exact wavelength (455 nm diode goggles do nothing against a 10.6 µm CO2 beam, and vice
  versa). A **CO2** (10.6 µm) beam is blocked by ordinary glass/polycarbonate — the machine's
  enclosure and viewing window *are* the eye protection, so the rule there is to never defeat
  or open the enclosure while it fires. Never look at any beam or its reflection off metal,
  glass, or foil.
- **Fire risk — never run a laser unattended.** Laser fires are a leading makerspace incident;
  the beam can ignite the workpiece and a 5-minute "quick job" becomes a house fire. Stay
  with it, keep a fire extinguisher within reach.
- **Fumes — extraction is mandatory.** And a categorical rule: **never cut PVC or vinyl** —
  it releases chlorine gas that harms you and corrodes the machine. Never cut unknown
  plastics; if you can't identify it, don't burn it.

**Dust**: wood, MDF, and composite dust is both a respiratory hazard and, in fine
concentrations, an *explosion* hazard. Run dust extraction and wear a respirator — a shop vac
plus a proper mask, not a paper dust mask.

**Electrical**: steppers and spindles draw real current. Fuse the supply, use a supply sized
to the machine, and keep a master switch. Same discipline as robot power architecture (see
ground-robots.md § Power) — brownouts and shorts are electrical bugs, not software bugs.

**The deterministic-safety parallel — prove it before it can hurt you.** This is the CNC
version of props-off, wheels-off-the-ground, and SITL-before-flight:
1. **Air-cut first.** Run every new program with the tool raised well above the material (or
   the laser at minimum/zero power) and watch the whole path. Confirm it stays in the
   envelope, zeros where you expect, and never plunges wrong.
2. Trust soft + hard limits and homing to catch what your eyes miss.
3. Only then set the real Z zero and cut. Stage it: simulate/preview in CAM → air-cut →
   scrap material → real stock, with the E-stop in reach at every stage.

## Relationship to the rest of the skill

A CNC machine is a robot whose "autonomy" is a G-code program running behind hard motion
limits. It shares the stepper/driver/ESP32 electronics of compute-platforms.md, the
acceleration and open-vs-closed-loop control ideas of control-and-stability.md and
sensors.md, the calibrate-then-trust discipline this whole skill preaches, and above all the
ethos of **prove it before it can hurt you**. Where a rover teleops with wheels off the
ground and a drone flies first in SITL, a CNC air-cuts above the work — same principle, same
reason. The generated toolpath proposes; homing, soft limits, and a hardware E-stop dispose.
Build those guardrails before the first chip flies, and cutting becomes low-stakes iteration
instead of a hazard.
