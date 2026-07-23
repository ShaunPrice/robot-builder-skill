"""Train a PPO policy to balance the robot — the training-gym pathway from
references/simulation-and-gyms.md, end to end:

  Gymnasium env (our own robot)  ->  vectorized envs  ->  PPO (stable-baselines3)
  -> domain randomization during training (sim2real habit)
  -> evaluate on the nominal robot -> learning_curve.png, rl_run.png, rl_balancer.gif

CPU-only, ~3-6 minutes. The trained policy lands in ppo_balancer.zip.
"""

import numpy as np
import imageio.v2 as imageio
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from gymnasium.wrappers import TimeLimit
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.monitor import Monitor

from balancer_env import BalancerEnv, CONTROL_HZ

TRAIN_STEPS = 300_000
EPISODE_STEPS = 500          # 5 s episodes during training
EVAL_SECONDS = 8.0


def make_env():
    return Monitor(TimeLimit(BalancerEnv(domain_randomization=True),
                             max_episode_steps=EPISODE_STEPS))


def main():
    venv = make_vec_env(make_env, n_envs=8, seed=42)
    model = PPO("MlpPolicy", venv, seed=42, verbose=0,
                n_steps=512, batch_size=1024, learning_rate=3e-4,
                gamma=0.99, gae_lambda=0.95, ent_coef=0.001)
    model.learn(total_timesteps=TRAIN_STEPS, progress_bar=False)
    model.save("ppo_balancer")

    # Learning curve from the Monitor wrappers.
    rewards, lengths = [], []
    for e in venv.envs:
        rewards += e.get_episode_rewards()
        lengths += e.get_episode_lengths()
    order = np.argsort(np.cumsum(lengths))          # rough chronological merge
    r = np.array(rewards)[order]
    smooth = np.convolve(r, np.ones(25) / 25, mode="valid")
    plt.figure(figsize=(8, 4.5))
    plt.plot(r, alpha=0.25, label="episode reward")
    plt.plot(np.arange(len(smooth)) + 12, smooth, label="25-ep moving avg")
    plt.axhline(EPISODE_STEPS, color="gray", ls="--", lw=0.8,
                label=f"max possible ≈ {EPISODE_STEPS}")
    plt.xlabel("episode"), plt.ylabel("reward")
    plt.title(f"PPO learning curve — {TRAIN_STEPS:,} steps, domain-randomized")
    plt.legend(), plt.tight_layout()
    plt.savefig("learning_curve.png", dpi=110)
    venv.close()

    # Evaluate deterministically on the NOMINAL robot (no randomization).
    env = BalancerEnv()
    obs, _ = env.reset(seed=7)
    gif = imageio.get_writer("rl_balancer.gif", fps=25, loop=0)
    log = {"t": [], "pitch": [], "vel": [], "act": []}
    steps = int(EVAL_SECONDS * CONTROL_HZ)
    fell_at = None
    for i in range(steps):
        action, _ = model.predict(obs, deterministic=True)
        obs, _r, terminated, _tr, _ = env.step(action)
        log["t"].append(i / CONTROL_HZ)
        log["pitch"].append(np.degrees(obs[0]))
        log["vel"].append(obs[3])
        log["act"].append(float(action[0]))
        if i % 4 == 0:
            gif.append_data(env.render())
        if terminated:
            fell_at = i / CONTROL_HZ
            break
    gif.close()
    env.close()

    fig, axes = plt.subplots(3, 1, figsize=(9, 7), sharex=True)
    axes[0].plot(log["t"], log["pitch"]), axes[0].set_ylabel("pitch (deg)")
    axes[1].plot(log["t"], log["vel"], color="tab:green"), axes[1].set_ylabel("fwd vel (m/s)")
    axes[2].plot(log["t"], log["act"], color="tab:orange")
    axes[2].set_ylabel("action [-1,1]"), axes[2].set_xlabel("time (s)")
    fig.suptitle("PPO policy — deterministic eval on nominal robot")
    fig.tight_layout(), fig.savefig("rl_run.png", dpi=110)

    print(f"episodes trained: {len(rewards)}  "
          f"final avg reward (last 25): {np.mean(r[-25:]):.1f}/{EPISODE_STEPS}")
    print("eval: " + ("FELL at %.2fs" % fell_at if fell_at
          else f"survived {EVAL_SECONDS:.0f}s, mean |pitch|={np.mean(np.abs(log['pitch'])):.2f} deg"))


if __name__ == "__main__":
    main()
