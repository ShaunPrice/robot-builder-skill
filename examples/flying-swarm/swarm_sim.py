#!/usr/bin/env python3
"""
Low-cost ESP32 micro-quad SWARM simulator (for the Robot Builder tutorial).

Real per-drone physics (2nd-order, thrust/accel limited) + a centralized
formation controller that mimics the ESP-NOW-mesh "centralized coordinator"
pattern from the robot-builder swarm module:
  - one virtual coordinator assigns each drone a slot in a formation
  - each drone steers to its slot (cohesion) while keeping clear of neighbours
    (separation) — the boids rules the swarm file describes
  - a scripted mission: arm -> take off -> form a V -> orbit a waypoint in a
    ring -> regroup -> land

Outputs (headless, no display needed):
  swarm_flight.mp4     3D animated coordinated flight with trails
  swarm_topdown.mp4    top-down formation view
  swarm_telemetry.png  min inter-drone distance + formation error over time
  swarm_metrics.json   summary numbers for the video / write-up

Run:  python swarm_sim.py [N]      (N drones, default 5)
Deps: numpy, matplotlib, imageio, imageio-ffmpeg
"""
import json
import math
import sys

import numpy as np

N = int(sys.argv[1]) if len(sys.argv) > 1 else 5
DT = 0.05                # 20 Hz control loop (what a tiny ESP32 quad can hold)
G = 9.81
MAX_ACC = 5.0           # m/s^2 lateral accel a light quad can pull (cohesion budget)
SEP_ACC = 9.0           # m/s^2 emergency-avoidance budget on TOP of cohesion
MAX_V = 3.0             # m/s cruise
SEP_R = 1.0             # m: push apart inside this radius (< slot spacing)
SEP_GAIN = 26.0
SLOT_GAIN = 2.4         # pull toward assigned formation slot
DAMP = 2.0             # velocity damping (air drag + control)
rng = np.random.default_rng(7)

# ---- formation slot generators (body frame offsets around the leader) -------
# Slot spacing is kept > SEP_R so drones holding formation don't fight their own
# separation field; separation only fires when they get closer than a slot pitch.
def v_formation(n):
    slots = [np.array([0.0, 0.0, 0.0])]
    for i in range(1, n):
        side = 1 if i % 2 else -1
        rank = (i + 1) // 2
        slots.append(np.array([-1.5 * rank, side * 1.5 * rank, 0.0]))
    return np.array(slots[:n])

def ring_formation(n, radius=3.0):
    return np.array([[radius * math.cos(2 * math.pi * i / n),
                      radius * math.sin(2 * math.pi * i / n), 0.0] for i in range(n)])

# ---- scripted leader mission (the "coordinator" path) -----------------------
def leader_target(t):
    """Returns leader position + which formation to hold at time t."""
    if t < 4:                                   # vertical takeoff to 6 m
        return np.array([0, 0, min(6.0, 1.5 * t)]), "v", 1.0
    if t < 12:                                  # cruise out in a V
        return np.array([1.2 * (t - 4), 0, 6.0]), "v", 1.0
    if t < 30:                                  # orbit a waypoint as a ring
        a = (t - 12) * 0.5
        c = np.array([11.0, 0.0, 6.0])
        return c + np.array([3.0 * math.cos(a), 3.0 * math.sin(a), 0.6 * math.sin(a * 2)]), "ring", 1.0
    if t < 40:                                  # regroup + return in a V
        f = (t - 30) / 10
        return np.array([11.0 * (1 - f), 0, 6.0 - 0.0], ), "v", 1.0
    # descend and land
    return np.array([0, 0, max(0.0, 6.0 - 1.4 * (t - 40))]), "v", 0.0


def simulate(T=48.0):
    steps = int(T / DT)
    pos = np.zeros((N, 3))
    pos[:, 0] = np.linspace(-0.45 * (N - 1), 0.45 * (N - 1), N)   # 0.9 m ground spacing
    pos[:, 1] = rng.uniform(-0.2, 0.2, N)
    vel = np.zeros((N, 3))

    # per-drone altitude lane: guarantees >=0.6 m vertical clearance while cruising
    # so crossing xy paths during formation changes can never be a 3-D collision.
    # The lane collapses toward 0 as the leader descends, so they still land on
    # their distinct V-formation spots at ground level.
    base_layer = (np.arange(N) - (N - 1) / 2.0) * 0.6

    P = np.zeros((steps, N, 3))
    min_sep = np.zeros(steps)
    form_err = np.zeros(steps)
    lead = np.zeros((steps, 3))

    for k in range(steps):
        t = k * DT
        lpos, form, armed = leader_target(t)
        slots = v_formation(N) if form == "v" else ring_formation(N)
        # heading of the formation = leader velocity direction (rotate slots)
        heading = math.atan2(lpos[1] - lead[k - 1][1] if k else 0.0,
                             (lpos[0] - lead[k - 1][0]) if k else 1.0)
        ch, sh = math.cos(heading), math.sin(heading)
        R = np.array([[ch, -sh, 0], [sh, ch, 0], [0, 0, 1]])
        goals = lpos + slots @ R.T
        goals[:, 2] += base_layer * min(1.0, max(0.0, lpos[2] / 6.0))  # altitude lanes

        # cohesion: steer each drone toward its assigned slot, then damp.
        # This is the "get into formation" budget and is clamped to MAX_ACC.
        coh = SLOT_GAIN * (goals - pos) - DAMP * vel
        cn = np.linalg.norm(coh, axis=1, keepdims=True)
        coh = np.where(cn > MAX_ACC, coh / cn * MAX_ACC, coh)

        # separation: emergency collision-avoidance, added ON TOP of cohesion so
        # a near-miss always out-authorities the pull toward the slot.
        sep = np.zeros((N, 3))
        for i in range(N):
            d = pos[i] - pos
            dist = np.linalg.norm(d, axis=1)
            for j in range(N):
                if j != i and 1e-3 < dist[j] < SEP_R:
                    sep[i] += SEP_GAIN * (d[j] / dist[j]) * (SEP_R - dist[j]) / SEP_R
        sn = np.maximum(np.linalg.norm(sep, axis=1, keepdims=True), 1e-9)
        sep = np.where(sn > SEP_ACC, sep / sn * SEP_ACC, sep)

        acc = coh + sep
        acc[:, 2] += (0.0 if armed else -2.0)    # cut lift when disarmed -> sink

        vel += acc * DT
        vn = np.linalg.norm(vel, axis=1, keepdims=True)
        vel = np.where(vn > MAX_V, vel / vn * MAX_V, vel)
        pos = pos + vel * DT
        pos[:, 2] = np.maximum(pos[:, 2], 0.0)   # don't go underground

        P[k] = pos
        lead[k] = lpos
        # metrics
        dm = np.inf
        for i in range(N):
            for j in range(i + 1, N):
                dm = min(dm, np.linalg.norm(pos[i] - pos[j]))
        min_sep[k] = dm
        form_err[k] = np.mean(np.linalg.norm(pos - goals, axis=1))

    return P, lead, min_sep, form_err, steps


def render(P, lead, min_sep, form_err, steps):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D  # noqa
    import imageio.v2 as imageio

    colors = plt.cm.turbo(np.linspace(0.1, 0.95, N))
    stride = 2                                   # render every 2nd step (~10 fps look)
    fps = int(round(1 / (DT * stride)))

    # ---- 3D flight ----
    w3 = imageio.get_writer("swarm_flight.mp4", fps=fps, macro_block_size=8)
    for k in range(0, steps, stride):
        fig = plt.figure(figsize=(9.6, 5.4), dpi=140)
        ax = fig.add_subplot(111, projection="3d")
        ax.set_facecolor("#0b0e14"); fig.patch.set_facecolor("#0b0e14")
        for i in range(N):
            tr = P[max(0, k - 40):k + 1, i]
            ax.plot(tr[:, 0], tr[:, 1], tr[:, 2], color=colors[i], lw=1.2, alpha=0.6)
            ax.scatter(*P[k, i], color=colors[i], s=42, depthshade=True)
        ax.scatter(*lead[k], color="w", marker="x", s=30)
        ax.set_xlim(-3, 15); ax.set_ylim(-6, 6); ax.set_zlim(0, 8)
        ax.set_box_aspect((18, 12, 8))
        for a in (ax.xaxis, ax.yaxis, ax.zaxis):
            a.pane.set_facecolor("#0b0e14"); a.pane.set_edgecolor("#243040")
        ax.tick_params(colors="#5b6b7d", labelsize=7)
        ax.set_title(f"ESP32 micro-quad swarm  |  N={N}  t={k*DT:4.1f}s",
                     color="#cfe8ff", fontsize=11)
        ax.view_init(elev=22, azim=-60 + k * 0.15)
        fig.tight_layout()
        fig.canvas.draw()
        buf = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
        buf = buf.reshape(fig.canvas.get_width_height()[::-1] + (4,))[:, :, :3]
        w3.append_data(buf)
        plt.close(fig)
    w3.close()

    # ---- top-down ----
    wt = imageio.get_writer("swarm_topdown.mp4", fps=fps, macro_block_size=8)
    for k in range(0, steps, stride):
        fig, ax = plt.subplots(figsize=(6.4, 6.4), dpi=140)
        ax.set_facecolor("#0b0e14"); fig.patch.set_facecolor("#0b0e14")
        for i in range(N):
            tr = P[max(0, k - 60):k + 1, i]
            ax.plot(tr[:, 0], tr[:, 1], color=colors[i], lw=1.0, alpha=0.5)
            ax.scatter(P[k, i, 0], P[k, i, 1], color=colors[i], s=60)
        ax.set_xlim(-3, 15); ax.set_ylim(-7, 7); ax.set_aspect("equal")
        ax.set_title(f"top-down  t={k*DT:4.1f}s", color="#cfe8ff")
        ax.tick_params(colors="#5b6b7d"); ax.grid(color="#182230")
        fig.tight_layout(); fig.canvas.draw()
        buf = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
        buf = buf.reshape(fig.canvas.get_width_height()[::-1] + (4,))[:, :, :3]
        wt.append_data(buf); plt.close(fig)
    wt.close()

    # ---- telemetry ----
    t = np.arange(steps) * DT
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 5), dpi=140, sharex=True)
    fig.patch.set_facecolor("#0b0e14")
    for a in (a1, a2):
        a.set_facecolor("#0b0e14"); a.tick_params(colors="#8aa"); a.grid(color="#182230")
        for s in a.spines.values(): s.set_color("#243040")
    a1.plot(t, min_sep, color="#00c8ff"); a1.axhline(0.5, color="#ff5555", ls="--", lw=1)
    a1.set_ylabel("min sep (m)", color="#cfe8ff"); a1.set_ylim(0, None)
    a1.set_title("Swarm safety + coordination telemetry", color="#cfe8ff")
    a2.plot(t, form_err, color="#7CFC00"); a2.set_ylabel("mean formation err (m)", color="#cfe8ff")
    a2.set_xlabel("time (s)", color="#cfe8ff")
    fig.tight_layout(); fig.savefig("swarm_telemetry.png"); plt.close(fig)

    return fps, float(min_sep[10:].min()), float(form_err[-60:].mean())


if __name__ == "__main__":
    P, lead, min_sep, form_err, steps = simulate()
    fps, worst_sep, settle_err = render(P, lead, min_sep, form_err, steps)
    metrics = {
        "drones": N, "control_hz": int(1 / DT), "sim_seconds": round(steps * DT, 1),
        "fps": fps, "min_separation_m": round(worst_sep, 2),
        "no_collisions": bool(worst_sep > 0.5),
        "settled_formation_error_m": round(settle_err, 2),
        "mission": "arm -> takeoff -> V-formation cruise -> ring orbit -> regroup -> land",
    }
    json.dump(metrics, open("swarm_metrics.json", "w"), indent=2)
    print(json.dumps(metrics, indent=2))
