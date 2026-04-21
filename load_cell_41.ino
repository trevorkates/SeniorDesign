#include "HX711.h"

// --- WIRING CONFIGURATION ---
// Load Cell A (Scale 1)
const int DOUT1 = 3;
const int SCK1  = 2;

// Load Cell B (Scale 2) - Pins 4 and 5, No Shared Clock
const int DOUT2 = 5;
const int SCK2  = 4;

HX711 scale1;
HX711 scale2;

// --- UTM CALIBRATION FACTORS (From your plots) ---
float cal1 = 556.70; 
float cal2 = 858.54; 

void setup() {
  // Python GUI requires 115200 baud
  Serial.begin(115200);
  
  scale1.begin(DOUT1, SCK1);
  scale2.begin(DOUT2, SCK2);

  scale1.set_scale(cal1);
  scale2.set_scale(cal2);

  // Initial Zeroing
  scale1.tare();
  scale2.tare();
}

void loop() {
  // Logic: Wait for both to be ready so the Python CSV split stays in sync
  if (scale1.is_ready() && scale2.is_ready()) {
    float val1 = scale1.get_units(1);
    float val2 = scale2.get_units(1);
    
    // Output Format: A,B (e.g., 105.20,98.45)
    Serial.print(val1, 2);
    Serial.print(",");
    Serial.println(val2, 2);
  }

  // GUI Command Listener
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "TARE") {
      scale1.tare();
      scale2.tare();
    } 
    // Fix: Using .toFloat() for Arduino String class
    else if (command.startsWith("SET_CAL1:")) {
      cal1 = command.substring(9).toFloat();
      scale1.set_scale(cal1);
    }
    else if (command.startsWith("SET_CAL2:")) {
      cal2 = command.substring(9).toFloat();
      scale2.set_scale(cal2);
    }
  }

  delay(30); 
}