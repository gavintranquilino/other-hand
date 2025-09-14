#include <Arduino.h>
#include <FastLED.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <WiFi.h>

BLEServer* pServer = NULL;
BLECharacteristic* pCharacteristic = NULL;
bool deviceConnected = false;
bool oldDeviceConnected = false;

#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
      deviceConnected = true;
      Serial.println();
      Serial.println("*** BLE CLIENT CONNECTED! ***");
      Serial.println("Device is now paired and ready for communication");
    };

    void onDisconnect(BLEServer* pServer) {
      deviceConnected = false;
      Serial.println();
      Serial.println("*** BLE CLIENT DISCONNECTED ***");
      Serial.println("Restarting advertising in 500ms...");
      delay(500); // give the bluetooth stack the chance to get things ready
      pServer->startAdvertising(); // restart advertising
      Serial.println("BLE Advertising restarted - device discoverable again");
      Serial.println("Look for 'Other Hand HTN25' in Bluetooth settings");
    }
};


// Rotary encoder pin definitions
#define ENCODER_SW  D9   // Switch pin
#define ENCODER_DT  D8   // Data pin
#define ENCODER_CLK D7   // Clock pin

// LED strip configuration
#define LED_PIN D10         // Pin where the LED strip is connected
#define NUM_LEDS 3          // Number of LEDs in the strip
#define LED_TYPE WS2812     // Type of LED strip
#define COLOR_ORDER GRB     // Color order for WS2812
#define LED_STATES 5       // Number of LED states (e.g., off, red, green, blue)

#define LED_0 0
#define LED_1 1
#define LED_2 2

#define BUTTON D1


CRGB leds[NUM_LEDS];

// Rainbow variables
uint8_t hue = 0;           // Starting hue value
uint8_t brightness = 100;   // LED brightness (0-255)


// Variables for encoder state
volatile int encoderPos = 0;
volatile bool lastCLK = HIGH;
volatile bool lastDT = HIGH;

// Debouncing variables
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 2; // 2ms debounce

// Rollovers logic
uint8_t maxPos = 7;
uint8_t minPos = 0;
uint8_t ledActive = 0;

// Setting all the CHSV Values

CRGB whiteLEDs = CRGB(255, 255, 255);
CRGB redLEDs = CRGB(255, 0, 0);
CRGB greenLEDs = CRGB(0, 255, 0);
CRGB blueLEDs = CRGB(0, 0, 255);
CRGB offLEDs = CRGB(0, 0, 0);
CRGB orangeLEDs = CRGB(255, 165, 0);


void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  delay(2000); // Give time for Serial Monitor to connect
  Serial.println("=== ESP32-S3 BLE Device Starting ===");
  Serial.println("Rotary Encoder Test Starting...");
  
  // Configure encoder pins as inputs with pull-ups
  pinMode(ENCODER_CLK, INPUT_PULLUP);
  pinMode(ENCODER_DT, INPUT_PULLUP);
  pinMode(ENCODER_SW, INPUT_PULLUP);
  
  pinMode(BUTTON, INPUT_PULLUP);
  
  // Read initial states
  lastCLK = digitalRead(ENCODER_CLK);
  lastDT = digitalRead(ENCODER_DT);
  
  Serial.println("Encoder initialized. Rotate to see steps:");
  Serial.println("Position: 0");

  // Initializing FastLED
  Serial.println("Initializing LED strip...");
  // Initializing FastLED
  Serial.println("Initializing LED strip...");
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.setBrightness(brightness);

  // Clear all LEDs
  FastLED.clear();
  FastLED.show();
  Serial.println("LED strip initialized and cleared");

  // Setting up BLE
  Serial.println("=== Starting BLE Setup ===");

  // Initialize BLE Device
  Serial.println("Initializing BLE Device with name: 'Other Hand HTN25'");
  BLEDevice::init("Other Hand HTN25");
  Serial.println("BLE Device initialized successfully");
  
  // Display MAC address
  String macAddress = BLEDevice::getAddress().toString().c_str();
  Serial.printf("ESP32 MAC Address: %s\n", macAddress.c_str());
  Serial.printf("BLE Address: %s\n", BLEDevice::getAddress().toString().c_str());
  Serial.printf("WiFi MAC Address: %s\n", WiFi.macAddress().c_str());
  
  Serial.println("Creating BLE Server...");
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());
  Serial.println("BLE Server created with callbacks");

  Serial.println("Creating BLE Service...");
  BLEService *pService = pServer->createService(SERVICE_UUID);
  Serial.printf("BLE Service created with UUID: %s\n", SERVICE_UUID);

  Serial.println("Creating BLE Characteristic...");
  pCharacteristic = pService->createCharacteristic(
                      CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_READ |
                      BLECharacteristic::PROPERTY_WRITE |
                      BLECharacteristic::PROPERTY_NOTIFY
                    );
  
  // Add descriptor for notifications
  pCharacteristic->addDescriptor(new BLE2902());
  
  Serial.printf("BLE Characteristic created with UUID: %s\n", CHARACTERISTIC_UUID);

  Serial.println("Starting BLE Service...");
  pService->start();
  Serial.println("BLE Service started successfully");
  
  // Configure advertising
  Serial.println("Configuring BLE Advertising...");
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinPreferred(0x20);  // Increase connection interval for stability
  pAdvertising->setMaxPreferred(0x40);  // Set max interval
  Serial.println("BLE Advertising configured");
  
  // Start advertising
  Serial.println("Starting BLE Advertising...");
  BLEDevice::startAdvertising();
  
  // Start advertising
  Serial.println("Starting BLE Advertising...");
  BLEDevice::startAdvertising();
  
  Serial.println("=== BLE SETUP COMPLETE ===");
  Serial.println("Device Name: 'Other Hand HTN25'");
  Serial.printf("Service UUID: %s\n", SERVICE_UUID);
  Serial.printf("Characteristic UUID: %s\n", CHARACTERISTIC_UUID);
  Serial.println("Device is now DISCOVERABLE!");
  Serial.println("Look for 'Other Hand HTN25' in your Bluetooth settings");
  Serial.println("==========================");
  
  Serial.println("Waiting for a client connection to notify...");

  leds[0] = blueLEDs;
  leds[1] = greenLEDs;
  leds[2] = redLEDs;
  FastLED.show();
  Serial.println("LEDs set to blue/green/red - waiting for connection");

  // Non-blocking connection waiting with periodic status updates
  unsigned long lastStatusUpdate = 0;
  unsigned long statusInterval = 5000; // 5 seconds
  int dotCount = 0;
  
  Serial.println("Device is actively advertising...");
  Serial.println("You should now be able to see 'Other Hand HTN25' in:");
  Serial.println("- Windows Bluetooth settings");
  Serial.println("- BLE scanner apps");
  Serial.println("- Chrome://bluetooth-internals");
  Serial.println();
  
  while (!deviceConnected) {
    delay(500);
    Serial.print(".");
    dotCount++;
    
    if (millis() - lastStatusUpdate > statusInterval) {
      Serial.println();
      Serial.printf("Still advertising as 'Other Hand HTN25' (%d seconds elapsed)\n", (millis() / 1000));
      Serial.println("If you can't see the device, try:");
      Serial.println("1. Download 'Bluetooth LE Explorer' from Microsoft Store");
      Serial.println("2. Reset your Windows Bluetooth stack");
      Serial.println("3. Try from a smartphone with BLE scanner app");
      Serial.println("4. Check chrome://bluetooth-internals in Chrome browser");
      Serial.println("Restarting advertising to ensure visibility...");
      BLEDevice::startAdvertising();
      Serial.println();
      lastStatusUpdate = millis();
      dotCount = 0;
    }
  }

  leds[0] = offLEDs;
  leds[1] = offLEDs;
  leds[2] = offLEDs;
  FastLED.show();


  Serial.println();
  Serial.println("=== CLIENT CONNECTED! ===");
  leds[0] = whiteLEDs;
  leds[1] = whiteLEDs;
  leds[2] = whiteLEDs;
  FastLED.show();
  Serial.println("LEDs set to white - connection established");
  Serial.println("Device ready for operation!");
  Serial.println("=========================");

  delay(2000);

  leds[0] = offLEDs;
  leds[1] = offLEDs;
  leds[2] = offLEDs;
  FastLED.show();





}

void loop() {

  // Check for disconnection
  if (!deviceConnected && oldDeviceConnected) {
    Serial.println("*** CLIENT DISCONNECTED! ***");
    oldDeviceConnected = deviceConnected;
  }
  
  // Check for new connection
  if (deviceConnected && !oldDeviceConnected) {
    Serial.println("*** CLIENT CONNECTED! ***");
    oldDeviceConnected = deviceConnected;
  }

  // DISCONNECT CHECK - Block all actions if not connected
  if (!deviceConnected) {
    // Set all LEDs to orange to indicate disconnected state

    encoderPos = 0; // Reset encoder position
    ledActive = 0; // Reset LED state

    leds[LED_0] = orangeLEDs;
    leds[LED_1] = orangeLEDs;
    leds[LED_2] = orangeLEDs;
    FastLED.show();
    
    // Actively try to reconnect by ensuring advertising is running
    static unsigned long lastReconnectAttempt = 0;
    if (millis() - lastReconnectAttempt > 5000) { // Try every 5 seconds
      Serial.println("🔄 Attempting reconnection - restarting advertising...");
      BLEDevice::startAdvertising();
      Serial.println("📡 BLE Advertising active - device discoverable");
      lastReconnectAttempt = millis();
    }

    
    
    // Block all other functionality - just wait for reconnection
    delay(100); // Small delay to prevent excessive loop execution
    return; // Exit loop early, skip all encoder and button processing
  }

  // NORMAL OPERATION - Only execute when connected

  // Updating HUE Values

  CHSV rainbowLEDs = CHSV(hue, 255, 255);

  if (ledActive == 4) {

    hue++;
    
    if (hue > 255) {
      hue = 0;
    }

  } else {
    hue = 0;
  }

  // Read current states
  bool currentCLK = digitalRead(ENCODER_CLK);
  bool currentDT = digitalRead(ENCODER_DT);
  
  
  // Check if CLK state changed (falling edge detection)
  if (currentCLK != lastCLK && currentCLK == LOW) {
    // Debouncing
    if (millis() - lastDebounceTime > debounceDelay) {
      // Determine rotation direction
      if (currentDT == currentCLK) { // Change from != to == to determine direction
        encoderPos++; // Clockwise
        // Serial.print("Clockwise - Position: ");
        // Serial.println(encoderPos);
      } else {
        encoderPos--; // Counter-clockwise
        // Serial.print("Counter-clockwise - Position: ");
        // Serial.println(encoderPos);
      }
      lastDebounceTime = millis();
    }
  }

  // Rolling over the position of encoder pos, 

  if (encoderPos > maxPos) {
    encoderPos = minPos;
  } else if (encoderPos < minPos) {
    encoderPos = maxPos;
  }

  // Serial.print("Current Position of Encoder: ");
  // Serial.println(encoderPos);

  // Case Statement for each position

  switch (encoderPos) {

    // NUMBER 0

    case 0:
      leds[LED_0] = offLEDs;
      leds[LED_1] = offLEDs;
      leds[LED_2] = offLEDs;
      FastLED.show();
      break;

    // NUMBER 1
    
    case 1:
      switch (ledActive) {
        

        case 0:
          leds[LED_0] = whiteLEDs;
          leds[LED_1] = offLEDs;
          leds[LED_2] = offLEDs;
          FastLED.show();

          break;

        case 1:
          leds[LED_0] = redLEDs;
          leds[LED_1] = offLEDs;
          leds[LED_2] = offLEDs;
          FastLED.show();

          break;
        
        case 2:
          leds[LED_0] = greenLEDs;
          leds[LED_1] = offLEDs;
          leds[LED_2] = offLEDs;
          FastLED.show();
          break;

        case 3:
          leds[LED_0] = blueLEDs;
          leds[LED_1] = offLEDs;
          leds[LED_2] = offLEDs;
          FastLED.show();
          break;

        case 4:

          
          // Each LED gets a different hue, spaced evenly across the rainbow
          leds[LED_0] = rainbowLEDs;
          leds[LED_1] = offLEDs;
          leds[LED_2] = offLEDs;
          

          FastLED.show();

          break;


        default:
          break;

      }
      break;

    
    // NUMBER 2

    case 2:
      switch (ledActive) {
        

        case 0:
          leds[LED_0] = offLEDs;
          leds[LED_1] = whiteLEDs;
          leds[LED_2] = offLEDs;
          FastLED.show();

          break;
        

        case 1:
          leds[LED_0] = offLEDs;
          leds[LED_1] = redLEDs;
          leds[LED_2] = offLEDs;
          FastLED.show();

          break;

        case 2:
          leds[LED_0] = offLEDs;
          leds[LED_1] = greenLEDs;
          leds[LED_2] = offLEDs;
          FastLED.show();
          break;
        
        case 3:
          leds[LED_0] = offLEDs;
          leds[LED_1] = blueLEDs;
          leds[LED_2] = offLEDs;
          FastLED.show();
          break;

        case 4:
          // Each LED gets a different hue, spaced evenly across the rainbow
          leds[LED_0] = offLEDs;
          leds[LED_1] = rainbowLEDs;
          leds[LED_2] = offLEDs;
          

          FastLED.show();

          break;

        default:
          break;

      }
      break;

    // NUMBER 3

    case 3:
      switch (ledActive) {
        

        case 0:
          leds[LED_0] = whiteLEDs;
          leds[LED_1] = whiteLEDs;
          leds[LED_2] = offLEDs;
          FastLED.show();

          break;

        case 1:
          leds[LED_0] = redLEDs;
          leds[LED_1] = redLEDs;
          leds[LED_2] = offLEDs;
          FastLED.show();

          break;

        case 2:
          leds[LED_0] = greenLEDs;
          leds[LED_1] = greenLEDs;
          leds[LED_2] = offLEDs;
          FastLED.show();
          break;

        case 3:
          leds[LED_0] = blueLEDs;
          leds[LED_1] = blueLEDs;
          leds[LED_2] = offLEDs;
          FastLED.show();
          break;

        case 4:
          // Each LED gets a different hue, spaced evenly across the rainbow
          leds[LED_0] = rainbowLEDs;
          leds[LED_1] = rainbowLEDs;
          leds[LED_2] = offLEDs;
          

          FastLED.show();

          break;

        default:
          break;

      }
      break;

    // NUMBER 4


    case 4:

      switch (ledActive) {
        

        case 0:
          leds[LED_0] = offLEDs;
          leds[LED_1] = offLEDs;
          leds[LED_2] = whiteLEDs;
          FastLED.show();

          break;

        case 1:
          leds[LED_0] = offLEDs;
          leds[LED_1] = offLEDs;
          leds[LED_2] = redLEDs;
          FastLED.show();

          break;

        case 2:
          leds[LED_0] = offLEDs;
          leds[LED_1] = offLEDs;
          leds[LED_2] = greenLEDs;
          FastLED.show();
          break;  
        
        case 3:
          leds[LED_0] = offLEDs;
          leds[LED_1] = offLEDs;
          leds[LED_2] = blueLEDs;
          FastLED.show();
          break;

        case 4:
          // Each LED gets a different hue, spaced evenly across the rainbow
          leds[LED_0] = offLEDs;
          leds[LED_1] = offLEDs;
          leds[LED_2] = rainbowLEDs;
          

          FastLED.show();

          break;  
        

        default:
          break;

      }
      break;

    // NUMBER 5


    case 5:

      switch (ledActive) {
        

        case 0:
          leds[LED_0] = whiteLEDs;
          leds[LED_1] = offLEDs;
          leds[LED_2] = whiteLEDs;
          FastLED.show();

          break;

        case 1:
          leds[LED_0] = redLEDs;
          leds[LED_1] = offLEDs;
          leds[LED_2] = redLEDs;
          FastLED.show();

          break;

        case 2:
          leds[LED_0] = greenLEDs;
          leds[LED_1] = offLEDs;
          leds[LED_2] = greenLEDs;
          FastLED.show();
          break;

        case 3:
          leds[LED_0] = blueLEDs;
          leds[LED_1] = offLEDs;
          leds[LED_2] = blueLEDs;
          FastLED.show();
          break;

        case 4:
          // Each LED gets a different hue, spaced evenly across the rainbow
          leds[LED_0] = rainbowLEDs;
          leds[LED_1] = offLEDs;
          leds[LED_2] = rainbowLEDs;
          

          FastLED.show();

          break;  

        default:
          break;

      }
      break;

    // NUMBER 6

    case 6:

      switch (ledActive) {
        

        case 0:
          leds[LED_0] = offLEDs;
          leds[LED_1] = whiteLEDs;
          leds[LED_2] = whiteLEDs;
          FastLED.show();

          break;

        case 1:
          leds[LED_0] = offLEDs;
          leds[LED_1] = redLEDs;
          leds[LED_2] = redLEDs;
          FastLED.show();

          break;

        case 2:
          leds[LED_0] = offLEDs;
          leds[LED_1] = greenLEDs;
          leds[LED_2] = greenLEDs;
          FastLED.show();
          break;

        case 3:
          leds[LED_0] = offLEDs;
          leds[LED_1] = blueLEDs;
          leds[LED_2] = blueLEDs;
          FastLED.show();
          break;
        
        case 4:
          // Each LED gets a different hue, spaced evenly across the rainbow
          leds[LED_0] = offLEDs;
          leds[LED_1] = rainbowLEDs;
          leds[LED_2] = rainbowLEDs;
          

          FastLED.show();

          break;

        default:
          break;

      }
      break;

    // NUMBER 7
    case 7:

      switch (ledActive) {
        

        case 0:
          leds[LED_0] = whiteLEDs;
          leds[LED_1] = whiteLEDs;
          leds[LED_2] = whiteLEDs;
          FastLED.show();

          break;

        case 1:
          leds[LED_0] = redLEDs;
          leds[LED_1] = redLEDs;
          leds[LED_2] = redLEDs;
          FastLED.show();

          break;

        case 2:
          leds[LED_0] = greenLEDs;
          leds[LED_1] = greenLEDs;
          leds[LED_2] = greenLEDs;
          FastLED.show();
          break;

        case 3:
          leds[LED_0] = blueLEDs;
          leds[LED_1] = blueLEDs;
          leds[LED_2] = blueLEDs;
          FastLED.show();
          break;

        case 4:
          // Each LED gets a different hue, spaced evenly across the rainbow
          leds[LED_0] = rainbowLEDs;
          leds[LED_1] = rainbowLEDs;
          leds[LED_2] = rainbowLEDs;
          

          FastLED.show();

          break;  

        default:
          break;

      }
      break;
    default:
      break;
  }


  
  // Update last states
  lastCLK = currentCLK;
  lastDT = currentDT;
  
  // Check button press (optional - for testing)
  static bool lastButtonState = HIGH;
  bool currentButtonState = digitalRead(ENCODER_SW);
  
  if (currentButtonState != lastButtonState && currentButtonState == LOW) {

    // Increment the LED Active Variable 

    ledActive++;

    // If LEDActive = 0, disable all LEDs

    // Rolling over the ledActive parameter

    if (ledActive > (LED_STATES-1)) {
      ledActive = 0;
    }

    Serial.println("Button pressed!");
    Serial.print(ledActive);
    delay(50); // Simple button debounce
  }


  static bool lastButtonStateSending = HIGH;
  bool currentButtonStateSending = digitalRead(BUTTON);

  Serial.print("Button state: ");
  Serial.println(currentButtonStateSending);

  if (currentButtonStateSending != lastButtonStateSending && currentButtonStateSending == LOW) {
    // Button pressed - send encoderPos and button state (1)

    if (deviceConnected) {
      char message[16];
      snprintf(message, sizeof(message), "%d,%d", encoderPos, 1);
      pCharacteristic->setValue((uint8_t*)message, strlen(message));
      pCharacteristic->notify();
      Serial.print("Sent via BLE - Position: ");
      Serial.print(encoderPos);
      Serial.println(", Button: PRESSED (1)");
    } else {
      Serial.println("Cannot send position - no device connected");
    }

    Serial.println("Send Button pressed!");
    delay(50); // Simple button debounce
    
  }

  if (currentButtonStateSending != lastButtonStateSending && currentButtonStateSending == HIGH) {
    // Button released - send encoderPos and button state (0)

    if (deviceConnected) {
      char message[16];
      snprintf(message, sizeof(message), "%d,%d", encoderPos, 0);
      pCharacteristic->setValue((uint8_t*)message, strlen(message));
      pCharacteristic->notify();
      Serial.print("Sent via BLE - Position: ");
      Serial.print(encoderPos);
      Serial.println(", Button: RELEASED (0)");
    } else {
      Serial.println("Cannot send position - no device connected");
    }

    Serial.println("Send Button released!");
    delay(50); // Simple button debounce
    
  }


  lastButtonState = currentButtonState;
  lastButtonStateSending = currentButtonStateSending;
}