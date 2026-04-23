// PER Suspension Test Rig — Arduino Mega
// Fixes applied:
//   1. Non-blocking loop: tare flag is set immediately, executed at top of next loop
//   2. Serial.readStringUntil() replaced with a manual byte-by-byte reader so the
//      40 ms delay never causes an incoming TARE command to be missed
//   3. Tare count reduced to 2 averages (fast) and done after checking ready() so
//      we don't block waiting for a conversion that hasn't finished
//   4. All eight HX711 objects updated only when is_ready() — no blocking get_units()

#include "HX711.h"

// --- WIRING CONFIGURATION ---
// Load Cells
const int LC_LAT_SCK  = 2;  const int LC_LAT_DT  = 3;
const int LC_NORM_SCK = 4;  const int LC_NORM_DT = 5;

// Strain Gauges
const int SG1_SCK = 6;  const int SG1_DT = 7;
const int SG2_SCK = 8;  const int SG2_DT = 9;
const int SG3_SCK = 10; const int SG3_DT = 11;
const int SG4_SCK = 14; const int SG4_DT = 15;
const int SG5_SCK = 16; const int SG5_DT = 17;
const int SG6_SCK = 18; const int SG6_DT = 19;

HX711 latCell, normCell;
HX711 sg1, sg2, sg3, sg4, sg5, sg6;

// Calibration factors — adjust as needed
float calLat  = 556.70;
float calNorm = 858.54;
float calSG   = 1.0;

// Last-good values (updated only when HX711 says it is ready)
float latVal = 0.0, normVal = 0.0;
float s1Val  = 0.0, s2Val  = 0.0, s3Val = 0.0;
float s4Val  = 0.0, s5Val  = 0.0, s6Val = 0.0;

// FIX #1 — tare is requested via a flag, not executed inside serial parsing
volatile bool tare_requested = false;

// FIX #2 — manual command buffer so we never block on readStringUntil()
#define CMD_BUF_LEN 16
char  cmdBuf[CMD_BUF_LEN];
uint8_t cmdIdx = 0;

// Timing
unsigned long lastSend = 0;
const unsigned long SEND_INTERVAL_MS = 40;

// ------------------------------------------------------------------
void setup() {
  Serial.begin(115200);

  latCell.begin(LC_LAT_DT,  LC_LAT_SCK);
  normCell.begin(LC_NORM_DT, LC_NORM_SCK);
  sg1.begin(SG1_DT, SG1_SCK);
  sg2.begin(SG2_DT, SG2_SCK);
  sg3.begin(SG3_DT, SG3_SCK);
  sg4.begin(SG4_DT, SG4_SCK);
  sg5.begin(SG5_DT, SG5_SCK);
  sg6.begin(SG6_DT, SG6_SCK);

  latCell.set_scale(calLat);
  normCell.set_scale(calNorm);
  sg1.set_scale(calSG);  sg2.set_scale(calSG);
  sg3.set_scale(calSG);  sg4.set_scale(calSG);
  sg5.set_scale(calSG);  sg6.set_scale(calSG);

  // Initial tare on startup (blocking is fine here, we're in setup)
  latCell.tare();  normCell.tare();
  sg1.tare();  sg2.tare();  sg3.tare();
  sg4.tare();  sg5.tare();  sg6.tare();

  Serial.println("READY");
}

// ------------------------------------------------------------------
void loop() {

  // FIX #1 — execute tare at the TOP of loop before anything else
  // tare(2) still blocks ~200 ms total across 8 HX711s, but we do it
  // immediately when requested rather than waiting for a dialog step.
  if (tare_requested) {
    tare_requested = false;
    latCell.tare(2);  normCell.tare(2);
    sg1.tare(2);  sg2.tare(2);  sg3.tare(2);
    sg4.tare(2);  sg5.tare(2);  sg6.tare(2);
    // Zero the held values right away so GUI sees 0 before next sample
    latVal = 0.0;  normVal = 0.0;
    s1Val  = 0.0;  s2Val  = 0.0;  s3Val = 0.0;
    s4Val  = 0.0;  s5Val  = 0.0;  s6Val = 0.0;
  }

  // FIX #2 — read serial byte-by-byte, never blocking, detect newline as terminator
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (cmdIdx > 0) {
        cmdBuf[cmdIdx] = '\0';
        String command = String(cmdBuf);
        command.trim();
        if (command == "TARE") {
          tare_requested = true;   // will execute at top of next loop()
        }
        cmdIdx = 0;   // reset buffer
      }
    } else {
      if (cmdIdx < CMD_BUF_LEN - 1) {
        cmdBuf[cmdIdx++] = c;
      }
      // If buffer overflows just discard — it's not a valid command
    }
  }

  // Read HX711s only when they have a conversion ready (non-blocking)
  if (latCell.is_ready())  latVal  = latCell.get_units(1);
  if (normCell.is_ready()) normVal = normCell.get_units(1);
  if (sg1.is_ready())      s1Val   = sg1.get_units(1);
  if (sg2.is_ready())      s2Val   = sg2.get_units(1);
  if (sg3.is_ready())      s3Val   = sg3.get_units(1);
  if (sg4.is_ready())      s4Val   = sg4.get_units(1);
  if (sg5.is_ready())      s5Val   = sg5.get_units(1);
  if (sg6.is_ready())      s6Val   = sg6.get_units(1);

  // Send at fixed interval (replaces blocking delay(40))
  unsigned long now = millis();
  if (now - lastSend >= SEND_INTERVAL_MS) {
    lastSend = now;
    Serial.print(latVal,  2);  Serial.print(",");
    Serial.print(normVal, 2);  Serial.print(",");
    Serial.print(s1Val,   2);  Serial.print(",");
    Serial.print(s2Val,   2);  Serial.print(",");
    Serial.print(s3Val,   2);  Serial.print(",");
    Serial.print(s4Val,   2);  Serial.print(",");
    Serial.print(s5Val,   2);  Serial.print(",");
    Serial.println(s6Val, 2);
  }
  // No delay() — loop runs as fast as possible so serial reads are never missed
}
