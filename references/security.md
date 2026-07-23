# Security: connecting robots to networks, the internet, and the cloud

A robot is a computer with motors. Compromise means physical consequences, so the bar is
higher than for a web app. Apply this file the day the robot first joins Wi-Fi, not
"later" — later never comes.

## Threat model (keep it proportionate)

Hobby robots mostly face: opportunistic scanning of exposed ports, default credentials,
neighbors/guests on the LAN, and the user's own future mistakes (leaked keys in a public
repo, an open video stream). Nation-states are not after the rover; sloppy MQTT brokers
and port-forwards are the actual risk. Secure accordingly — simple, layered, low-friction.

## Baseline (every robot, day one)

1. **No default credentials.** Unique username + strong password set at image time
   (Raspberry Pi Imager does this). Change any vendor default on cameras, routers, FCs.
2. **SSH keys, not passwords**:
   ```bash
   ssh-keygen -t ed25519          # on the laptop, if no key yet
   ssh-copy-id user@robot.local
   # then on the robot, in /etc/ssh/sshd_config:
   #   PasswordAuthentication no
   #   PermitRootLogin no
   sudo systemctl restart ssh
   ```
3. **Updates**: `sudo apt update && sudo apt full-upgrade` regularly;
   `unattended-upgrades` for security patches on long-lived robots.
4. **Firewall — default deny inbound**:
   ```bash
   sudo apt install ufw
   sudo ufw default deny incoming && sudo ufw default allow outgoing
   sudo ufw allow from 192.168.0.0/24 to any port 22   # SSH from home LAN only
   sudo ufw enable
   ```
5. **Only run what you need**: `sudo ss -tlnp` and question every listening port.
6. **Physical**: anyone with the SD card owns the robot. For robots that leave the house,
   consider full-disk encryption impractical-but-possible; at minimum, no long-lived cloud
   credentials stored in plain text on the card (scope them, see below).

## Remote access: the one rule

**Never port-forward a robot (or its camera, or its MQTT broker) to the internet.** No
DMZ, no UPnP, no "temporary" NAT rules. Shodan indexes these within hours.

The right answer is an **overlay VPN**:

- **Tailscale** (WireGuard-based, free tier is generous): install on robot + laptop +
  phone; each gets a stable private IP; SSH/video/ROS work from anywhere as if at home;
  nothing is exposed publicly. This is the default recommendation — setup is 10 minutes.
  Use an ACL so the robot can be reached but can't reach your other machines.
- **Plain WireGuard** self-hosted: same result, more control, more setup.
- Web dashboards for a robot: keep them LAN/VPN-only. If something truly must be public,
  put it behind an authenticating proxy (e.g. Cloudflare Access/Tunnel) — never the bare
  Flask app.

## Wireless links

- Wi-Fi: WPA2/WPA3 only; a **separate IoT SSID/VLAN** for robots keeps a compromised
  device away from laptops/NAS. Guest network is the poor-man's version — it at least
  gives client isolation.
- RC links (ELRS/FrSky): set a unique binding phrase/ID — prevents accidental takeover at
  a busy field.
- MAVLink telemetry radios are **unencrypted and unauthenticated** by design: anyone in RF
  range with the same radio can inject commands. Mitigations: change the default NetID,
  prefer MAVLink2 signing (set `SERIALn_PROTOCOL`/signing keys where supported), or run
  telemetry over the VPN via 4G instead of plain 915 MHz for anything sensitive.
- Cellular (4G robot): the carrier NATs you anyway; run Tailscale over it and everything
  works with zero exposure.
- Video streams (RTSP/WebRTC/MJPEG): password-protect or bind to the VPN interface — open
  camera streams are the most common hobby-robot leak.

## ROS 2 specifics

- Default DDS traffic is plaintext and unauthenticated: anyone on the LAN can echo your
  camera and publish `/cmd_vel`. On a home LAN behind your own router this is usually an
  accepted risk; on shared/university/competition networks it is not.
- Cheap mitigations first: robots on their own SSID/VLAN; unique `ROS_DOMAIN_ID`;
  `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` when everything runs on one machine.
- Real mitigation: **SROS2** (DDS-Security: authentication + encryption via certificates).
  It works but adds real friction — recommend for shared networks, competitions, or any
  robot around strangers.
- Never bridge ROS topics to the public internet raw; if remote ROS is needed, VPN first
  (Tailscale handles multi-machine ROS 2 discovery fine with static peers/discovery
  server).

## Cloud connections (telemetry, dashboards, AI APIs)

Principles, then services:

- **Authenticate with per-device credentials** — one leaked robot key revokes one robot,
  not the fleet. Never bake your personal cloud account keys into a robot.
- **TLS everywhere** (MQTT → port 8883 with TLS; HTTPS for REST).
- **Least privilege**: the robot's credential can publish `robots/rover01/telemetry` and
  read `robots/rover01/cmd` — nothing else. IAM policies/broker ACLs, not "allow all".
- **Secrets handling**: environment files (`/etc/robot/secrets.env`, `chmod 600`, owned
  by the service user) or systemd credentials — never hardcoded in the repo. Add
  `*.env`/`secrets*` to `.gitignore` on day one; scan before pushing
  (`gitleaks detect`) because robot repos love to accidentally contain Wi-Fi passwords
  and API keys.
- **Design for comms loss**: the robot must be safe (stop / loiter / RTL) when the cloud
  disappears mid-mission, and must not block motion control on a cloud round-trip.
  Cloud = telemetry, logging, non-realtime tasking. Local = control.
- **Command authentication**: if the cloud can send commands, sign or at least strictly
  validate them (schema + bounds + rate limit). A dashboard that publishes raw
  `cmd_vel` JSON to an open topic is a remote-control vulnerability.

Service notes:
- **MQTT**: Mosquitto with TLS + per-device users + ACL files is a fine self-hosted core.
  Public brokers (test.mosquitto.org etc.) are for experiments only — everything on them
  is world-readable.
- **AWS IoT Core / Azure IoT Hub**: X.509 per-device certs, policies scoped to the
  device's own topics, device shadows for state — the managed way to do fleet telemetry
  properly.
- **LLM/vision APIs from the robot**: the API key lives in the env file, calls go out
  over HTTPS, spending caps set on the account, and nothing safety-critical waits on the
  response (see ai-ml.md).

## OTA updates and supply chain

- Update mechanism = remote code execution by design, so: pull-based (robot fetches signed
  releases; nothing pushes to the robot), over the VPN, verify integrity (git tags/commit
  pins at minimum, signed artifacts better), and keep a rollback (previous release dir +
  symlink flip).
- Vet dependencies casually but genuinely: pin versions (`requirements.txt` with hashes,
  lockfiles), prefer well-known packages, and be suspicious of random "robot control"
  packages with three downloads.
- Flash vendor firmware (FCs, ESCs, cameras) from official sources only.

## Quick audit checklist (run when a robot goes "production")

- [ ] No default passwords anywhere (Pi, router, cameras, brokers, dashboards)
- [ ] SSH: keys only, root login off
- [ ] ufw default-deny; every open port justified
- [ ] Remote access via Tailscale/WireGuard only; zero port-forwards
- [ ] Robots on isolated SSID/VLAN
- [ ] MQTT/cloud: TLS + per-device credentials + scoped ACLs
- [ ] No secrets in the git repo (`gitleaks detect` clean); `.env` files chmod 600
- [ ] Comms-loss behavior defined AND tested (kill the Wi-Fi mid-run on blocks)
- [ ] RC binding phrase/NetID changed from default
- [ ] Update path documented; robot can be rebuilt from repo + image in <1 hr
