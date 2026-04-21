#include "HX711.h"

// --- WIRING CONFIGURATION (From Photo) ---
// Load Cells
const int LC_LAT_SCK = 2;  const int LC_LAT_DT = 3;
const int LC_NORM_SCK = 4; const int LC_NORM_DT = 5;

// Strain Gauges
const int SG1_SCK = 6;  const int SG1_DT = 7;
const int SG2_SCK = 8;  const int SG2_DT = 9;
const int SG3_SCK = 10; const int SG3_DT = 11;
const int SG4_SCK = 14; const int SG4_DT = 15;
const int SG5_SCK = 16; const int SG5_DT = 17;
const int SG6_SCK = 18; const int SG6_DT = 19;

// Initialize Objects
HX711 latCell, normCell;
HX711 sg1, sg2, sg3, sg4, sg5, sg6;

// --- CALIBRATION FACTORS ---
float calLat = 556.70; 
float calNorm = 858.54; 
float calSG = 1.0; // Set to 1.0 for raw bit reading until calibrated

void setup() {
  Serial.begin(115200); // GUI requires 115200 baud

  // Initialize all 8 chips
  latCell.begin(LC_LAT_DT, LC_LAT_SCK);
  normCell.begin(LC_NORM_DT, LC_NORM_SCK);
  sg1.begin(SG1_DT, SG1_SCK);
  sg2.begin(SG2_DT, SG2_SCK);
  sg3.begin(SG3_DT, SG3_SCK);
  sg4.begin(SG4_DT, SG4_SCK);
  sg5.begin(SG5_DT, SG5_SCK);
  sg6.begin(SG6_DT, SG6_SCK);

  // Apply calibration factors
  latCell.set_scale(calLat);
  normCell.set_scale(calNorm);
  sg1.set_scale(calSG);
  sg2.set_scale(calSG);
  sg3.set_scale(calSG);
  sg4.set_scale(calSG);
  sg5.set_scale(calSG);
  sg6.set_scale(calSG);

  // Initial Tare (Zeroing)
  latCell.tare(); normCell.tare();
  sg1.tare(); sg2.tare(); sg3.tare();
  sg4.tare(); sg5.tare(); sg6.tare();
}

void loop() {
  // Read each sensor independently. Default to 0.0 if not ready.
  float latVal  = (latCell.is_ready())  ? latCell.get_units(1)  : 0.0;
  float normVal = (normCell.is_ready()) ? normCell.get_units(1) : 0.0;
  float s1Val   = (sg1.is_ready())      ? sg1.get_units(1)      : 0.0;
  float s2Val   = (sg2.is_ready())      ? sg2.get_units(1)      : 0.0;
  float s3Val   = (sg3.is_ready())      ? sg3.get_units(1)      : 0.0;
  float s4Val   = (sg4.is_ready())      ? sg4.get_units(1)      : 0.0;
  float s5Val   = (sg5.is_ready())      ? sg5.get_units(1)      : 0.0;
  float s6Val   = (sg6.is_ready())      ? sg6.get_units(1)      : 0.0;

  // Output Format: Lateral, Normal, SG1, SG2, SG3, SG4, SG5, SG6
  // This strict 8-column rule is required for the Python split(",") logic
  Serial.print(latVal, 2);  Serial.print(",");
  Serial.print(normVal, 2); Serial.print(",");
  Serial.print(s1Val, 2);   Serial.print(",");
  Serial.print(s2Val, 2);   Serial.print(",");
  Serial.print(s3Val, 2);   Serial.print(",");
  Serial.print(s4Val, 2);   Serial.print(",");
  Serial.print(s5Val, 2);   Serial.print(",");
  Serial.println(s6Val, 2);

  // Command Listener for "ZERO SYSTEM" button
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    if (command == "TARE") {
      latCell.tare(); normCell.tare();
      sg1.tare(); sg2.tare(); sg3.tare();
      sg4.tare(); sg5.tare(); sg6.tare();
    }
  }

  delay(40); // Balanced for GUI responsiveness
}