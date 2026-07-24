/*
 * drone.ino — per-drone flight controller for the ESP32 brushed micro-quad swarm.
 *
 *   MPU-6050 (I2C) -> complementary-filter attitude -> angle+rate PID ->
 *   X-mix -> 4 brushed motors (LEDC PWM into SI2302 MOSFET gates).
 *   Setpoints (arm / throttle / pitch / roll / yaw-rate) arrive over ESP-NOW
 *   from the coordinator bridge. Failsafe disarms on link loss.
 *
 * ⚠️  UNTESTED ON HARDWARE. This is reference firmware to build on. Bench-test
 *     with PROPS OFF and the craft tethered. Verify each motor's spin direction
 *     and the SIGN of every axis before you ever fit props. PID gains below are
 *     starting points — expect to tune them.
 *
 * Board: any ESP32 / ESP32-C3/S3 (Arduino core). Set the 4 motor pins + I2C pins
 *        for your board. Flash one drone at a time and note its MAC (printed at
 *        boot) — the coordinator addresses each drone by MAC.
 */
#include <Wire.h>
#include <WiFi.h>
#include <esp_now.h>

// ---------------- board pins (EDIT for your board) ----------------
static const int MOTOR_PIN[4] = {2, 3, 4, 5};   // M1 FR, M2 RR, M3 RL, M4 FL
static const int I2C_SDA = 6, I2C_SCL = 7;
static const int MPU_ADDR = 0x68;

// ---------------- control constants ----------------
static const int   PWM_FREQ = 20000, PWM_RES = 10;      // 20 kHz, 0..1023 duty
static const int   PWM_MAX  = (1 << PWM_RES) - 1;
static const float LOOP_HZ  = 500.0f;                    // control-loop rate
static const uint32_t FAILSAFE_MS = 300;                 // disarm if no packet
static const float MAX_TILT_DEG = 25.0f;                 // setpoint clamp
static const float IDLE_THR = 0.06f;                     // spin-to-idle when armed

// angle PID (pitch/roll): P on angle error, D on gyro rate. Yaw: P on rate.
static float Kp_ang = 0.010f, Kd_ang = 0.0016f, Ki_ang = 0.0008f;
static float Kp_yaw = 0.004f;
static float I_LIMIT = 0.15f;

// ---------------- ESP-NOW packet (must match the bridge) ----------------
typedef struct __attribute__((packed)) {
  uint8_t  armed;      // 0/1
  float    throttle;   // 0..1
  float    pitch_sp;   // deg (+nose up)
  float    roll_sp;    // deg (+right down)
  float    yaw_rate_sp;// deg/s
} Setpoint;

volatile Setpoint sp = {0, 0, 0, 0, 0};
volatile uint32_t lastRxMs = 0;

// ---------------- state ----------------
float pitch = 0, roll = 0;            // deg (complementary filter)
float gx_bias = 0, gy_bias = 0, gz_bias = 0;
float iPitch = 0, iRoll = 0;
uint32_t lastLoopUs = 0;

// ---------------- MPU-6050 ----------------
void mpuWrite(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(MPU_ADDR); Wire.write(reg); Wire.write(val); Wire.endTransmission();
}
void mpuInit() {
  Wire.begin(I2C_SDA, I2C_SCL, 400000);
  mpuWrite(0x6B, 0x00);   // wake
  mpuWrite(0x1B, 0x00);   // gyro ±250 dps
  mpuWrite(0x1C, 0x00);   // accel ±2 g
  mpuWrite(0x1A, 0x03);   // DLPF ~44 Hz
}
void mpuRead(float &ax, float &ay, float &az, float &gxr, float &gyr, float &gzr) {
  Wire.beginTransmission(MPU_ADDR); Wire.write(0x3B); Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 14, true);
  int16_t r[7];
  for (int i = 0; i < 7; i++) r[i] = (Wire.read() << 8) | Wire.read();
  ax = r[0] / 16384.0f; ay = r[1] / 16384.0f; az = r[2] / 16384.0f;   // g
  gxr = r[4] / 131.0f - gx_bias;                                       // deg/s
  gyr = r[5] / 131.0f - gy_bias;
  gzr = r[6] / 131.0f - gz_bias;
}
void gyroCalibrate() {
  float sx = 0, sy = 0, sz = 0; const int N = 800;
  for (int i = 0; i < N; i++) {
    float ax, ay, az, gxr, gyr, gzr; mpuRead(ax, ay, az, gxr, gyr, gzr);
    sx += gxr; sy += gyr; sz += gzr; delay(2);
  }
  gx_bias = sx / N; gy_bias = sy / N; gz_bias = sz / N;
}

// ---------------- ESP-NOW ----------------
void onRecv(const esp_now_recv_info_t *info, const uint8_t *data, int len) {
  if (len == sizeof(Setpoint)) { memcpy((void *)&sp, data, sizeof(Setpoint)); lastRxMs = millis(); }
}

// ---------------- motors ----------------
void writeMotor(int i, float u) {                 // u in 0..1
  u = u < 0 ? 0 : (u > 1 ? 1 : u);
  ledcWrite(MOTOR_PIN[i], (uint32_t)(u * PWM_MAX));
}
void motorsOff() { for (int i = 0; i < 4; i++) writeMotor(i, 0); }

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < 4; i++) { ledcAttach(MOTOR_PIN[i], PWM_FREQ, PWM_RES); writeMotor(i, 0); }
  mpuInit(); delay(100); gyroCalibrate();
  WiFi.mode(WIFI_STA);
  Serial.print("Drone MAC (add to coordinator): "); Serial.println(WiFi.macAddress());
  if (esp_now_init() != ESP_OK) { Serial.println("ESP-NOW init failed"); }
  esp_now_register_recv_cb(onRecv);
  lastLoopUs = micros();
}

void loop() {
  // fixed-rate control loop
  uint32_t now = micros();
  float dt = (now - lastLoopUs) * 1e-6f;
  if (dt < 1.0f / LOOP_HZ) return;
  lastLoopUs = now;

  float ax, ay, az, gxr, gyr, gzr; mpuRead(ax, ay, az, gxr, gyr, gzr);
  // accel angles (deg) and complementary filter
  float pitchAcc = atan2f(-ax, sqrtf(ay * ay + az * az)) * 57.2958f;
  float rollAcc  = atan2f(ay, az) * 57.2958f;
  pitch = 0.98f * (pitch + gyr * dt) + 0.02f * pitchAcc;
  roll  = 0.98f * (roll  + gxr * dt) + 0.02f * rollAcc;

  bool armed = sp.armed && (millis() - lastRxMs < FAILSAFE_MS);   // link-loss failsafe
  if (!armed || sp.throttle < IDLE_THR) { motorsOff(); iPitch = iRoll = 0; return; }

  // setpoint clamp
  float pSp = constrain(sp.pitch_sp, -MAX_TILT_DEG, MAX_TILT_DEG);
  float rSp = constrain(sp.roll_sp,  -MAX_TILT_DEG, MAX_TILT_DEG);

  // angle PID -> axis commands
  float ePitch = pSp - pitch, eRoll = rSp - roll;
  iPitch = constrain(iPitch + ePitch * dt, -I_LIMIT / Ki_ang, I_LIMIT / Ki_ang);
  iRoll  = constrain(iRoll  + eRoll  * dt, -I_LIMIT / Ki_ang, I_LIMIT / Ki_ang);
  float pitchCmd = Kp_ang * ePitch + Ki_ang * iPitch - Kd_ang * gyr;
  float rollCmd  = Kp_ang * eRoll  + Ki_ang * iRoll  - Kd_ang * gxr;
  float yawCmd   = Kp_yaw * (sp.yaw_rate_sp - gzr);

  // X-mix (verify signs & motor order with props OFF)
  float thr = sp.throttle;
  writeMotor(0, thr - pitchCmd + rollCmd - yawCmd);   // M1 front-right
  writeMotor(1, thr + pitchCmd + rollCmd + yawCmd);   // M2 rear-right
  writeMotor(2, thr + pitchCmd - rollCmd - yawCmd);   // M3 rear-left
  writeMotor(3, thr - pitchCmd - rollCmd + yawCmd);   // M4 front-left
}
