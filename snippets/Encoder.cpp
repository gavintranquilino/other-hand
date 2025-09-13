#include <Arduino.h>

// Rotary encoder pin definitions
#define ENCODER_SW  D9   // Switch pin
#define ENCODER_DT  D8   // Data pin
#define ENCODER_CLK D7   // Clock pin

// Variables for encoder state
volatile int encoderPos = 0;
volatile bool lastCLK = HIGH;
volatile bool lastDT = HIGH;

// Debouncing variables
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 2; // 2ms debounce

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  Serial.println("Rotary Encoder Test Starting...");
  
  // Configure encoder pins as inputs with pull-ups
  pinMode(ENCODER_CLK, INPUT_PULLUP);
  pinMode(ENCODER_DT, INPUT_PULLUP);
  pinMode(ENCODER_SW, INPUT_PULLUP);
  
  // Read initial states
  lastCLK = digitalRead(ENCODER_CLK);
  lastDT = digitalRead(ENCODER_DT);
  
  Serial.println("Encoder initialized. Rotate to see steps:");
  Serial.println("Position: 0");
}

void loop() {
  // Read current states
  bool currentCLK = digitalRead(ENCODER_CLK);
  bool currentDT = digitalRead(ENCODER_DT);
  
  // Check if CLK state changed (falling edge detection)
  if (currentCLK != lastCLK && currentCLK == LOW) {
    // Debouncing
    if (millis() - lastDebounceTime > debounceDelay) {
      // Determine rotation direction
      if (currentDT != currentCLK) {
        encoderPos++; // Clockwise
        Serial.print("Clockwise - Position: ");
        Serial.println(encoderPos);
      } else {
        encoderPos--; // Counter-clockwise
        Serial.print("Counter-clockwise - Position: ");
        Serial.println(encoderPos);
      }
      lastDebounceTime = millis();
    }
  }
  
  // Update last states
  lastCLK = currentCLK;
  lastDT = currentDT;
  
  // Check button press (optional - for testing)
  static bool lastButtonState = HIGH;
  bool currentButtonState = digitalRead(ENCODER_SW);
  
  if (currentButtonState != lastButtonState && currentButtonState == LOW) {
    Serial.println("Button pressed!");
    delay(50); // Simple button debounce
  }
  lastButtonState = currentButtonState;
}