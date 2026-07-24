/*
 * robot.ino — per-robot firmware for the differential-drive wheeled swarm.
 *
 *   Receives (v, omega) velocity setpoints over ESP-NOW from the coordinator
 *   bridge, converts them to left/right wheel PWM (DRV8833), and reads a VL53L0X
 *   time-of-flight distance sensor for LOCAL emergency stop. There is no wheel
 *   encoder: the position loop is closed by the overhead camera at the
 *   coordinator, so each robot is a thin, honest actuator + a safety reflex.
 *
 * ⚠️  UNTESTED ON HARDWARE — reference firmware. Bench-test with the wheels OFF
 *     the ground first; verify each wheel's forward direction before driving.
 *
 * Board: any ESP32 (Arduino core 3.x). Motor driver: DRV8833 (2 inputs/motor).
 * Deps (Library Manager): Adafruit_VL53L0X.  Flash one robot at a time and note
 * its MAC (printed at boot) — the coordinator addresses each robot by MAC.
 */
#include <Wire.h>
#include <WiFi.h>
#include <esp_now.h>
#include <math.h>
#include <Adafruit_VL53L0X.h>

// ---------------- pins (EDIT for your board) ----------------
static const int AIN1 = 2, AIN2 = 3;     // left motor  (DRV8833 A)
static const int BIN1 = 4, BIN2 = 5;     // right motor (DRV8833 B)
static const int I2C_SDA = 6, I2C_SCL = 7;

// ---------------- constants ----------------
static const int PWM_FREQ = 20000, PWM_RES = 10;
static const int PWM_MAX = (1 << PWM_RES) - 1;
static const uint32_t FAILSAFE_MS = 400;
static const float V_MAX = 0.35f;        // m/s at full PWM (from your motor test)
static const float W_MAX = 2.5f;         // rad/s
static const float HALF_BASE = 0.07f;    // half the wheel track (m)
static const float WHEEL_R = 0.033f;     // wheel radius (m) — for v -> wheel speed
static const int   STOP_MM = 90;         // ToF: hard-stop forward under this range

// ---------------- ESP-NOW packet (must match the bridge) ----------------
typedef struct __attribute__((packed)) {
  uint8_t armed;      // 0/1
  float   v;          // m/s   (+forward)
  float   omega;      // rad/s (+CCW)
} Setpoint;

volatile Setpoint sp = {0, 0, 0};
volatile uint32_t lastRxMs = 0;
static portMUX_TYPE spMux = portMUX_INITIALIZER_UNLOCKED;

Adafruit_VL53L0X tof;
bool tofOk = false;

// ---------------- ESP-NOW ----------------
void onRecv(const esp_now_recv_info_t *info, const uint8_t *data, int len) {
  if (len != sizeof(Setpoint)) return;
  portENTER_CRITICAL(&spMux);
  memcpy((void *)&sp, data, sizeof(Setpoint)); lastRxMs = millis();
  portEXIT_CRITICAL(&spMux);
}

// ---------------- motors (DRV8833: sign chooses direction) ----------------
void wheel(int in1, int in2, float u) {                 // u in [-1,1]
  u = u < -1 ? -1 : (u > 1 ? 1 : u);
  int duty = (int)(fabsf(u) * PWM_MAX);
  ledcWrite(in1, u >= 0 ? duty : 0);
  ledcWrite(in2, u >= 0 ? 0 : duty);
}
void stop() { wheel(AIN1, AIN2, 0); wheel(BIN1, BIN2, 0); }

void setup() {
  Serial.begin(115200);
  for (int p : {AIN1, AIN2, BIN1, BIN2}) { ledcAttach(p, PWM_FREQ, PWM_RES); ledcWrite(p, 0); }
  Wire.begin(I2C_SDA, I2C_SCL);
  tofOk = tof.begin();
  if (tofOk) tof.startRangeContinuous();
  WiFi.mode(WIFI_STA);
  Serial.print("Robot MAC (add to coordinator): "); Serial.println(WiFi.macAddress());
  if (esp_now_init() != ESP_OK) Serial.println("ESP-NOW init failed");
  esp_now_register_recv_cb(onRecv);
}

void loop() {
  // atomic snapshot of the setpoint (written by the ESP-NOW task on the other core)
  Setpoint s; uint32_t rxMs;
  portENTER_CRITICAL(&spMux);
  memcpy(&s, (const void *)&sp, sizeof s); rxMs = lastRxMs;
  portEXIT_CRITICAL(&spMux);
  if (!isfinite(s.v)) s.v = 0;
  if (!isfinite(s.omega)) s.omega = 0;

  bool armed = s.armed && (millis() - rxMs < FAILSAFE_MS);   // link-loss failsafe
  if (!armed) { stop(); delay(5); return; }

  // local ToF emergency stop: if something is close ahead, kill forward motion
  float v = s.v;
  if (tofOk && tof.isRangeComplete()) {
    int mm = tof.readRangeResult();
    if (mm > 0 && mm < STOP_MM && v > 0) v = 0;
  }

  // differential-drive mixing: wheel linear speeds -> normalised PWM
  float vl = v - s.omega * HALF_BASE;
  float vr = v + s.omega * HALF_BASE;
  wheel(AIN1, AIN2, vl / V_MAX);
  wheel(BIN1, BIN2, vr / V_MAX);
  delay(5);
}
