# Sensors: cameras, depth, lidar, IMU, GPS, and friends

Rung 4. Order of value for most robots: **camera → encoders → IMU → range sensing
(lidar/depth) → GPS**. Add one sensor at a time and verify it with a live plot/echo before
adding the next.

## Cameras

- **CSI (ribbon) cameras**: Pi Camera Module 3 (~$25, autofocus, HDR) on Pi; IMX219/IMX477
  modules on Jetson. Lowest latency, best Linux integration (`libcamera`/Argus).
- **USB (UVC) webcams**: work everywhere (`/dev/video0`, OpenCV `VideoCapture`), slightly
  more latency. Logitech C920 is the boring reliable choice.
- Gotchas: CSI ribbons are fragile and directional (contacts face the board's contact
  side); long ribbons pick up noise; on Jetson use GStreamer pipelines
  (`nvarguscamerasrc`) for hardware-accelerated capture.
- For AI: 640×480 @ 30 fps is plenty for most detection tasks — resolution costs FPS.

## Depth cameras (RGB-D)

Give you a per-pixel distance image — obstacle avoidance, 3D mapping, grasping.

| Camera | ~Price | Tech | Notes |
|---|---|---|---|
| OAK-D Lite / OAK-D Pro | $150 / $250–400 | Stereo (+active IR on Pro) + **onboard NPU** | Runs YOLO *on the camera* — the best depth choice for Raspberry Pi hosts |
| RealSense D435i / D455 | $300–400 | Active IR stereo | The ROS-era standard; D435i adds IMU (worth it for SLAM/VIO). Mature `realsense-ros` wrapper |
| Any ToF module (Arducam etc.) | $50–150 | Time-of-flight | Short range, indoor; simple integration |
| Used Kinect/Xtion | $20–50 | Structured light | Fun and cheap, ancient drivers — only for tinkerers |

Depth camera realities:
- IR stereo struggles **outdoors in sunlight** (IR washout) and on textureless/shiny/black
  surfaces — expect holes in the depth image; filter them.
- Real usable range is ~0.3–6 m regardless of spec-sheet optimism.
- USB 3 cable quality matters; use the short cable that shipped with it. RealSense on
  ARM: match `librealsense` version to the ROS wrapper version exactly, and prefer
  `sensor_data` QoS in ROS 2 subscriptions.

## Lidar

2D lidar gives a 360° range scan — the classic input for SLAM and indoor navigation.

- **RPLIDAR C1/A1** (~$70–100): the starter. 12 m, 10 Hz. `sllidar_ros2` driver.
- **LDROBOT LD19/STL-19P** (~$90): small, solid.
- **RPLIDAR S-series** (~$300–600): outdoor-capable, longer range.
- **3D**: Livox Mid-360 (~$750) — real 3D SLAM territory; Unitree L2 (~$400) emerging.
- 1D rangefinders: TF-Mini/TF-Luna ToF (~$20–40, UART/I2C) — great as bump/cliff/altitude
  sensors; ultrasonic HC-SR04 (~$3) works but is noisy and slow.

Lidar vs depth camera: lidar = robust geometry, 360°, great for SLAM/Nav2, but no
semantics and (2D) only one plane. Depth cam = semantics + 3D but narrow FOV and lighting
sensitivity. Mature robots often carry both; on a budget: **lidar for navigation,
camera for understanding**.

Gotchas: lidars on USB serial adapters need stable 5 V (brownouts = "lidar disconnects
randomly"); mount above chassis clutter or you map your own wiring loom; spinning lidars
hate dust and fingers.

## IMU (accelerometer + gyro ± magnetometer)

- **BNO055/BNO085** (~$25–30): does sensor fusion on-chip, outputs quaternion directly —
  the beginner-friendly choice.
- **MPU-6050/9250, ICM-20948** (~$5–15): raw data; fuse with Madgwick/Mahony filter (or
  let `robot_localization` do it in ROS 2).
- Autopilot boards already contain good IMUs — don't add another.
- Realities: mount away from motor vibration (foam tape helps); magnetometers are useless
  near motors/power wiring — calibrate away from the robot, and distrust heading indoors;
  gyros drift, so heading needs mag/GPS/vision to stay true. Calibrate on every new build.

## GPS / GNSS (outdoor only)

- u-blox M8N/M10 module (~$25–40): 1.5–3 m accuracy, fine for waypoint missions.
- **RTK** (ZED-F9P, ~$200–300 + corrections from a base station or NTRIP service):
  centimeter accuracy — needed for mowing-stripe-grade paths.
- Realities: no GPS indoors, poor near buildings (multipath); mount the antenna high with
  clear sky view and away from the Pi/Jetson (RF noise from USB 3 famously jams GPS —
  shielding/distance fixes it); first fix takes 30 s–5 min cold.
- Autopilot users: buy a combined GPS+compass module and mount it on a mast.

## Encoders (the most underrated sensor)

Wheel encoders turn "I told the motors to go" into "we actually went 1.2 m". Without them
there is no real odometry, and SLAM/Nav2 quality suffers badly.

- Buy gearmotors **with encoders built in** (JGA25-371, JGB37, Pololu micro-metal with
  magnetic encoder boards).
- Count edges with MCU interrupts (or Pi Pico PIO — flawless at high rates). The Pi itself
  can miss interrupts under load — this is a top reason to add an MCU.
- Convert ticks → distance with wheel diameter + gear ratio + CPR; calibrate by driving a
  measured 2 m and adjusting.

## Domain extras

- **Water**: pressure/depth sensor (Blue Robotics Bar30, ~$85), leak probes (~$30),
  underwater sonar (Ping/Ping360). Magnetometers are your only cheap heading source
  underwater (no GPS below the surface!).
- **Air**: barometer (on every autopilot) for altitude; airspeed pitot sensor for fixed
  wing; lidar/ToF pointing down for precision landing; optical flow (e.g. PMW3901) for
  GPS-free position hold.
- **Rockets**: barometric altimeter (commercial: PerfectFlite, Eggtimer) + high-g
  accelerometer; log fast (≥100 Hz), events are over in seconds.

## Verification habits (do these before trusting any sensor)

- Echo raw data live (`ros2 topic echo`, a matplotlib live plot, or the vendor viewer —
  `realsense-viewer`, RPLIDAR's demo app) and physically wave a hand / rotate the robot to
  confirm the numbers move the right way.
- Check the **frame conventions** early: ROS uses x-forward, y-left, z-up (REP-103); many
  IMU breakouts don't. A sign error here costs days later.
- Timestamp everything at capture; sensor fusion with wrong timestamps is worse than no
  fusion.
- Record a dataset the first day a sensor works (`ros2 bag record`, or plain CSV/video) —
  it lets you develop perception code on the desk without the robot.
