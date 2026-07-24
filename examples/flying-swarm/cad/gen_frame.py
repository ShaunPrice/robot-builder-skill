#!/usr/bin/env python3
"""
Parametric 3D-printable frame for the ESP32 brushed micro-quad (X configuration).

Generates whoop_frame.stl: a 75 mm-wheelbase X frame sized for 8.5 mm coreless
motors, with a central board deck (mounting holes + lightening cutout + wire
slot), four tapered arms, and four motor-mount tubes bored for a press-fit.

Units are millimetres. Build watertight via manifold boolean ops so it slices
cleanly. Print in PLA/PETG; supports not needed if printed deck-down.

    pip install trimesh manifold3d numpy
    python gen_frame.py            # -> whoop_frame.stl

Tune the PARAMS block for a different motor size or wheelbase.
"""
import numpy as np
import trimesh
from trimesh.creation import box, cylinder
from trimesh.transformations import rotation_matrix, translation_matrix

# ---------------- PARAMS (mm) ----------------
WHEELBASE   = 75.0     # motor-to-motor, diagonally opposite motors
MOTOR_OD    = 8.5      # coreless motor diameter
BORE_OD     = 8.6      # motor-mount bore (press fit; +0.1 clearance)
TUBE_OD     = 12.0     # motor-mount outer diameter
TUBE_H      = 9.0      # motor-mount height (holds the 20 mm motor upright)
DECK        = (26.0, 26.0, 2.0)   # central board deck L x W x thickness
ARM_W       = 5.0      # arm width
ARM_H       = 3.0      # arm thickness (z)
BOARD_HOLE  = 2.2      # M2 clearance for the FC/ESP32 board
BOARD_PITCH = 20.0     # board mounting-hole square (edit to your board)
LIGHTEN_OD  = 11.0     # central lightening hole
WIRE_SLOT   = (16.0, 3.5)  # wire pass-through slot (len x width)
SECTIONS    = 64       # cylinder facet count
PLA_DENSITY = 1.24e-3  # g/mm^3 (for a mass estimate)

r = WHEELBASE / 2.0                     # motor radius from centre
angles = [45, 135, 225, 315]            # X-quad arm directions (deg)


def at(mesh, x=0, y=0, z=0, rot_deg=0):
    m = mesh.copy()
    if rot_deg:
        m.apply_transform(rotation_matrix(np.radians(rot_deg), [0, 0, 1]))
    m.apply_transform(translation_matrix([x, y, z]))
    return m


solids, holes = [], []

# central deck (sits z: 0..DECK[2])
solids.append(at(box(extents=DECK), z=DECK[2] / 2))

for a in angles:
    ca, sa = np.cos(np.radians(a)), np.sin(np.radians(a))
    # arm: a bar from the deck edge out to the motor, laid along the diagonal
    r_in, r_out = 9.0, r
    arm_len = r_out - r_in
    arm = box(extents=[arm_len, ARM_W, ARM_H])
    arm = at(arm, x=(r_in + r_out) / 2, z=ARM_H / 2)      # place along +x first
    arm.apply_transform(rotation_matrix(np.radians(a), [0, 0, 1]))
    solids.append(arm)
    # motor-mount tube at the motor position
    mx, my = r * ca, r * sa
    solids.append(at(cylinder(radius=TUBE_OD / 2, height=TUBE_H, sections=SECTIONS),
                     x=mx, y=my, z=TUBE_H / 2))
    # bore for the motor (through the tube, from the top down) + shaft clearance below
    holes.append(at(cylinder(radius=BORE_OD / 2, height=TUBE_H + 2, sections=SECTIONS),
                    x=mx, y=my, z=(TUBE_H + 2) / 2))

# board mounting holes (M2 square) + central lightening hole + wire slot
for sx in (-1, 1):
    for sy in (-1, 1):
        holes.append(at(cylinder(radius=BOARD_HOLE / 2, height=DECK[2] + 2, sections=32),
                        x=sx * BOARD_PITCH / 2, y=sy * BOARD_PITCH / 2, z=DECK[2] / 2))
holes.append(at(cylinder(radius=LIGHTEN_OD / 2, height=DECK[2] + 2, sections=SECTIONS),
                z=DECK[2] / 2))
holes.append(at(box(extents=[WIRE_SLOT[0], WIRE_SLOT[1], DECK[2] + 2]),
                x=0, y=DECK[1] / 2 - WIRE_SLOT[1] / 2 - 1.0, z=DECK[2] / 2))

solid = trimesh.boolean.union(solids, engine="manifold")
hole = trimesh.boolean.union(holes, engine="manifold")
frame = trimesh.boolean.difference([solid, hole], engine="manifold")

frame.merge_vertices()
frame.remove_degenerate_faces() if hasattr(frame, "remove_degenerate_faces") else None
frame.export("whoop_frame.stl")

vol_mm3 = frame.volume
bb = frame.bounds
print("whoop_frame.stl written")
print(f"  watertight : {frame.is_watertight}")
print(f"  triangles  : {len(frame.faces)}")
print(f"  bbox (mm)  : {bb[1][0]-bb[0][0]:.1f} x {bb[1][1]-bb[0][1]:.1f} x {bb[1][2]-bb[0][2]:.1f}")
print(f"  volume     : {vol_mm3/1000:.2f} cm^3")
print(f"  solid mass : {vol_mm3*PLA_DENSITY:.1f} g PLA @100% infill "
      f"(~{vol_mm3*PLA_DENSITY*0.5:.1f} g at ~40-50% infill)")
