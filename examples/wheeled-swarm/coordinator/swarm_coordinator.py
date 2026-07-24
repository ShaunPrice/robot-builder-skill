#!/usr/bin/env python3
"""
swarm_coordinator.py — laptop coordinator for the wheeled fiducial swarm.

Reads an OVERHEAD CAMERA, detects the ArUco tag on each robot to get its
(x, y, heading), runs the same formation controller as wheeled_swarm_sim.py, and
streams a velocity setpoint per robot to the coordinator_bridge over USB serial:

    id,armed,v,omega\\n

The camera closes the position loop; each robot just executes (v, omega). Mission:
scatter -> triangle -> translate -> rotate -> line -> park.

  --sim              integrate a kinematic model and PRINT setpoints (no hardware)
  --camera 0         overhead-camera index (default 0)
  --port PORT        serial port to the bridge (e.g. /dev/tty.usbserial-XXX)
  --marker-mm 60     printed marker size (must match make_tags.py)
  --ids 0,1,2        ArUco ids in robot order
  --show             draw the camera view with detections

Deps: numpy; for hardware also opencv-contrib-python + pyserial.
⚠️  Reference code — bench-test wheels-up first.
"""
import argparse, math, sys, time
import numpy as np

CTRL_HZ = 20.0
V_MAX, W_MAX = 0.35, 2.5
K_RHO, K_ALPHA, K_BETA, K_FINAL = 1.1, 3.0, -0.9, 1.5
SAFE_DIST, BRAKE0, YIELD = 0.30, 0.16, 0.20
POS_TOL = 0.02
ARENA = (2.6, 1.9)


def wrap(a): return (a + math.pi) % (2 * math.pi) - math.pi
def clamp(x, lo, hi): return lo if x < lo else (hi if x > hi else x)


def triangle(side=0.5):
    r = side / math.sqrt(3)
    return np.array([[r * math.cos(math.radians(90 + 120 * i)),
                      r * math.sin(math.radians(90 + 120 * i))] for i in range(3)])


def line(n, gap=0.42):
    return np.array([[gap * (i - (n - 1) / 2.0), 0.0] for i in range(n)])


def phase_id(t):
    return 0 if t < 8 else 1 if t < 16 else 2 if t < 24 else 3 if t < 32 else 4


def formation_at(t, n):
    cx, cy = ARENA[0] * 0.40, ARENA[1] * 0.5
    if t < 8:  return np.array([cx, cy]), math.radians(90), triangle()
    if t < 16: return np.array([cx + 0.7 * (t - 8) / 8, cy]), math.radians(90), triangle()
    if t < 24: return np.array([cx + 0.7, cy]), math.radians(90 + 180 * (t - 16) / 8), triangle()
    if t < 32:
        f = (t - 24) / 8
        a = np.array([cx + 0.7, cy]); b = np.array([cx - 0.05, cy + 0.32])
        return a + f * (b - a), math.radians(0), line(n)
    return np.array([cx - 0.05, cy + 0.32]), math.radians(0), line(n)


def slots(t, n):
    c, th, offs = formation_at(t, n)
    R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    return c + offs @ R.T, th


def nearest_assign(pos, pts):
    import itertools
    return list(min(itertools.permutations(range(len(pts))),
                    key=lambda p: sum(np.linalg.norm(pos[i] - pts[p[i]]) for i in range(len(pts)))))


def goto(est, tgt):
    dx, dy = tgt[0] - est[0], tgt[1] - est[1]
    rho = math.hypot(dx, dy)
    if rho < POS_TOL:
        return 0.0, clamp(K_FINAL * wrap(tgt[2] - est[2]), -W_MAX, W_MAX)
    alpha = wrap(math.atan2(dy, dx) - est[2]); beta = wrap(tgt[2] - math.atan2(dy, dx))
    return clamp(K_RHO * rho * math.cos(alpha), -V_MAX, V_MAX), \
        clamp(K_ALPHA * alpha + K_BETA * beta, -W_MAX, W_MAX)


# ---------------- overhead-camera ArUco pose ----------------
def make_detector():
    import cv2, cv2.aruco as aruco
    d = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
    return cv2.aruco.ArucoDetector(d, aruco.DetectorParameters())


def detect_poses(frame, detector, marker_mm, cv2):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = detector.detectMarkers(gray)
    poses = {}
    if ids is None:
        return poses
    sides = [(np.linalg.norm(c[0][1] - c[0][0]) + np.linalg.norm(c[0][2] - c[0][3])) / 2 for c in corners]
    mpp = (marker_mm / 1000.0) / (np.mean(sides))          # global metres-per-pixel this frame
    for c, i in zip(corners, ids.ravel()):
        pts = c[0]
        cen = pts.mean(axis=0)
        ex = pts[1] - pts[0]                                # marker top edge = local +x
        poses[int(i)] = (cen[0] * mpp, -cen[1] * mpp, math.atan2(-ex[1], ex[0]))
    return poses


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sim", action="store_true")
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--port", default=None)
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--marker-mm", type=float, default=60.0)
    ap.add_argument("--ids", default="0,1,2")
    ap.add_argument("--duration", type=float, default=38.0)
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    ids = [int(x) for x in a.ids.split(",")]
    n = len(ids)
    dt = 1.0 / CTRL_HZ

    ser = None
    cap = None
    detector = None
    cv2 = None
    if not a.sim:
        import cv2 as _cv2; cv2 = _cv2
        detector = make_detector()
        cap = cv2.VideoCapture(a.camera)
        if not cap.isOpened():
            sys.exit(f"cannot open camera {a.camera}")
        if a.port:
            import serial; ser = serial.Serial(a.port, a.baud, timeout=0); time.sleep(2)

    # sim state (also the fallback pose when a robot is briefly unseen)
    pose = np.array([[0.30, 0.35, 0.6], [0.35, 1.55, -0.5], [0.55, 0.95, 0.1],
                     [0.20, 0.75, 0.3], [0.45, 1.25, -0.8]])[:n].astype(float)

    slot0, _ = slots(0.0, n)
    assign = nearest_assign(pose[:, :2], slot0)
    prev_ph, t = 0, 0.0
    print(f"# coordinator: {n} robots ids={ids}, {'SIM' if a.sim else 'camera %d' % a.camera}, {CTRL_HZ:.0f} Hz")
    try:
        while t <= a.duration:
            ph = phase_id(t)
            if ph != prev_ph:
                pts_new, _ = slots(t, n)
                assign = nearest_assign(pose[:, :2], pts_new)
                prev_ph = ph

            if not a.sim:                                   # read real poses from the camera
                ok, frame = cap.read()
                if ok:
                    seen = detect_poses(frame, detector, a.marker_mm, cv2)
                    for r, mid in enumerate(ids):
                        if mid in seen:
                            pose[r] = seen[mid]
                    if a.show:
                        cv2.imshow("swarm", frame)
                        if cv2.waitKey(1) == 27:
                            break

            pts, th = slots(t, n)
            for r in range(n):
                tgt = np.array([pts[assign[r]][0], pts[assign[r]][1], th])
                v, w = goto(pose[r], tgt)
                line_out = f"{ids[r]},1,{v:.3f},{w:.3f}"
                if ser: ser.write((line_out + "\n").encode())
                if a.sim:                                   # integrate a unicycle model as feedback
                    pose[r, 0] += v * math.cos(pose[r, 2]) * dt
                    pose[r, 1] += v * math.sin(pose[r, 2]) * dt
                    pose[r, 2] = wrap(pose[r, 2] + w * dt)
                    if abs(t - round(t)) < dt / 2 and r == 0:
                        print(f"t={t:4.1f}s r0 -> v={v:+.2f} w={w:+.2f}  pose=({pose[0,0]:.2f},{pose[0,1]:.2f})")
            time.sleep(0 if a.sim else dt)
            t += dt
    finally:
        if ser:
            for mid in ids: ser.write(f"{mid},0,0,0\n".encode())   # disarm all
            ser.close()
        if cap: cap.release()
    print("# done")


if __name__ == "__main__":
    main()
