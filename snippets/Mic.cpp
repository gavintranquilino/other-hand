#include <Arduino.h>
#include <driver/i2s.h>

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

// Audio buffer
int32_t i2s_buffer[I2S_BUFFER_LEN];
size_t bytes_read;

// Audio level monitoring
int16_t audio_samples[I2S_BUFFER_LEN];
float rms_level = 0;
int peak_level = 0;

void setupI2S() {
  // Configure SEL pin - LOW = Left channel, HIGH = Right channel
  pinMode(I2S_SEL_PIN, OUTPUT);
  digitalWrite(I2S_SEL_PIN, LOW); // Select left channel
  
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

  // Install and start I2S driver
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

  Serial.println("I2S microphone initialized successfully!");
  Serial.println("Pin configuration:");
  Serial.printf("  BCLK: D%d\n", I2S_SCK_PIN);
  Serial.printf("  DOUT: D%d\n", I2S_SD_PIN);
  Serial.printf("  LRCL: D%d\n", I2S_WS_PIN);
  Serial.printf("  SEL:  D%d (set to LEFT channel)\n", I2S_SEL_PIN);
}

void calculateAudioLevels() {
  long sum = 0;
  peak_level = 0;
  
  for (int i = 0; i < I2S_BUFFER_LEN; i++) {
    // SPH0645LM4H outputs 18-bit data in 32-bit format, left-justified
    // So we need to shift right by 14 bits to get the actual 18-bit value
    int32_t sample32 = i2s_buffer[i];
    int16_t sample16 = (sample32 >> 14); // Shift to get 18-bit data, then use as 16-bit
    
    audio_samples[i] = sample16;
    
    // Calculate RMS
    sum += (long)sample16 * sample16;
    
    // Track peak
    int abs_sample = abs(sample16);
    if (abs_sample > peak_level) {
      peak_level = abs_sample;
    }
  }
  
  rms_level = sqrt(sum / I2S_BUFFER_LEN);
}

void setup() {
  Serial.begin(115200);
  Serial.println("=================================");
  Serial.println("Adafruit I2S MEMS Microphone Test");
  Serial.println("SPH0645LM4H - Audio Level Monitor");
  Serial.println("=================================");
  
  // Initialize I2S microphone
  setupI2S();
  
  Serial.println("Starting audio monitoring...");
  Serial.println("Speak into the microphone!");
  Serial.println("");
}

void loop() {
  // Read audio data from I2S
  esp_err_t result = i2s_read(I2S_PORT, i2s_buffer, sizeof(i2s_buffer), &bytes_read, portMAX_DELAY);
  
  if (result == ESP_OK && bytes_read > 0) {
    // Calculate audio levels
    calculateAudioLevels();
    
    // Print audio levels to serial every 100ms
    static unsigned long lastPrint = 0;
    if (millis() - lastPrint > 100) {
      Serial.printf("RMS: %6.1f | Peak: %5d | ", rms_level, peak_level);
      
      // Simple audio level bar (30 characters wide)
      int bars = map(peak_level, 0, 32767, 0, 30);
      bars = constrain(bars, 0, 30);
      
      Serial.print("[");
      for (int i = 0; i < 30; i++) {
        if (i < bars) {
          if (i < 15) Serial.print("=");      // Green zone
          else if (i < 25) Serial.print("#");  // Yellow zone  
          else Serial.print("!");              // Red zone
        } else {
          Serial.print(" ");
        }
      }
      Serial.print("] ");
      
      // Show percentage and level description
      float percentage = (float)peak_level / 32767.0 * 100.0;
      Serial.printf("%.1f%% ", percentage);
      
      if (percentage < 10) Serial.println("(Very Quiet)");
      else if (percentage < 30) Serial.println("(Quiet)");
      else if (percentage < 60) Serial.println("(Normal)");
      else if (percentage < 85) Serial.println("(Loud)");
      else Serial.println("(Very Loud!)");
      
      lastPrint = millis();
    }
  } else {
    Serial.printf("I2S read error: %s\n", esp_err_to_name(result));
    delay(100);
  }
}