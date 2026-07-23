# Getting started: SD cards, first boot, and controllers

This file covers rungs 2–3 of the ladder: getting an OS onto the robot's brain, getting a
controller talking to it, and achieving safe first motion.

## Writing SD cards / flashing firmware

### Raspberry Pi (microSD)

Use **Raspberry Pi Imager** (official, free, all platforms) — not `dd`, not Etcher, because
Imager pre-configures headless access:

1. Buy a decent card: 32 GB+, A2-rated (SanDisk Extreme, Samsung Evo Plus). Cheap cards are
   the #1 cause of "my Pi is flaky".
2. In Imager: choose device → choose OS (**Raspberry Pi OS (64-bit)** for desktop use, or
   **Lite (64-bit)** for headless robots — robots should be headless) → choose the SD card.
3. **Click the gear / "Edit settings" before writing.** Set: hostname (e.g. `rover-01`),
   enable SSH (public-key auth if the user has a key: `cat ~/.ssh/id_ed25519.pub`), a
   username + strong password (NOT the default `pi`), Wi-Fi SSID/password + country, locale.
   This is the security starting line — see security.md.
4. Write, boot, find it with `ping rover-01.local` (mDNS) or the router's DHCP table, then
   `ssh user@rover-01.local`.
5. First-login ritual: `sudo apt update && sudo apt full-upgrade -y`, `sudo raspi-config`
   for interfaces (enable I2C/SPI/camera as needed), then reboot.

If Imager isn't available: Balena Etcher or `dd` work, but you must create `ssh` and
`userconf.txt`/custom firstrun files by hand — prefer Imager.

### NVIDIA Jetson

- **Orin Nano / Orin NX devkits**: current JetPack no longer boots well from SD alone on
  older QSPI firmware. The reliable path is **NVIDIA SDK Manager** on an Ubuntu x86 host
  (VM with USB passthrough is possible but fussy; native Ubuntu or a spare laptop is
  better): put the Jetson in recovery mode (jumper FC REC → GND, connect USB-C), let SDK
  Manager flash JetPack (L4T + CUDA + TensorRT) to NVMe. **Buy a cheap NVMe SSD
  ($25, 256 GB+) — running Jetson from microSD is slow and wears the card.**
- Orin Nano devkit *can* be flashed via SD image from NVIDIA's site if QSPI firmware is
  already current — try that first (it's the easy path), fall back to SDK Manager.
- After flash: `sudo apt update && sudo apt upgrade`, install `jtop`
  (`sudo pip3 install jetson-stats`) — it's the Jetson dashboard for power modes,
  temps, and library versions. Set max power mode for benching: `sudo nvpmodel -m 0`.

### Flight controllers (drones/planes/boats/rovers with autopilots)

No SD imaging — firmware flashes over USB:

- **ArduPilot** (versatile: copter/plane/rover/sub): flash with **Mission Planner**
  (Windows) or **QGroundControl** (all platforms). Select the exact board name.
- **PX4**: flash with **QGroundControl**.
- **Betaflight** (FPV quads): **Betaflight Configurator** (app). Hold BOOT button while
  plugging in for DFU mode if the board is bricked/new.
- The autopilot's own microSD card (Pixhawk-style boards) just needs FAT32 — it stores
  logs and terrain data, no imaging required.

### ESP32/Arduino (microcontroller robots)

No SD card at all. Install **Arduino IDE** or **PlatformIO** (recommended for real
projects), select board + port, upload over USB. ESP32 boards sometimes need the BOOT
button held during upload. CH340/CP210x USB drivers are the usual "port not found" fix on
Windows/macOS.

## Controllers

### Controller-only robots (no computer aboard — T0)

RC transmitter (the thing in your hands, "TX") + receiver on the robot ("RX"):

1. **Protocols must match**: FrSky↔FrSky, ELRS↔ELRS, Spektrum↔Spektrum. Modern
   recommendation: **ExpressLRS (ELRS)** — cheap, open source, superb range.
   RadioMaster Pocket (~$65) or Boxer with an ELRS RX (~$15–20).
2. **Binding**: power the RX in bind mode (button on RX, or via LUA script for ELRS —
   TX and RX must be on the same ELRS version and "binding phrase"), then confirm the
   RX LED goes solid.
3. **Wiring**: toy-grade cars have RX+ESC integrated. Hobby-grade: RX channel 1 → steering
   servo, channel 2 → ESC (which powers the RX via its BEC — don't also feed the RX from
   another 5 V source).
4. **Before first drive**: check failsafe — turn the TX off while the robot is on blocks
   and confirm motors stop. Set this in the RX/ESC if it doesn't.

### Bluetooth gamepads on a Pi/Jetson (T1+)

Xbox, DualSense/DS4, and 8BitDo pads all pair over Bluetooth:

```bash
sudo apt install -y joystick bluetooth bluez
bluetoothctl
# inside bluetoothctl:
#   scan on            → put pad in pairing mode (Xbox: hold pair button;
#                        PS: hold SHARE+PS until light flashes)
#   pair XX:XX:...     → then: trust XX:XX:...  → connect XX:XX:...
jstest /dev/input/js0    # verify axes/buttons
```

In Python, read it with `pygame` or `evdev`; in ROS 2, `ros2 run joy joy_node` publishes
`/joy` and `teleop_twist_joy` turns it into velocity commands. Xbox pads on older kernels
may need `xpadneo`; DS4 works out of the box.

### Web/phone control (nice for demos)

A tiny Flask/FastAPI server on the robot serving a page with buttons/joystick → simplest
cross-device controller, and doubles as the first "robot API". Keep it LAN-only
(see security.md).

## First boot & first motion checklist

Work through this in order; each line is a session-sized win for a beginner:

1. **Power the brain alone** (no motors wired). SSH in. Blink an LED / print sensor value.
2. **Motor driver wired, robot on blocks** (wheels off ground / props OFF). Command one
   motor at low duty cycle. Confirm direction; swap wires if backwards (that's the fix,
   not shame).
3. **Both/all motors + steering**: forward, back, spin. Still on blocks.
4. **Controller teleop on blocks.** Verify E-stop: releasing sticks (or a dedicated
   button) must stop everything. Software watchdog: if no command for 500 ms, stop motors.
5. **Floor test** in a clear area, slowest speed.
6. Commit the code. Update BUILD_LOG.md. Celebrate — this is "first motion", the biggest
   milestone in any build.

## Common first-week failures (check in this order)

| Symptom | Usual cause |
|---|---|
| Pi won't boot / rainbow screen | Bad SD card or inadequate power supply (Pi 5 wants 5 V/5 A) |
| Pi reboots when motors start | Motors browning out the 5 V rail → separate motor battery, common ground |
| One motor runs, other doesn't | Loose Dupont jumper (crimp or solder for anything permanent) |
| Motors hum but don't turn | Duty cycle too low, or L298N eating the voltage (replace it) |
| "It worked yesterday" | Battery is flat. Check voltage first, always |
| Controller pairs but no input | Wrong event device — check `ls /dev/input/`, use `evtest` |
| ESC beeping endlessly | It wants a valid throttle signal / throttle not at zero — recalibrate |
| Serial port missing (ESP32) | USB cable is charge-only, or missing CH340/CP210x driver |

## Graduation

When teleop is boring, the user is ready for sensors ([sensors.md](sensors.md)) and then
autonomy ([ros.md](ros.md) for ground/water, autopilot missions in
[air-robots.md](air-robots.md) for aircraft).
