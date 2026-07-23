# YouTube listing — Robot-Builder-intro-v1.mp4

## Title (pick one, all under 100 chars)

1. **Robot Builder — an AI mentor that takes you from first motor to machine learning**  ← recommended
2. I gave Claude a robotics skill — it designed and trained a robot in simulation
3. This Claude skill teaches you to build robots (and proved it in a physics sim)

## Description

```
What if your AI could walk you through building a robot — from the first parts list to
machine learning?

Robot Builder is a skill for Claude that turns it into a personal robotics mentor. It
covers parts selection matched to your budget, SD-card flashing, RC and gamepad
controllers, Raspberry Pi and NVIDIA Jetson builds, depth sensors and lidar, ROS 2, PID
control, simulators and RL training gyms, security, and putting AI safely on real robots
— across ground, water, and air.

To prove it works, the skill designed the robot in this video by following its own
playbook: a two-wheel self-balancing robot modeled in MuJoCo, balanced first with a
classic cascaded PID controller, then by a neural network trained with reinforcement
learning (PPO, 300,000 steps, domain-randomized) in a Gymnasium training environment —
about five minutes on an ordinary laptop.

Everything in this video — the code, the simulation, the trained policy, and the skill
itself — is in the repo:
▶ https://github.com/ShaunPrice/robot-builder-skill

CHAPTERS
0:00 Meet Robot Builder
0:17 The 9-rung build ladder
0:29 Cascaded PID balancing (MuJoCo physics)
0:40 Reinforcement learning in a training gym
0:51 Safety by architecture
1:02 Get started

Narration: ElevenLabs · Art: gpt-image-2 · Pipeline: Claude Code + ffmpeg

#robotics #ai #claudeai #reinforcementlearning #mujoco #simulation #maker
```

## Tags (comma-separated, fits the 500-char limit)

robotics, robot building, AI robotics, Claude, Claude Code, AI agent, self balancing
robot, inverted pendulum, PID control, PID tuning, reinforcement learning, PPO, MuJoCo,
Gymnasium, stable baselines3, robot simulation, sim2real, ROS2, Raspberry Pi robot,
NVIDIA Jetson, hobby robotics, maker, DIY robot, machine learning, physics simulation

## Upload settings

- **Category**: Science & Technology
- **Thumbnail**: use `assets/header.png` (already 16:9-ish at 1792×1024; YouTube wants
  ≥1280×720, under 2 MB — export as JPG ~85% quality to get under the limit), or grab the
  outro frame at 1:07.
- **Audience**: not made for kids · **Visibility**: your call — video is fully
  self-contained.
- **End screen**: link element pointing at the GitHub repo URL.

## Publishing notes

The repo is public, so the video/description link works for viewers. Music bed: reused
from the in-house salesvideo pipeline; narration is ElevenLabs, art is gpt-image-2.
