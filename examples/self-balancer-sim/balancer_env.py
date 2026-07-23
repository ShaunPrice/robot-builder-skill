"""Gymnasium environment for the two-wheel self-balancing robot (MuJoCo).

This is the pattern from references/simulation-and-gyms.md: wrap your own robot
model in the Gymnasium API so PID code, RL training, and (later) the real robot
all speak the same interface.

Observation (what a real balancer can actually measure — no oracle state):
    [pitch (rad), pitch_rate (rad/s), mean wheel velocity (rad/s), forward velocity (m/s)]
Action:
    [torque] in [-1, 1], scaled to the motor limit, applied to BOTH wheels
    (balance is a 1-DOF problem; steering would add a second action).
"""

from __future__ import annotations

import os

import mujoco
import numpy as np
import gymnasium as gym
from gymnasium import spaces

MODEL_PATH = os.path.join(os.path.dirname(__file__), "balancer.xml")

MAX_TORQUE = 0.35          # must match ctrlrange in balancer.xml
CONTROL_HZ = 100           # real builds run 100-500 Hz (control-and-stability.md)
FALL_ANGLE = 0.7           # rad (~40 deg): beyond this it has fallen — cut motors


class BalancerEnv(gym.Env):
    metadata = {"render_modes": ["rgb_array"], "render_fps": CONTROL_HZ}

    def __init__(self, render_mode: str | None = None, domain_randomization: bool = False):
        self.model = mujoco.MjModel.from_xml_path(MODEL_PATH)
        self.data = mujoco.MjData(self.model)
        self.frame_skip = int(round(1.0 / (CONTROL_HZ * self.model.opt.timestep)))
        self.render_mode = render_mode
        self.domain_randomization = domain_randomization
        self._renderer = None
        self._base_body_mass = self.model.body_mass.copy()

        high = np.array([np.pi, 50.0, 200.0, 10.0], dtype=np.float32)
        self.observation_space = spaces.Box(-high, high, dtype=np.float32)
        self.action_space = spaces.Box(-1.0, 1.0, shape=(1,), dtype=np.float32)

    # -- physics helpers ---------------------------------------------------
    def _pitch(self) -> float:
        """Pitch about the axle (y) axis from the root quaternion."""
        w, x, y, z = self.data.qpos[3:7]
        # sin(pitch) for y-axis rotation; asin keeps sign correct near upright
        return float(np.arcsin(np.clip(2.0 * (w * y - z * x), -1.0, 1.0)))

    def _obs(self) -> np.ndarray:
        pitch = self._pitch()
        pitch_rate = float(self.data.qvel[4])            # angular vel about y
        wheel_vel = float(0.5 * (self.data.qvel[6] + self.data.qvel[7]))
        fwd_vel = float(self.data.qvel[0])
        return np.array([pitch, pitch_rate, wheel_vel, fwd_vel], dtype=np.float32)

    # -- gym API -----------------------------------------------------------
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)

        if self.domain_randomization:
            # Randomize mass (+/-20%) and floor friction — the sim2real habit.
            scale = self.np_random.uniform(0.8, 1.2, size=self._base_body_mass.shape)
            self.model.body_mass[:] = self._base_body_mass * scale
            self.model.geom_friction[0, 0] = self.np_random.uniform(0.6, 1.4)

        # Start with a random lean, like being stood up by an imperfect hand.
        tilt = self.np_random.uniform(-0.15, 0.15)       # +/- ~8.5 deg
        self.data.qpos[3:7] = [np.cos(tilt / 2), 0.0, np.sin(tilt / 2), 0.0]
        mujoco.mj_forward(self.model, self.data)
        return self._obs(), {}

    def step(self, action):
        torque = float(np.clip(action[0], -1.0, 1.0)) * MAX_TORQUE
        self.data.ctrl[:] = [torque, torque]
        for _ in range(self.frame_skip):
            mujoco.mj_step(self.model, self.data)

        obs = self._obs()
        pitch, pitch_rate, wheel_vel, fwd_vel = obs
        fallen = bool(abs(pitch) > FALL_ANGLE)

        # Reward: stay upright, stay put, don't thrash.
        reward = (
            1.0                                  # alive bonus
            - 2.0 * pitch**2                     # upright
            - 0.05 * pitch_rate**2               # smooth
            - 0.1 * fwd_vel**2                   # don't run away
            - 0.01 * (torque / MAX_TORQUE) ** 2  # effort
        )
        if fallen:
            reward = -10.0
        return obs, float(reward), fallen, False, {}

    def render(self):
        if self._renderer is None:
            self._renderer = mujoco.Renderer(self.model, height=480, width=640)
        self._renderer.update_scene(self.data)
        return self._renderer.render()

    def close(self):
        if self._renderer is not None:
            self._renderer.close()
            self._renderer = None
