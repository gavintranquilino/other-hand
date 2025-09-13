#include <Arduino.h>
#include <FastLED.h>

// LED strip configuration
#define LED_PIN D10         // Pin where the LED strip is connected
#define NUM_LEDS 3          // Number of LEDs in the strip
#define LED_TYPE WS2812     // Type of LED strip
#define COLOR_ORDER GRB     // Color order for WS2812

// Create LED array
CRGB leds[NUM_LEDS];

// Rainbow variables
uint8_t hue = 0;           // Starting hue value
uint8_t brightness = 100;   // LED brightness (0-255)

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  Serial.println("FastLED WS2812 Rainbow Test Starting...");
  
  // Initialize FastLED
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.setBrightness(brightness);
  
  // Clear all LEDs
  FastLED.clear();
  FastLED.show();
  
  Serial.println("FastLED initialized successfully!");
}

void loop() {
  // Create rainbow effect
  for(int i = 0; i < NUM_LEDS; i++) {
    // Each LED gets a different hue, spaced evenly across the rainbow
    leds[i] = CHSV(hue + (i * 85), 255, 255); // 85 = 256/3 for even spacing
  }
  
  // Update the strip
  FastLED.show();
  
  // Increment hue for smooth rainbow animation
  hue += 2; // Adjust this value to change speed (higher = faster)
  
  // Small delay for smooth animation
  delay(50);
  
  // Print status every 100 cycles
  static int counter = 0;
  if(counter % 100 == 0) {
    Serial.print("Rainbow cycling... Hue: ");
    Serial.println(hue);
  }
  counter++;
}