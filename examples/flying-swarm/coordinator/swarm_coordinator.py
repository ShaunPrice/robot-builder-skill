#!/usr/bin/env python3
"""
swarm_coordinator.py — laptop-side swarm coordinator for the ESP32 micro-quads.

Runs the SAME centralized formation controller as ../swarm_sim.py (cohesion to a
formation slot + separation + altitude lanes, flying the mission take off -> V ->
ring orbit -> regroup -> land), turns each drone's position error into an
attitude+throttle SETPOINT, and streams one line per drone at 20 Hz to the
coordinator_bridge over USB serial:

    id,armed,throttle,pitch_sp,roll_sp,yaw_rate_sp\\n

  --dry-run     integrate a simple point-mass model and PRINT setpoints (no HW)
  --port PORT   send to the bridge over serial (e.g. /dev/tty.usbserial-XXX)

⚠️  REAL FLIGHT NEEDS POSITION FEEDBACK. In --dry-run the drone state comes from
    an internal model. On hardware you MUST replace get_state() with real
    localization (optical-flow + height, UWB anchors, or motion capture) telemetry
    — a swarm cannot hold formation open-loop. Bench-test props OFF first.

    pip install pyserial      # only needed for --port
"""
import argparse, math, sys, time
import numpy as np

# ---- controller constants (hover throttle from engineering/swarm-drone-calcs.xlsx) ----
CTRL_HZ   = 20.0
G         = 9.81
HOVER_THR = 0.42          # ~42% hover throttle for the reference build
KP_POS, KD_POS = 1.8, 2.2 # horizontal position / velocity gains -> tilt
KP_Z,  KD_Z   = 0.06, 0.04
MAX_TILT  = 20.0          # deg
SLOT_GAIN, SEP_R, SEP_GAIN, DAMP, MAX_ACC, MAX_V = 2.4, 1.0, 26.0, 2.0, 5.0, 3.0

# ---- formation geometry (identical to swarm_sim.py) ----
def v_formation(n):
    s = [np.array([0.0, 0, 0])]
    for i in range(1, n):
        side = 1 if i % 2 else -1; rank = (i + 1) // 2
        s.append(np.array([-1.5 * rank, side * 1.5 * rank, 0.0]))
    return np.array(s[:n])

def ring_formation(n, radius=3.0):
    return np.array([[radius * math.cos(2 * math.pi * i / n),
                      radius * math.sin(2 * math.pi * i / n), 0.0] for i in range(n)])

def leader_target(t):
    if t < 4:  return np.array([0, 0, min(6.0, 1.5 * t)]), "v", 1.0
    if t < 12: return np.array([1.2 * (t - 4), 0, 6.0]), "v", 1.0
    if t < 30:
        a = (t - 12) * 0.5; c = np.array([11.0, 0, 6.0])
        return c + np.array([3 * math.cos(a), 3 * math.sin(a), 0.6 * math.sin(2 * a)]), "ring", 1.0
    if t < 40: return np.array([11.0 * (1 - (t - 30) / 10), 0, 6.0]), "v", 1.0
    z = max(0.0, 6.0 - 1.4 * (t - 40))                 # stay ARMED through the descent;
    return np.array([0, 0, z]), "v", (1.0 if z > 0.05 else 0.0)   # disarm only on the ground

def formation_goals(t, n, base_layer):
    lpos, form, armed = leader_target(t)
    slots = v_formation(n) if form == "v" else ring_formation(n)
    goals = lpos + slots                       # (heading assumed +x; extend with yaw if needed)
    goals[:, 2] += base_layer * min(1.0, max(0.0, lpos[2] / 6.0))
    return goals, armed


class Model:
    """Simple point-mass drones so --dry-run is runnable end-to-end (replace with
    real localization telemetry on hardware)."""
    def __init__(self, n):
        self.pos = np.zeros((n, 3)); self.vel = np.zeros((n, 3))
        self.pos[:, 0] = np.linspace(-0.45 * (n - 1), 0.45 * (n - 1), n)
    def state(self, i): return self.pos[i].copy(), self.vel[i].copy()
    def step(self, acc, dt):
        acc = acc.copy(); acc[:, 2] -= 0.0
        self.vel += acc * dt
        vn = np.maximum(np.linalg.norm(self.vel, axis=1, keepdims=True), 1e-9)  # avoid 0/0
        self.vel = np.where(vn > MAX_V, self.vel / vn * MAX_V, self.vel)
        self.pos += self.vel * dt
        self.pos[:, 2] = np.maximum(self.pos[:, 2], 0.0)


def setpoint(goal, pos, vel):
    """position error -> (throttle, pitch_deg, roll_deg). Small-angle mapping,
    yaw assumed 0 so body == world axes."""
    a = KP_POS * (goal[:2] - pos[:2]) - KD_POS * vel[:2]        # desired horiz accel (m/s^2)
    an = np.linalg.norm(a)
    if an > MAX_ACC: a = a / an * MAX_ACC
    pitch = math.degrees(math.atan2(-a[0], G))                 # +x accel -> nose down
    roll  = math.degrees(math.atan2(a[1], G))
    pitch = max(-MAX_TILT, min(MAX_TILT, pitch))
    roll  = max(-MAX_TILT, min(MAX_TILT, roll))
    thr = HOVER_THR + KP_Z * (goal[2] - pos[2]) - KD_Z * vel[2]
    return max(0.0, min(1.0, thr)), pitch, roll


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--drones", type=int, default=5)
    ap.add_argument("--port", default=None, help="serial port to the bridge")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--duration", type=float, default=48.0)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    n = a.drones
    base_layer = (np.arange(n) - (n - 1) / 2.0) * 0.6

    ser = None
    if a.port and not a.dry_run:
        import serial                                   # pip install pyserial
        ser = serial.Serial(a.port, a.baud, timeout=0); time.sleep(2)
    if not a.port and not a.dry_run:
        sys.exit("give --port <serial> for hardware, or --dry-run to preview")

    model = Model(n)
    dt = 1.0 / CTRL_HZ
    t = 0.0
    print(f"# coordinator: {n} drones, {'DRY-RUN model' if a.dry_run else a.port}, {CTRL_HZ:.0f} Hz")
    try:
        # arming preamble: hold armed + idle throttle ~1.5 s so each drone latches its
        # arm interlock (drone.ino arms only after seeing a low-throttle packet) before takeoff.
        ta = 0.0
        while ta < 1.5:
            for i in range(n):
                if ser: ser.write(f"{i},1,0.000,0.00,0.00,0.00\n".encode())
            time.sleep(0 if a.dry_run else dt); ta += dt
        while t <= a.duration:
            goals, armed = formation_goals(t, n, base_layer)
            acc = np.zeros((n, 3))
            for i in range(n):
                pos, vel = model.state(i)               # <-- HARDWARE: real localization here
                thr, pitch, roll = setpoint(goals[i], pos, vel)
                line = f"{i},{int(armed)},{thr:.3f},{pitch:.2f},{roll:.2f},0.00"
                if ser: ser.write((line + "\n").encode())
                if a.dry_run and abs(t - round(t)) < dt / 2 and i == 0:
                    print(f"t={t:4.1f}s d0 -> thr={thr:.2f} pitch={pitch:+5.1f} roll={roll:+5.1f}  "
                          f"pos=({pos[0]:+.1f},{pos[1]:+.1f},{pos[2]:.1f}) goal_z={goals[i][2]:.1f}")
                # advance the dry-run model with the same formation controller as the sim
                d = pos - model.pos; dist = np.linalg.norm(d, axis=1)
                acc[i] += SLOT_GAIN * (goals[i] - pos) - DAMP * vel
                for j in range(n):
                    if j != i and 1e-3 < dist[j] < SEP_R:
                        acc[i] += SEP_GAIN * (d[j] / dist[j]) * (SEP_R - dist[j]) / SEP_R
            if a.dry_run:
                model.step(acc, dt)
            time.sleep(0 if a.dry_run else dt)
            t += dt
    finally:
        if ser:                                          # always disarm + close, incl. Ctrl-C
            for i in range(n): ser.write(f"{i},0,0,0,0,0\n".encode())
            ser.close()
    print("# done")


if __name__ == "__main__":
    main()
