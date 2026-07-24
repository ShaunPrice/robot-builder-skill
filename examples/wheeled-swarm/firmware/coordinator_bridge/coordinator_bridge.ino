/*
 * coordinator_bridge.ino — USB-serial -> ESP-NOW bridge for the wheeled swarm.
 *
 * One spare ESP32 on the laptop. It receives one line per robot from
 * swarm_coordinator.py and unicasts a velocity setpoint to that robot.
 *
 * Serial line (115200 baud), '\n' terminated:   id,armed,v,omega
 *   e.g.  1,1,0.18,-0.6
 *
 * ⚠️  UNTESTED ON HARDWARE — reference code. Paste each robot's MAC (printed at
 *     boot) into ROBOT_MAC[]. All robots + this bridge share one Wi-Fi channel.
 */
#include <WiFi.h>
#include <esp_now.h>

uint8_t ROBOT_MAC[][6] = {
  {0x24, 0x6F, 0x28, 0x00, 0x00, 0x01},   // robot 0  <-- EDIT
  {0x24, 0x6F, 0x28, 0x00, 0x00, 0x02},   // robot 1  <-- EDIT
  {0x24, 0x6F, 0x28, 0x00, 0x00, 0x03},   // robot 2  <-- EDIT
};
static const int N_ROBOTS = sizeof(ROBOT_MAC) / 6;

typedef struct __attribute__((packed)) { uint8_t armed; float v, omega; } Setpoint;

char buf[80]; int blen = 0;

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  if (esp_now_init() != ESP_OK) { Serial.println("ESP-NOW init failed"); return; }
  for (int i = 0; i < N_ROBOTS; i++) {
    esp_now_peer_info_t p = {};
    memcpy(p.peer_addr, ROBOT_MAC[i], 6); p.channel = 0; p.encrypt = false;
    esp_now_add_peer(&p);
  }
  Serial.print("Bridge ready, "); Serial.print(N_ROBOTS); Serial.println(" robots");
}

void handleLine(char *s) {
  // aligned locals then assign (never sscanf into a packed struct member — Xtensa unaligned store)
  int id, armed; float v, omega;
  if (sscanf(s, "%d,%d,%f,%f", &id, &armed, &v, &omega) == 4 && id >= 0 && id < N_ROBOTS) {
    Setpoint sp; sp.armed = (uint8_t)armed; sp.v = v; sp.omega = omega;
    esp_now_send(ROBOT_MAC[id], (uint8_t *)&sp, sizeof(sp));
  }
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || blen >= (int)sizeof(buf) - 1) { buf[blen] = 0; handleLine(buf); blen = 0; }
    else if (c != '\r') buf[blen++] = c;
  }
}
