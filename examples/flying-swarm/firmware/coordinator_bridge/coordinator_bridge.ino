/*
 * coordinator_bridge.ino — USB-serial -> ESP-NOW bridge for the swarm.
 *
 * One spare ESP32 plugged into the laptop. It receives one line per drone from
 * swarm_coordinator.py and unicasts a Setpoint to that drone over ESP-NOW.
 *
 * Serial line format (115200 baud), terminated by '\n':
 *     id,armed,throttle,pitch_sp,roll_sp,yaw_rate_sp
 *   e.g.  2,1,0.42,-3.0,1.5,0.0
 *
 * ⚠️  UNTESTED ON HARDWARE — reference code. Fill DRONE_MAC[] with the MACs each
 *     drone prints at boot. All drones + this bridge must share one Wi-Fi channel.
 */
#include <WiFi.h>
#include <esp_now.h>

// One row per drone — paste the MAC each drone prints over serial at boot.
uint8_t DRONE_MAC[][6] = {
  {0x24, 0x6F, 0x28, 0x00, 0x00, 0x01},   // drone 0  <-- EDIT
  {0x24, 0x6F, 0x28, 0x00, 0x00, 0x02},   // drone 1  <-- EDIT
  {0x24, 0x6F, 0x28, 0x00, 0x00, 0x03},   // drone 2  <-- EDIT
  {0x24, 0x6F, 0x28, 0x00, 0x00, 0x04},   // drone 3  <-- EDIT
  {0x24, 0x6F, 0x28, 0x00, 0x00, 0x05},   // drone 4  <-- EDIT
};
static const int N_DRONES = sizeof(DRONE_MAC) / 6;

typedef struct __attribute__((packed)) {
  uint8_t armed; float throttle, pitch_sp, roll_sp, yaw_rate_sp;
} Setpoint;

char buf[96]; int blen = 0;

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  if (esp_now_init() != ESP_OK) { Serial.println("ESP-NOW init failed"); return; }
  for (int i = 0; i < N_DRONES; i++) {
    esp_now_peer_info_t p = {};
    memcpy(p.peer_addr, DRONE_MAC[i], 6);
    p.channel = 0; p.encrypt = false;
    esp_now_add_peer(&p);
  }
  Serial.print("Bridge ready, "); Serial.print(N_DRONES); Serial.println(" drones");
}

void handleLine(char *s) {
  // Parse into ALIGNED locals — taking &member of a packed struct for sscanf is
  // an unaligned store (Xtensa LoadStoreAlignment risk). Member writes are byte-wise & safe.
  int id, armed; float thr, p, r, y;
  int n = sscanf(s, "%d,%d,%f,%f,%f,%f", &id, &armed, &thr, &p, &r, &y);
  if (n == 6 && id >= 0 && id < N_DRONES) {
    Setpoint sp;
    sp.armed = (uint8_t)armed; sp.throttle = thr;
    sp.pitch_sp = p; sp.roll_sp = r; sp.yaw_rate_sp = y;
    esp_now_send(DRONE_MAC[id], (uint8_t *)&sp, sizeof(sp));
  }
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || blen >= (int)sizeof(buf) - 1) { buf[blen] = 0; handleLine(buf); blen = 0; }
    else if (c != '\r') buf[blen++] = c;
  }
}
