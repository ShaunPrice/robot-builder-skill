# Build instructions — differential-drive swarm robot

Assembly, wiring, flashing and bring-up for **one** robot, then the camera + swarm. Build and prove
one before you make three. Pair with [`SWARM_BUILD.md`](SWARM_BUILD.md) (parts + costs),
[`engineering/swarm-robot-calcs.xlsx`](engineering/swarm-robot-calcs.xlsx), and the CAD in `cad/`.

> ⚠️ Proven in **simulation** only; the firmware is **untested reference code**. Test with the
> **wheels off the ground** first and verify each wheel's direction before it can drive off a table.
> Not sponsored. Build at your own risk.

## 1. Print the parts
- **Chassis:** `cad/chassis.stl` (regenerate/tune with `cad/gen_chassis.py`). PLA/PETG, 0.2 mm layers,
  ~40 % infill, no supports (prints flat). ~14 g.
- **Fiducials:** `python cad/make_tags.py 3` → `aruco_id0/1/2.png`. **Print at 100 % scale** so each
  marker is ~60 mm, cut out, and stick one flat on the top of each robot (id 0 on robot 0, etc.).
- Bolt the **four TT motors** into the chassis's corner mounts (axles out the side slots); press a
  65 mm wheel onto each axle. Two motors face left, two face right.

## 2. Wire it up
Common ground everywhere (battery −, DRV8833 GND, ESP32 GND, sensor GND).

**Motors — DRV8833, four motors as two skid-steer channels** (both left motors in parallel on channel
A, both right motors on channel B):

| ESP32 | → DRV8833 | DRV8833 out | → |
|---|---|---|---|
| GPIO2 | AIN1 | AO1 / AO2 | **both LEFT** motors (in parallel) |
| GPIO3 | AIN2 | | |
| GPIO4 | BIN1 | BO1 / BO2 | **both RIGHT** motors (in parallel) |
| GPIO5 | BIN2 | | |
| 3V3 | SLEEP/EEP (enable) | VM | battery + (motor voltage) |

**Distance sensor — HC‑SR04:** VCC→5 V, GND→GND, TRIG→GPIO8, ECHO→GPIO9 **through a divider / level
shifter** (ECHO is 5 V, the ESP32 is 3.3 V). Mount it looking **forward** through the chassis's front slot.

**Power:** the **4×AA pack** (6 V) feeds the DRV8833 `VM` (motors). Power the ESP32 from a small **5 V
buck** off the same pack, or from a **USB power bank** (easiest for a first build) — either way, tie
all grounds together. Pins are set at the top of `robot.ino` — edit to match your board.

## 3. Flash the robots
- Arduino IDE with the **ESP32 core (3.x)**. (No extra library needed — the HC‑SR04 is read directly.)
- Open `firmware/robot/robot.ino`, select your board + port, **Upload**.
- Serial Monitor @ 115200: **copy the `Robot MAC`** it prints. Flash each robot; keep a MAC list.

## 4. Flash the bridge
- On a **spare ESP32**, open `firmware/coordinator_bridge/coordinator_bridge.ino`, paste the robots'
  MACs into `ROBOT_MAC[]`, upload. Note its serial port.

## 5. Set up the camera
- Mount the webcam **looking straight down** ~1–1.5 m above the play area so the whole arena is in
  view and the tags are crisp. Even, glare-free lighting.
- Preview detection (no robots moving needed):
  ```bash
  cd coordinator
  python swarm_coordinator.py --camera 0 --show --marker-mm 60 --ids 0,1,2
  ```
  You should see all three tags outlined. Set `--marker-mm` to your printed size and `--ids` to the
  ids you stuck on, in robot order.

## 6. Bring-up — wheels OFF the ground
1. Preview the whole mission with **no hardware**:
   ```bash
   python swarm_coordinator.py --sim
   ```
2. Drive real robots with the wheels up:
   ```bash
   python swarm_coordinator.py --camera 0 --port /dev/tty.usbserial-XXXX --ids 0,1,2 --show
   ```
   (`pip install opencv-contrib-python pyserial`.) Confirm each robot's wheels spin the **right way**
   for forward — if a wheel is reversed, swap its two motor leads (or its two `IN` pins in `robot.ino`).
   **`Ctrl-C` disarms every robot.**

## 7. On the floor
Set the robots on the play area, run the same command, and watch them gather into the triangle,
translate, rotate, reform as a line, and park — the mission you proved in simulation. Log what worked
(pin map, marker size, camera height, motor directions) in a `BUILD_LOG.md`.

> **Localisation notes.** Accuracy comes from the camera: mount it square to the floor, keep tags flat
> and well-lit, and keep the whole arena in frame. If a robot's tag drops out momentarily it holds its
> last pose; long occlusions will drift it — keep the view clear.
