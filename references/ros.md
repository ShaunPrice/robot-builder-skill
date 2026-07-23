# ROS 2: from zero to Nav2

ROS 2 is the middleware that lets sensors, algorithms, and motors talk as composable
nodes. Recommend it when the robot has ≥2 sensors and autonomy ambitions (T2+). Skip it
for T0/T1 (plain Python is faster to joy) and for pure FPV/autopilot aircraft (the
autopilot ecosystem covers it).

## Install (get the pairing right)

ROS 2 releases pin to Ubuntu versions. Use the current LTS pairing — as of 2026:
**ROS 2 Jazzy on Ubuntu 24.04** (Humble/22.04 still fine and widely documented; prefer
whichever matches the OS the user already has).

- **Pi 5**: Ubuntu Server 24.04 (Raspberry Pi Imager offers it) + `ros-jazzy-ros-base`
  via apt. (ROS on Raspberry Pi OS means Docker or source builds — steer to Ubuntu instead.)
- **Jetson**: JetPack 6 is Ubuntu 22.04-based → Humble natively, or run Jazzy in Docker
  (`ros:jazzy` images run fine; NVIDIA's Isaac ROS containers when using their GEMs).
- **Desktop** (develop here, deploy to robot): `ros-jazzy-desktop` for RViz/Gazebo.
- Follow docs.ros.org's apt instructions verbatim; then add
  `source /opt/ros/jazzy/setup.bash` to `~/.bashrc`.

## The mental model (teach in this order)

1. **Nodes** publish/subscribe **topics** (typed messages) — `ros2 topic list/echo/hz`.
2. **Services** = request/reply; **actions** = long-running goals with feedback (Nav2 uses
   actions).
3. **Parameters** = per-node config; **launch files** (Python) start the whole robot.
4. **TF2** = the tree of coordinate frames (`map → odom → base_link → laser`). Half of all
   ROS problems are TF problems; `ros2 run tf2_tools view_frames` is the X-ray.
5. **QoS**: sensors publish *best-effort* (`sensor_data` profile); if a subscriber
   demands *reliable*, you get silent no-data. When "the topic exists but echo shows
   nothing", check QoS compatibility first, then TF, then network.

## Minimum viable ROS robot (differential drive)

Packages that give a full teleop→SLAM→autonomy stack without writing much code:

```
joy + teleop_twist_joy        # gamepad → /cmd_vel
<your motor node>             # /cmd_vel → PWM; publish /odom from encoders  (you write this one)
robot_state_publisher + URDF  # robot description → TF
sllidar_ros2 (or camera driver)
slam_toolbox                  # lidar SLAM → /map
nav2_bringup                  # autonomous navigation
```

The one node the user writes — `/cmd_vel` (`geometry_msgs/Twist`) in, motor commands out,
encoder ticks in, `/odom` + TF out — is the rite of passage. Write it with them in Python
(`rclpy`), ~150 lines. Include a watchdog: no `/cmd_vel` for 500 ms → motors stop.

Build/workspace basics: `mkdir -p ~/ros2_ws/src`, packages created with
`ros2 pkg create --build-type ament_python my_robot`, build with
`colcon build --symlink-install`, then `source install/setup.bash`. Commit the workspace
`src/` to git; never commit `build/ install/ log/`.

## URDF (robot description)

Even a crude URDF (two wheels + a box + sensor mounts) pays off immediately: RViz
visualization, correct TF, Nav2 footprint, simulation. Write it as xacro. Measure the
real robot; wrong wheel separation = curved "straight" lines.

## SLAM and Nav2 (the payoff)

- **Mapping**: drive around with `slam_toolbox` (async mode) → save with
  `ros2 run nav2_map_server map_saver_cli -f mymap`.
- **Navigation**: `nav2_bringup` with your map + AMCL localization. Click a goal in RViz;
  the robot plans and drives. Tune later: costmap inflation radius, robot footprint,
  velocity limits (start SLOW).
- Depth-camera-only robots: `depthimage_to_laserscan` fakes a lidar scan well enough for
  Nav2 indoors — note its output QoS may need RELIABLE override to feed some consumers.
- 3D/outdoor: that's `nav2` + GPS (`robot_localization` fusing GPS+IMU+odom) or
  research-tier 3D SLAM — set expectations that outdoor autonomy is a big step up.

## Simulation

- **Gazebo (new/Harmonic+)**: pairs with Jazzy; simulate the URDF with a diff-drive plugin
  and lidar before/alongside the real robot. Great for testing Nav2 configs safely.
- **Isaac Sim/Isaac Lab** (needs RTX PC): photoreal + RL training; overkill until T3+.
- **SITL** (aircraft/boats): ArduPilot/PX4 software-in-the-loop — see air-robots.md; it's
  the reason autopilot users can develop without crashing.

## micro-ROS (the MCU joins the graph)

ESP32/Pico running micro-ROS appears as native ROS 2 nodes via an agent on the Pi
(serial or UDP/Wi-Fi). Use it when the MCU owns motors/encoders and you want
`/cmd_vel`/`/odom` to terminate on the MCU itself. Setup is finicky (agent + firmware
versions must match); budget an afternoon.

## Multi-machine ROS (dev PC + robot)

Same LAN + same `ROS_DOMAIN_ID` (pick a non-zero number, 1–101) = topics just appear on
both machines. This is the normal workflow: heavy tools (RViz, rqt) on the desktop, drivers
on the robot. Realities:
- Wi-Fi multicast discovery is flaky on some routers — if discovery fails, set
  `ROS_AUTOMATIC_DISCOVERY_RANGE`/static peers, or use a discovery server, or CycloneDDS
  with peers listed.
- Isolate projects/machines with different `ROS_DOMAIN_ID`s; on shared networks this
  avoids "why am I seeing someone else's robot".
- Bandwidth: don't ship raw images over Wi-Fi; use `image_transport` compressed topics.
- Security: DDS is unauthenticated by default on the LAN — anyone on the network can
  publish `/cmd_vel`. See security.md (SROS2 / network isolation).

## Debug toolbox (teach these before writing more code)

`ros2 topic list | echo | hz | info -v` (the `-v` shows QoS), `ros2 node info`,
`rqt_graph`, `ros2 bag record/play`, `tf2_tools view_frames`, RViz. Rule: when something
doesn't work, first prove data is flowing (`hz`), then prove frames are right (TF tree),
then look at the algorithm.
