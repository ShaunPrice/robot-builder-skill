#!/usr/bin/env python3
"""
Generate printable ArUco fiducial tags for the swarm robots (one per robot).

Prints ArUco 4x4_50 markers id=0..N-1 with a white quiet-zone border and a label.
Print at 100% scale, cut out, and stick one flat on top of each robot (into the
chassis recess). The overhead camera + coordinator/swarm_coordinator.py read these
to get each robot's (x, y, heading). Keep MARKER_MM consistent with what you tell
the coordinator so pose scale is correct.

    pip install opencv-contrib-python
    python make_tags.py [N]        # -> aruco_id0.png ..  (default N=3)
"""
import sys
import cv2
import numpy as np
import cv2.aruco as aruco

N = int(sys.argv[1]) if len(sys.argv) > 1 else 3
DICT = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
PX = 800          # marker render size (px)
BORDER = 130      # white quiet zone (px) — ArUco needs a clear border to detect
MARKER_MM = 60    # printed marker size; tell the coordinator this number


def draw_marker(d, i, px):
    if hasattr(aruco, "generateImageMarker"):
        return aruco.generateImageMarker(d, i, px)      # OpenCV >= 4.7
    return aruco.drawMarker(d, i, px)                    # older OpenCV


for i in range(N):
    m = draw_marker(DICT, i, PX)
    canvas = np.full((PX + 2 * BORDER, PX + 2 * BORDER), 255, np.uint8)
    canvas[BORDER:BORDER + PX, BORDER:BORDER + PX] = m
    cv2.putText(canvas, f"ArUco 4x4_50  id={i}  ({MARKER_MM} mm)",
                (BORDER, BORDER - 45), cv2.FONT_HERSHEY_SIMPLEX, 1.1, 0, 3, cv2.LINE_AA)
    cv2.rectangle(canvas, (BORDER - 2, BORDER - 2), (BORDER + PX + 2, BORDER + PX + 2), 0, 1)
    cv2.imwrite(f"aruco_id{i}.png", canvas)
    print(f"aruco_id{i}.png written")
print(f"Print at 100% scale so each marker is ~{MARKER_MM} mm; stick id=k on robot k.")
