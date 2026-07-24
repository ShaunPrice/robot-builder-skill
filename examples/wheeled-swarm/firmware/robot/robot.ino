/*
 * robot.ino — per-robot firmware for the DIY 4-wheel differential (skid-steer) swarm robot.
 *
 *   Receives (v, omega) velocity setpoints over ESP-NOW from the coordinator
 *   bridge, converts them to left/right wheel PWM (DRV8833), and reads an HC-SR04
 *   ultrasonic sensor for a LOCAL emergency stop. Four TT motors are wired two per
 *   DRV8833 channel — both LEFT motors on channel A, both RIGHT motors on channel B
 *   — so this is ordinary differential / skid-steer control. There is no wheel
 *   encoder: the position loop is closed by the overhead camera at the coordinator,
 *   so each robot is a thin actuator + a safety reflex.
 *
 * ⚠️  UNTESTED ON HARDWARE — reference firmware. Bench-test with the wheels OFF the
 *     ground first; verify each wheel's forward direction before driving.
 *
 * Board: any ESP32 (Arduino core 3.x). Driver: DRV8833 (2 inputs/motor, 2 channels).
 * HC-SR04 ECHO is 5 V — use a divider / level shifter to the ESP32 3.3 V input.
 * Flash one robot at a time and note its MAC (printed at boot).
 */
#include <WiFi.h>
#include <esp_now.h>
#include <math.h>

// ---------------- pins (EDIT for your board) ----------------
static const int AIN1 = 2, AIN2 = 3;     // LEFT channel  (both left motors in parallel)
static const int BIN1 = 4, BIN2 = 5;     // RIGHT channel (both right motors in parallel)
static const int TRIG = 8, ECHO = 9;     // HC-SR04 (ECHO via level shifter / divider)

// ---------------- constants ----------------
static const int PWM_FREQ = 20000, PWM_RES = 10;
static const int PWM_MAX = (1 << PWM_RES) - 1;
static const uint32_t FAILSAFE_MS = 400;
static const float V_MAX = 0.35f;        // m/s at full PWM (from your motor test)
static const float HALF_BASE = 0.075f;   // half the wheel track (m)
static const float STOP_CM = 9.0f;       // hard-stop forward under this range

// ---------------- ESP-NOW packet (must match the bridge) ----------------
typedef struct __attribute__((packed)) {
  uint8_t armed;      // 0/1
  float   v;          // m/s   (+forward)
  float   omega;      // rad/s (+CCW)
} Setpoint;

volatile Setpoint sp = {0, 0, 0};
volatile uint32_t lastRxMs = 0;
static portMUX_TYPE spMux = portMUX_INITIALIZER_UNLOCKED;

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

// ---------------- HC-SR04 ultrasonic ----------------
float rangeCm() {
  digitalWrite(TRIG, LOW); delayMicroseconds(2);
  digitalWrite(TRIG, HIGH); delayMicroseconds(10); digitalWrite(TRIG, LOW);
  long us = pulseIn(ECHO, HIGH, 30000);                 // 30 ms timeout (~5 m)
  return us ? us * 0.0343f / 2.0f : 999.0f;             // no echo -> "clear"
}

void setup() {
  Serial.begin(115200);
  for (int p : {AIN1, AIN2, BIN1, BIN2}) { ledcAttach(p, PWM_FREQ, PWM_RES); ledcWrite(p, 0); }
  pinMode(TRIG, OUTPUT); pinMode(ECHO, INPUT);
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

  float v = s.v;
  if (rangeCm() < STOP_CM && v > 0) v = 0;                    // local ultrasonic e-stop

  // differential / skid-steer mixing: wheel linear speeds -> normalised PWM
  float vl = v - s.omega * HALF_BASE;
  float vr = v + s.omega * HALF_BASE;
  wheel(AIN1, AIN2, vl / V_MAX);   // both LEFT motors
  wheel(BIN1, BIN2, vr / V_MAX);   // both RIGHT motors
  delay(5);
}
