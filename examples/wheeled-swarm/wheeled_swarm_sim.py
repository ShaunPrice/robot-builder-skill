#!/usr/bin/env python3
"""
Wheeled robot SWARM simulator — 3 differential-drive robots localised by an
OVERHEAD CAMERA reading ArUco fiducials on each robot. This is the achievable
indoor relative-localisation the drone swarm lacked: the tags on the robots ARE
the positioning system. Each robot also carries a distance sensor for local,
camera-independent collision avoidance.

Per robot: unicycle kinematics + an Astolfi go-to-pose controller. Between camera
frames each robot dead-reckons on odometry (with drift); every camera frame its
pose estimate is corrected toward the fiducial measurement (with realistic noise).
A centralized coordinator assigns formation targets and runs the mission:
  scatter -> gather into a triangle -> translate -> rotate in place -> reform as a
  line -> park.

Outputs (headless, no display needed):
  wheeled_topdown.mp4    top-down coordinated driving: robots, headings, trails,
                         formation targets, and the camera field of view
  wheeled_telemetry.png  formation error | min inter-robot distance | localisation error
  wheeled_metrics.json   summary numbers

Run:  python wheeled_swarm_sim.py [N]      (N robots, default 3)
Deps: numpy, matplotlib, imageio, imageio-ffmpeg
"""
import itertools
import json
import math
import sys

import numpy as np

N = int(sys.argv[1]) if len(sys.argv) > 1 else 3
DT = 0.05                    # 20 Hz control loop
CAM_HZ = 15.0                # overhead-camera / fiducial detection rate
CAM_EVERY = max(1, round((1.0 / DT) / CAM_HZ))
V_MAX = 0.35                 # m/s  (small geared wheeled robot)
W_MAX = 2.5                  # rad/s
ROBOT_R = 0.06               # m (chassis radius)
SAFE_DIST = 0.30             # m centre-to-centre: distance sensor slows the robot inside this
BRAKE0 = 0.16                # m: braked fully to a stop at this gap
YIELD = 0.20                 # m: the lower-id robot yields (stops) inside this gap
POS_TOL = 0.02               # m
K_RHO, K_ALPHA, K_BETA, K_FINAL = 1.1, 3.0, -0.9, 1.5   # go-to-pose gains
CAM_NOISE_XY = 0.004         # m   (fiducial position noise, ~4 mm)
CAM_NOISE_TH = math.radians(1.0)   # rad (fiducial heading noise, ~1 deg)
ODO_DRIFT = 0.04             # odometry multiplicative drift (fraction of motion)
ARENA = (2.6, 1.9)           # m — the overhead camera's field of view
rng = np.random.default_rng(3)


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def clamp(x, lo, hi):
    return lo if x < lo else (hi if x > hi else x)


def triangle(side=0.5):
    r = side / math.sqrt(3)
    return np.array([[r * math.cos(math.radians(90 + 120 * i)),
                      r * math.sin(math.radians(90 + 120 * i))] for i in range(3)])


def line(gap=0.42):
    return np.array([[gap * (i - (N - 1) / 2.0), 0.0] for i in range(N)])


def formation_at(t):
    """(centre[x,y], heading, body-frame offsets) for the mission at time t."""
    cx, cy = ARENA[0] * 0.40, ARENA[1] * 0.5
    if t < 8:                                    # gather into a triangle
        return np.array([cx, cy]), math.radians(90), triangle()
    if t < 16:                                   # translate the triangle right
        return np.array([cx + 0.7 * (t - 8) / 8, cy]), math.radians(90), triangle()
    if t < 24:                                   # rotate the triangle in place
        return np.array([cx + 0.7, cy]), math.radians(90 + 180 * (t - 16) / 8), triangle()
    if t < 32:                                   # reform as a line, up and left
        f = (t - 24) / 8
        a = np.array([cx + 0.7, cy]); b = np.array([cx - 0.05, cy + 0.32])
        return a + f * (b - a), math.radians(0), line()
    return np.array([cx - 0.05, cy + 0.32]), math.radians(0), line()   # park


def phase_id(t):
    return 0 if t < 8 else 1 if t < 16 else 2 if t < 24 else 3 if t < 32 else 4


def nearest_assign(pos, pts):
    return list(min(itertools.permutations(range(len(pts))),
                    key=lambda p: sum(np.linalg.norm(pos[i] - pts[p[i]]) for i in range(len(pts)))))


def slots(t):
    c, th, offs = formation_at(t)
    R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    return c + offs @ R.T, th


def targets(t, assign):
    pts, th = slots(t)
    out = np.zeros((N, 3))
    for i in range(N):
        out[i, :2] = pts[assign[i]]; out[i, 2] = th
    return out


def goto(est, tgt):
    """Astolfi unicycle go-to-pose -> (v, omega)."""
    dx, dy = tgt[0] - est[0], tgt[1] - est[1]
    rho = math.hypot(dx, dy)
    if rho < POS_TOL:
        return 0.0, clamp(K_FINAL * wrap(tgt[2] - est[2]), -W_MAX, W_MAX)
    alpha = wrap(math.atan2(dy, dx) - est[2])
    beta = wrap(tgt[2] - math.atan2(dy, dx))
    v = K_RHO * rho * math.cos(alpha)
    w = K_ALPHA * alpha + K_BETA * beta
    return clamp(v, -V_MAX, V_MAX), clamp(w, -W_MAX, W_MAX)


def simulate(T=38.0):
    steps = int(T / DT)
    true = np.zeros((N, 3))                      # ground-truth pose [x,y,theta]
    # scattered start poses across the arena
    starts = np.array([[0.30, 0.35, 0.6], [0.35, 1.55, -0.5], [0.55, 0.95, 0.1],
                       [0.20, 0.75, 0.3], [0.45, 1.25, -0.8]])
    true[:] = starts[:N]
    est = true.copy() + rng.normal(0, CAM_NOISE_XY, (N, 3))   # first camera fix

    # assign each robot to its nearest slot; re-assign when the formation type changes
    slot0, _ = slots(0.0)
    assign = nearest_assign(true[:, :2], slot0)
    prev_ph = 0

    P = np.zeros((steps, N, 3))
    Pest = np.zeros((steps, N, 3))
    Ptgt = np.zeros((steps, N, 3))
    min_sep = np.zeros(steps)
    form_err = np.zeros(steps)
    loc_err = np.zeros(steps)

    for k in range(steps):
        t = k * DT
        ph = phase_id(t)
        if ph != prev_ph:                       # reconfigure: re-assign to nearest new slots
            pts_new, _ = slots(t)
            assign = nearest_assign(true[:, :2], pts_new)
            prev_ph = ph
        tgt = targets(t, assign)
        vw = np.zeros((N, 2))
        for i in range(N):
            v, w = goto(est[i], tgt[i])
            # distance-sensor avoidance — only when actually CLOSING on a neighbour (it lies
            # toward this robot's goal). Brake, veer away, and let the lower-id robot yield.
            # Gating on "closing" is what stops a robot freezing next to a neighbour it is
            # trying to drive away from.
            d = true[:, :2] - true[i, :2]                    # robot -> each neighbour
            dist = np.linalg.norm(d, axis=1)
            dist[i] = np.inf
            j = int(np.argmin(dist))
            to_goal = tgt[i, :2] - true[i, :2]
            if dist[j] < SAFE_DIST and float(d[j] @ to_goal) > 0.0:
                v *= clamp((dist[j] - BRAKE0) / (SAFE_DIST - BRAKE0), 0.0, 1.0)   # brake to 0 at BRAKE0
                bearing = wrap(math.atan2(d[j, 1], d[j, 0]) - true[i, 2])
                w = clamp(w - 1.2 * math.copysign(1.0, bearing), -W_MAX, W_MAX)   # veer away
                if dist[j] < YIELD and i < j:
                    v = 0.0                                                       # lower-id yields
            vw[i] = (v, w)

        # integrate true state (unicycle) + propagate odometry estimate
        for i in range(N):
            v, w = vw[i]
            true[i, 0] += v * math.cos(true[i, 2]) * DT
            true[i, 1] += v * math.sin(true[i, 2]) * DT
            true[i, 2] = wrap(true[i, 2] + w * DT)
            # odometry: what the robot *thinks* it did, with drift
            dv = v * (1 + rng.normal(0, ODO_DRIFT))
            dw = w * (1 + rng.normal(0, ODO_DRIFT))
            est[i, 0] += dv * math.cos(est[i, 2]) * DT
            est[i, 1] += dv * math.sin(est[i, 2]) * DT
            est[i, 2] = wrap(est[i, 2] + dw * DT)

        # overhead camera / fiducial correction every CAM_EVERY steps
        if k % CAM_EVERY == 0:
            meas = true + rng.normal(0, 1.0, (N, 3)) * np.array([CAM_NOISE_XY, CAM_NOISE_XY, CAM_NOISE_TH])
            est[:, :2] = 0.15 * est[:, :2] + 0.85 * meas[:, :2]      # fuse toward the fiducial
            est[:, 2] = meas[:, 2]

        P[k] = true; Pest[k] = est; Ptgt[k] = tgt
        dm = np.inf
        for i in range(N):
            for j in range(i + 1, N):
                dm = min(dm, np.linalg.norm(true[i, :2] - true[j, :2]))
        min_sep[k] = dm
        form_err[k] = np.mean(np.linalg.norm(true[:, :2] - tgt[:, :2], axis=1))
        loc_err[k] = np.mean(np.linalg.norm(true[:, :2] - est[:, :2], axis=1))

    return P, Pest, Ptgt, min_sep, form_err, loc_err, steps


def render(P, Pest, Ptgt, min_sep, form_err, loc_err, steps):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import imageio.v2 as imageio

    colors = plt.cm.turbo(np.linspace(0.15, 0.9, N))
    stride = 2
    fps = int(round(1 / (DT * stride)))

    def robot_patch(ax, x, y, th, c):
        # body + heading wedge + fiducial square on top
        ax.add_patch(plt.Circle((x, y), ROBOT_R, color=c, zorder=3))
        ax.plot([x, x + ROBOT_R * 1.6 * math.cos(th)], [y, y + ROBOT_R * 1.6 * math.sin(th)],
                color="w", lw=1.6, zorder=4)
        s = ROBOT_R * 0.7
        ax.add_patch(plt.Rectangle((x - s / 2, y - s / 2), s, s, color="w", alpha=0.85, zorder=5))
        ax.add_patch(plt.Rectangle((x - s / 2, y - s / 2), s, s, fill=False, ec="k", lw=0.6, zorder=6))

    w = imageio.get_writer("wheeled_topdown.mp4", fps=fps, macro_block_size=8)
    for k in range(0, steps, stride):
        fig, ax = plt.subplots(figsize=(9.6, 7.0), dpi=120)
        fig.patch.set_facecolor("#0b0e14"); ax.set_facecolor("#0e131c")
        # camera FOV / arena
        ax.add_patch(plt.Rectangle((0, 0), ARENA[0], ARENA[1], fill=False, ec="#2a3850", lw=1.5, ls="--"))
        ax.text(0.03, ARENA[1] - 0.08, "overhead camera field of view", color="#48607e", fontsize=9)
        for i in range(N):
            tr = P[max(0, k - 80):k + 1, i]
            ax.plot(tr[:, 0], tr[:, 1], color=colors[i], lw=1.2, alpha=0.5, zorder=2)
            tx, ty, tth = Ptgt[k, i]
            ax.add_patch(plt.Circle((tx, ty), ROBOT_R, fill=False, ec=colors[i], lw=1.0, ls=":", alpha=0.8))
            robot_patch(ax, P[k, i, 0], P[k, i, 1], P[k, i, 2], colors[i])
        ax.set_xlim(-0.1, ARENA[0] + 0.1); ax.set_ylim(-0.1, ARENA[1] + 0.1)
        ax.set_aspect("equal")
        ax.set_title(f"Wheeled swarm (fiducial + overhead camera)   N={N}   t={k*DT:4.1f}s",
                     color="#cfe8ff", fontsize=12)
        ax.tick_params(colors="#3d5068", labelsize=7)
        for sp in ax.spines.values(): sp.set_color("#243040")
        fig.tight_layout(); fig.canvas.draw()
        buf = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
        buf = buf.reshape(fig.canvas.get_width_height()[::-1] + (4,))[:, :, :3]
        w.append_data(buf); plt.close(fig)
    w.close()

    t = np.arange(steps) * DT
    fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(9, 6.5), dpi=130, sharex=True)
    fig.patch.set_facecolor("#0b0e14")
    for a in (a1, a2, a3):
        a.set_facecolor("#0b0e14"); a.tick_params(colors="#8aa"); a.grid(color="#182230")
        for s in a.spines.values(): s.set_color("#243040")
    a1.plot(t, form_err * 100, color="#7CFC00"); a1.set_ylabel("formation\nerr (cm)", color="#cfe8ff")
    a1.set_title("Wheeled swarm — coordination + localisation telemetry", color="#cfe8ff")
    a2.plot(t, min_sep * 100, color="#00c8ff"); a2.axhline(2 * ROBOT_R * 100, color="#ff5555", ls="--", lw=1)
    a2.set_ylabel("min sep\n(cm)", color="#cfe8ff"); a2.set_ylim(0, None)
    a3.plot(t, loc_err * 1000, color="#ffb454")
    a3.set_ylabel("localisation\nerr (mm)", color="#cfe8ff"); a3.set_xlabel("time (s)", color="#cfe8ff")
    fig.tight_layout(); fig.savefig("wheeled_telemetry.png"); plt.close(fig)

    return fps, float(min_sep[20:].min()), float(form_err[-40:].mean()), float(loc_err[20:].mean())


if __name__ == "__main__":
    P, Pest, Ptgt, ms, fe, le, steps = simulate()
    fps, worst_sep, settle_err, loc = render(P, Pest, Ptgt, ms, fe, le, steps)
    metrics = {
        "robots": N, "control_hz": int(1 / DT), "camera_hz": int(CAM_HZ),
        "sim_seconds": round(steps * DT, 1), "fps": fps,
        "min_separation_cm": round(worst_sep * 100, 1),
        "no_collisions": bool(worst_sep > 2 * ROBOT_R),
        "settled_formation_error_cm": round(settle_err * 100, 1),
        "mean_localisation_error_mm": round(loc * 1000, 1),
        "localisation": "overhead camera + ArUco fiducials, odometry between frames",
        "mission": "scatter -> gather (triangle) -> translate -> rotate -> line -> park",
    }
    json.dump(metrics, open("wheeled_metrics.json", "w"), indent=2)
    print(json.dumps(metrics, indent=2))
