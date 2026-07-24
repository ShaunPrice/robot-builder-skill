# Design and 3D: see it before you build it

This is the DESIGN rung — it sits *before* Scope & shop and the bench (SKILL.md's build
ladder), and it is the cheapest place on the whole project to be wrong. Sensor blind spots,
the arm that fouls the lidar, a battery that pushes the center of gravity behind the rear
axle, "the Pi doesn't actually fit under the top plate" — every one of those is a five-minute
edit on screen and a returned-parts saga after it arrives. Draft the robot, look at it from
every angle, *then* spend money. The self-balancer worked example already ships a MuJoCo
model rendered to video before any hardware moves; this module generalizes that "model
first" habit to every build.

Be honest about what this rung is and is not. The browser drafter answers **layout and
communication** questions (does the camera see over the arm, where is the CoG, will it fit).
It is not mechanical CAD — it will not give you a printable bracket with real tolerances.
Those are two different jobs and this file keeps them separate on purpose.

## Browser drafting: zero install, live 3D

The fastest way to start is to ask Claude to generate an **interactive 3D robot-drafter as
a self-contained web artifact** (Three.js on a canvas, no server, no account). You open it in
a browser and tweak the robot live:

- Chassis length/width/height and ground clearance.
- Drive type — differential/tank, Ackermann (car-style), mecanum, or a boat hull.
- Wheel count and placement; where the sensors and battery sit.
- Arm on/off, and where it mounts.

The preview is a fully orbitable 3D scene with two things a static sketch can't give you:

- A **center-of-gravity marker** that moves as you drag the battery, Jetson, or arm around —
  the single most useful thing to watch on a rover (tippiness) or a boat (trim). Pair with
  the CG discussion in control-and-stability.md and, for aircraft, the "CG is 90% of it"
  rule in the same file.
- **Field-of-view cones** for cameras and lidar so you can *see* the blind spots — the wedge
  a depth camera can't reach under the front bumper, the arm's shadow across the lidar's
  360°, the gap a single forward camera leaves behind the robot. Match the FoV and range
  numbers to real parts from sensors.md (a RealSense D435's ~87° H-FoV, a 2D lidar's planar
  sweep) so the cones mean something.

Good for: catching interference and coverage problems, and communicating the build to
someone else before parts are ordered. Not good for: anything load-bearing, dimensioned, or
printable.

## The URDF bridge (the idea that makes this rung pay off)

Here is why the drafter is not throwaway work. The drafted layout **exports a URDF** — the
same Unified Robot Description Format file that describes your robot to the rest of the
stack. That one file is the spine of everything downstream:

```
browser drafter → URDF → Gazebo sim → RViz → Nav2 on the real robot
   (layout)              (crash for free)   (visualize)   (autonomy)
```

- Gazebo turns your URDF into the *simulated* robot (see simulation-and-gyms.md — the digital
  twin section walks the whole URDF-to-sim flow: add inertials, attach the diff-drive and
  sensor plugins, bridge topics).
- RViz and Nav2 read the same URDF for TF frames and collision geometry (see ros.md).

So design → 3D preview → simulate → real robot is **one artifact chain**, not four separate
efforts. Get the link lengths, joint origins, and sensor mount frames right in the drafter
once, and every later rung inherits them. This is also the honest boundary of the browser
tool: it produces a *layout* URDF (link shapes, frames, sensor poses, rough masses). You add
accurate inertia tensors and collision meshes when you take it into Gazebo — the drafter gets
you a valid, well-framed skeleton, not a physics-perfect model.

## Heavy 3D belongs on a connected service, not the browser

Photoreal renders, physics-accurate meshes, and large multi-part assemblies will melt a
browser canvas. When you need them, connect Claude to a **render/CAD server over Docker-MCP**
rather than trying to do it in the artifact — a Blender render server is the natural fit, and
Claude can drive it (build the scene, render, read back the image) the same conversational way
it drives Gazebo. See the Docker-MCP section of docker-and-environments.md for the connection
pattern and its cautions, and hardware-requirements.md for what a render/GPU box actually
needs (a real GPU; photoreal rendering is as VRAM-hungry as the Isaac runs in
simulation-and-gyms.md). Rule of thumb: layout and FoV in the browser; anything that needs a
GPU or looks like a photo goes to the service.

## When you need REAL mechanical CAD (out of scope here — go to these)

The moment the question becomes "print me this motor bracket with 0.2 mm clearance and an M3
bolt pattern," you have left the drafter's job and entered fabrication CAD. The drafter does
not do tolerances, threads, fillets, or watertight STLs for printing — point the builder at a
proper tool:

| Tool | Runs where | Best for | Cost |
|---|---|---|---|
| **Onshape** | Browser (cloud) | The best in-browser parametric CAD; brackets, assemblies, exports STL/STEP | Free hobbyist plan (public docs) |
| **Tinkercad** | Browser | Absolute beginners; drag-and-drop solids for a first printed part | Free |
| **FreeCAD** | Desktop (Win/Mac/Linux) | Open-source parametric CAD; no cloud, fully offline | Free |
| **Fusion 360** | Desktop | Polished parametric CAD/CAM | Free for qualifying hobbyists |

For a hobbyist who wants to design a printable part *in the browser*, Onshape is the
recommendation — parametric, capable, and it exports the STL you hand to the slicer or the
STEP you hand to a machinist. Bring the finished mesh back into the URDF as a visual/collision
mesh so the accurate part shows up in sim and RViz.

## The honest scope, one more time

- **Browser drafter** → layout and communication. Interference, coverage, CoG. Exports a
  layout URDF.
- **URDF** → simulation. The same file drives Gazebo, RViz, Nav2 (simulation-and-gyms.md,
  ros.md).
- **Render/CAD server** → photoreal and heavy assemblies, over Docker-MCP on a GPU box
  (docker-and-environments.md, hardware-requirements.md).
- **Onshape/FreeCAD/Fusion** → real fabrication CAD: printable, dimensioned, toleranced STLs.

Draft it, look at it, sim it, then build it. The screen is where mistakes are free.
