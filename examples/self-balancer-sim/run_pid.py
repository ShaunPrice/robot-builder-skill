"""Balance the virtual robot with the cascaded PID from control-and-stability.md.

Inner loop: pitch angle -> wheel torque (fast, does the balancing).
Outer loop: forward velocity -> pitch setpoint (slow, stops it drifting away).

At t = 4 s the robot gets shoved (external force on the chassis) to show
disturbance recovery. Outputs: pid_run.png (telemetry) and pid_balancer.gif.
"""

import numpy as np
import imageio.v2 as imageio
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mujoco

from balancer_env import BalancerEnv, MAX_TORQUE, CONTROL_HZ

DT = 1.0 / CONTROL_HZ
DURATION_S = 8.0
PUSH_AT_S = 4.0

# Inner (angle) gains — tuned the way the skill teaches: Kp to brisk, then Kd, tiny Ki.
KP, KI, KD = 4.0, 8.0, 0.15
I_CLAMP = 0.5 * MAX_TORQUE            # anti-windup
# Outer (velocity -> lean) gain: lean gently against drift.
KV, LEAN_CLAMP = 0.06, 0.12           # rad of allowed corrective lean


def main():
    env = BalancerEnv()
    obs, _ = env.reset(seed=3)
    gif = imageio.get_writer("pid_balancer.gif", fps=25, loop=0)

    integral = 0.0
    log = {k: [] for k in ("t", "pitch", "vel", "torque", "setpoint")}

    steps = int(DURATION_S * CONTROL_HZ)
    for i in range(steps):
        pitch, pitch_rate, _wheel_vel, fwd_vel = obs

        # Outer loop: velocity error -> pitch setpoint (lean toward where it drifts from).
        pitch_sp = float(np.clip(-KV * fwd_vel, -LEAN_CLAMP, LEAN_CLAMP))

        # Inner loop: PID on pitch error.
        err = pitch_sp - pitch
        integral = float(np.clip(integral + err * DT, -I_CLAMP / max(KI, 1e-9),
                                 I_CLAMP / max(KI, 1e-9)))
        torque = KP * err + KI * integral + KD * (0.0 - pitch_rate)
        action = np.array([np.clip(-torque / MAX_TORQUE, -1.0, 1.0)], dtype=np.float32)

        # The shove: 6 N backwards on the chassis for 100 ms.
        body = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_BODY, "chassis")
        if PUSH_AT_S <= i * DT < PUSH_AT_S + 0.1:
            env.data.xfrc_applied[body, 0] = -6.0
        else:
            env.data.xfrc_applied[body, 0] = 0.0

        obs, _r, terminated, _tr, _ = env.step(action)
        log["t"].append(i * DT)
        log["pitch"].append(np.degrees(pitch))
        log["vel"].append(fwd_vel)
        log["torque"].append(float(action[0]) * MAX_TORQUE)
        log["setpoint"].append(np.degrees(pitch_sp))
        if i % 4 == 0:                       # 25 fps GIF
            gif.append_data(env.render())
        if terminated:
            print(f"FELL at t={i*DT:.2f}s — gains need work")
            break
    gif.close()
    env.close()

    fig, axes = plt.subplots(3, 1, figsize=(9, 7), sharex=True)
    axes[0].plot(log["t"], log["pitch"], label="pitch")
    axes[0].plot(log["t"], log["setpoint"], "--", label="setpoint", alpha=0.7)
    axes[0].axvspan(PUSH_AT_S, PUSH_AT_S + 0.1, color="red", alpha=0.2, label="shove (6 N)")
    axes[0].set_ylabel("pitch (deg)"), axes[0].legend(loc="upper right")
    axes[1].plot(log["t"], log["vel"], color="tab:green")
    axes[1].axvspan(PUSH_AT_S, PUSH_AT_S + 0.1, color="red", alpha=0.2)
    axes[1].set_ylabel("fwd vel (m/s)")
    axes[2].plot(log["t"], log["torque"], color="tab:orange")
    axes[2].axvspan(PUSH_AT_S, PUSH_AT_S + 0.1, color="red", alpha=0.2)
    axes[2].set_ylabel("torque (N·m)"), axes[2].set_xlabel("time (s)")
    fig.suptitle(f"Cascaded PID balancer — Kp={KP} Ki={KI} Kd={KD}, outer Kv={KV}")
    fig.tight_layout()
    fig.savefig("pid_run.png", dpi=110)

    survived = len(log["t"]) == steps
    final_pitch = abs(log["pitch"][-1])
    print(f"survived={survived}  steps={len(log['t'])}/{steps}  "
          f"final |pitch|={final_pitch:.2f} deg  "
          f"max |pitch| after shove={max(abs(p) for t, p in zip(log['t'], log['pitch']) if t >= PUSH_AT_S):.1f} deg")


if __name__ == "__main__":
    main()
