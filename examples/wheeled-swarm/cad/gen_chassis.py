#!/usr/bin/env python3
"""
Parametric 3D-printable chassis for the differential-drive swarm robot.

A flat base plate (prints with no supports): rear mounting holes + axle slots for
two TT gear motors, a front ball-caster hole pattern, a deck hole grid for the
ESP32 / motor driver / battery holder, a front slot for the VL53L0X distance
sensor, and a shallow top recess to seat the printed ArUco fiducial flat so the
overhead camera sees it cleanly.

    pip install trimesh manifold3d numpy
    python gen_chassis.py            # -> chassis.stl

Units are millimetres. Tune the PARAMS block for your motors / caster / board.
"""
import numpy as np
import trimesh
from trimesh.creation import box, cylinder
from trimesh.transformations import rotation_matrix, translation_matrix

# ---------------- PARAMS (mm) ----------------
BASE = (120.0, 90.0, 3.0)      # length (x) x width (y) x thickness
M3 = 3.3                        # M3 clearance hole
CASTER_PITCH = 20.0             # front ball-caster screw square
MOTOR_X = -38.0                 # rear motor line (x)
MOTOR_HOLE_DX, MOTOR_HOLE_DY = 18.0, 10.0   # per-motor mounting-hole rectangle
AXLE_SLOT = (10.0, 5.0)         # axle clearance slot at each side edge (x,y)
DECK = [(x, y) for x in (-12, 12) for y in (-18, 0, 18)]   # ESP32/driver/battery deck grid
TOF_SLOT = (14.0, 5.0)          # front distance-sensor slot (x through-cut)
FID = (52.0, 1.0)              # fiducial recess: square side, depth
SECT = 48
PLA = 1.24e-3                   # g/mm^3


def at(m, x=0, y=0, z=0, rx=0):
    m = m.copy()
    if rx:
        m.apply_transform(rotation_matrix(np.radians(rx), [1, 0, 0]))
    m.apply_transform(translation_matrix([x, y, z]))
    return m


def hole(x, y, d, depth=BASE[2] + 2):
    return at(cylinder(radius=d / 2, height=depth, sections=SECT), x, y, BASE[2] / 2)


base = at(box(extents=BASE), z=BASE[2] / 2)
holes = []

# front ball-caster screw pattern (front = +x)
cx = BASE[0] / 2 - 14
for sx in (-1, 1):
    for sy in (-1, 1):
        holes.append(hole(cx + sx * CASTER_PITCH / 2, sy * CASTER_PITCH / 2, M3))

# two TT-motor mounting-hole rectangles at the rear sides + axle clearance slots
for side in (+1, -1):
    yc = side * (BASE[1] / 2 - 16)
    for sx in (-1, 1):
        for sy in (-1, 1):
            holes.append(hole(MOTOR_X + sx * MOTOR_HOLE_DX / 2, yc + sy * MOTOR_HOLE_DY / 2, M3))
    # axle clearance slot cut into the side edge at the motor line
    holes.append(at(box(extents=[AXLE_SLOT[0], AXLE_SLOT[1] + 4, BASE[2] + 2]),
                    MOTOR_X, side * (BASE[1] / 2 - AXLE_SLOT[1] / 2 + 1), BASE[2] / 2))

# electronics deck hole grid
for (x, y) in DECK:
    holes.append(hole(x, y, M3))

# front distance-sensor slot (through the front edge)
holes.append(at(box(extents=[TOF_SLOT[0] + 2, TOF_SLOT[1], BASE[2] + 2]),
                BASE[0] / 2 - TOF_SLOT[0] / 2, 0, BASE[2] / 2))

# shallow top recess for the ArUco fiducial (seats the printed/stuck tag flat)
recess = at(box(extents=[FID[0], FID[0], FID[1] + 0.2]), 6, 0, BASE[2] - FID[1] / 2 + 0.1)

cut = trimesh.boolean.union(holes + [recess], engine="manifold")
chassis = trimesh.boolean.difference([base, cut], engine="manifold")
chassis.merge_vertices()
chassis.export("chassis.stl")

bb = chassis.bounds
print("chassis.stl written")
print(f"  watertight : {chassis.is_watertight}")
print(f"  triangles  : {len(chassis.faces)}")
print(f"  bbox (mm)  : {bb[1][0]-bb[0][0]:.0f} x {bb[1][1]-bb[0][1]:.0f} x {bb[1][2]-bb[0][2]:.0f}")
print(f"  solid mass : {chassis.volume*PLA:.1f} g PLA @100% (~{chassis.volume*PLA*0.4:.1f} g at ~40% infill)")
