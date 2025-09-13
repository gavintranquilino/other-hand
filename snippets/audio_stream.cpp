#include <Arduino.h>
#include <driver/i2s.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>

// I2S pin definitions for ESP32-S3 - Your connections
#define I2S_SCK_PIN   D2   // BCLK (Bit Clock) - connected to pin 2
#define I2S_SD_PIN    D3   // DOUT (Data Out) - connected to pin 3  
#define I2S_WS_PIN    D4   // LRCL (Left/Right Clock) - connected to pin 4
#define I2S_SEL_PIN   D5   // SEL (Channel Select) - connected to pin 5

// I2S configuration
#define I2S_PORT      I2S_NUM_0
#define I2S_SAMPLE_RATE 16000
#define I2S_SAMPLE_BITS 32
#define I2S_CHANNELS    1
#define I2S_BUFFER_LEN  1024

// WiFi Access Point configuration
const char* ap_ssid = "ESP32-AudioStream";
const char* ap_password = "audio123";

// Web server
WebServer server(80);

// Audio buffer
int32_t i2s_buffer[I2S_BUFFER_LEN];
int16_t audio_samples[I2S_BUFFER_LEN];
size_t bytes_read;

// Streaming clients
WiFiClient streamingClients[5]; // Support up to 5 concurrent streams
bool clientConnected[5] = {false, false, false, false, false};
unsigned long lastHeartbeat[5];

void setupI2S() {
  // Configure SEL pin - LOW = Left channel
  pinMode(I2S_SEL_PIN, OUTPUT);
  digitalWrite(I2S_SEL_PIN, LOW);
  
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = I2S_SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = I2S_BUFFER_LEN,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };

  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK_PIN,
    .ws_io_num = I2S_WS_PIN,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD_PIN
  };

  esp_err_t result = i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
  if (result != ESP_OK) {
    Serial.printf("Error installing I2S driver: %s\n", esp_err_to_name(result));
    return;
  }

  result = i2s_set_pin(I2S_PORT, &pin_config);
  if (result != ESP_OK) {
    Serial.printf("Error setting I2S pins: %s\n", esp_err_to_name(result));
    return;
  }

  Serial.println("✅ I2S microphone initialized!");
}

void setupWiFiAP() {
  Serial.println("Setting up WiFi Access Point...");
  
  // Configure Access Point
  WiFi.mode(WIFI_AP);
  WiFi.softAP(ap_ssid, ap_password);
  
  IPAddress IP = WiFi.softAPIP();
  Serial.println("✅ Access Point started!");
  Serial.println("📶 Network Name: " + String(ap_ssid));
  Serial.println("🔐 Password: " + String(ap_password));
  Serial.println("🌐 IP Address: " + IP.toString());
  Serial.println();
  
  // Setup mDNS for easy access
  if (MDNS.begin("esp32audio")) {
    Serial.println("🔍 mDNS responder started - access via: http://esp32audio.local");
  }
}

void handleRoot() {
  String html = R"(
<!DOCTYPE html>
<html>
<head>
    <title>ESP32 Audio Streamer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; margin: 20px; background: #f0f0f0; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        h1 { color: #333; text-align: center; }
        .stream-info { background: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .stream-url { font-family: monospace; background: #f8f8f8; padding: 10px; border: 1px solid #ddd; border-radius: 3px; word-break: break-all; }
        .instructions { background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #0056b3; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .connected { background: #d4edda; color: #155724; }
        .info { background: #d1ecf1; color: #0c5460; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ ESP32 Audio Streamer</h1>
        
        <div class="status connected">
            <strong>✅ Audio Stream Server Active</strong><br>
            Sample Rate: 16 kHz | Format: 16-bit PCM | Channels: Mono
        </div>
        
        <div class="stream-info">
            <h3>🎵 Direct Audio Stream URL:</h3>
            <div class="stream-url">http://)" + WiFi.softAPIP().toString() + R"(:8080/audio.wav</div>
        </div>
        
        <div class="instructions">
            <h3>📋 How to Listen:</h3>
            <p><strong>Option 1 - VLC Media Player:</strong></p>
            <ol>
                <li>Open VLC Media Player</li>
                <li>Go to Media → Open Network Stream</li>
                <li>Paste the stream URL above</li>
                <li>Click Play</li>
            </ol>
            
            <p><strong>Option 2 - Browser Audio:</strong></p>
            <ol>
                <li>Click the button below to test in browser</li>
                <li>Note: Browser playback might have latency</li>
            </ol>
            
            <p><strong>Option 3 - Command Line:</strong></p>
            <div class="stream-url">ffplay http://)" + WiFi.softAPIP().toString() + R"(:8080/audio.wav</div>
        </div>
        
        <div style="text-align: center;">
            <button onclick="window.open('/audio.wav', '_blank')">🔊 Test Audio in Browser</button>
            <button onclick="location.reload()">🔄 Refresh</button>
        </div>
        
        <div class="status info">
            <strong>📡 Connection Info:</strong><br>
            Connect to WiFi: <strong>)" + String(ap_ssid) + R"(</strong><br>
            Password: <strong>)" + String(ap_password) + R"(</strong><br>
            Then visit: <strong>http://)" + WiFi.softAPIP().toString() + R"(</strong>
        </div>
    </div>
</body>
</html>
  )";
  
  server.send(200, "text/html", html);
}

void handleAudioStream() {
  Serial.println("🎵 New audio stream client connected!");
  
  // Set headers for audio streaming
  server.setContentLength(CONTENT_LENGTH_UNKNOWN);
  server.send(200, "audio/wav", "");
  
  // Send WAV header for 16-bit PCM
  uint8_t wavHeader[44] = {
    0x52, 0x49, 0x46, 0x46, // "RIFF"
    0xFF, 0xFF, 0xFF, 0xFF, // File size (will be streaming, so we use max)
    0x57, 0x41, 0x56, 0x45, // "WAVE"
    0x66, 0x6D, 0x74, 0x20, // "fmt "
    0x10, 0x00, 0x00, 0x00, // PCM format chunk size (16)
    0x01, 0x00,             // Audio format (PCM)
    0x01, 0x00,             // Number of channels (1)
    0x80, 0x3E, 0x00, 0x00, // Sample rate (16000 Hz)
    0x00, 0x7D, 0x00, 0x00, // Byte rate (16000 * 1 * 2)
    0x02, 0x00,             // Block align (1 * 2)
    0x10, 0x00,             // Bits per sample (16)
    0x64, 0x61, 0x74, 0x61, // "data"
    0xFF, 0xFF, 0xFF, 0xFF  // Data size (streaming)
  };
  
  server.client().write(wavHeader, 44);
  
  WiFiClient client = server.client();
  unsigned long lastSend = millis();
  
  while (client.connected()) {
    // Read audio data
    esp_err_t result = i2s_read(I2S_PORT, i2s_buffer, sizeof(i2s_buffer), &bytes_read, 10);
    
    if (result == ESP_OK && bytes_read > 0) {
      // Process audio data (convert to 16-bit)
      for (int i = 0; i < I2S_BUFFER_LEN; i++) {
        int32_t sample32 = i2s_buffer[i];
        audio_samples[i] = (int16_t)(sample32 >> 14);
      }
      
      // Send audio data to client
      if (client.connected()) {
        size_t written = client.write((uint8_t*)audio_samples, I2S_BUFFER_LEN * 2);
        if (written == 0) {
          break; // Client disconnected
        }
      }
      
      // Heartbeat every 5 seconds
      if (millis() - lastSend > 5000) {
        Serial.println("🎵 Streaming audio...");
        lastSend = millis();
      }
    }
    
    yield(); // Allow other tasks to run
  }
  
  Serial.println("🔌 Audio stream client disconnected");
}

void setupWebServer() {
  server.on("/", handleRoot);
  server.on("/audio.wav", handleAudioStream);
  
  server.begin(80);
  
  // Start audio streaming server on port 8080
  server.begin(8080);
  
  Serial.println("🌐 Web server started on port 80");
  Serial.println("🎵 Audio stream server started on port 8080");
}

void processAudioData() {
  for (int i = 0; i < I2S_BUFFER_LEN; i++) {
    int32_t sample32 = i2s_buffer[i];
    audio_samples[i] = (int16_t)(sample32 >> 14);
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("==========================================");
  Serial.println("🎙️ ESP32 Audio Streaming Access Point");
  Serial.println("==========================================");
  
  setupI2S();
  setupWiFiAP();
  setupWebServer();
  
  Serial.println("🚀 Ready! Connect to the WiFi and open the web interface.");
  Serial.println("📱 WiFi: " + String(ap_ssid) + " | Password: " + String(ap_password));
  Serial.println("🌐 Web Interface: http://" + WiFi.softAPIP().toString());
  Serial.println("🎵 VLC Stream URL: http://" + WiFi.softAPIP().toString() + ":8080/audio.wav");
  Serial.println();
}

void loop() {
  server.handleClient();
  
  // Show periodic status
  static unsigned long lastStatus = 0;
  if (millis() - lastStatus > 10000) { // Every 10 seconds
    Serial.println("📡 Access Point Active | Clients: " + String(WiFi.softAPgetStationNum()));
    Serial.println("🎵 Stream: http://" + WiFi.softAPIP().toString() + ":8080/audio.wav");
    lastStatus = millis();
  }
  
  yield();
}
