#include <WiFi.h>
#include <PubSubClient.h>
#include <ezLED.h>

const char* ssid = "Galaxy A516A59";
const char* password = "20111996";
const char* mqtt_server = "broker.hivemq.com";

WiFiClient espClient;
PubSubClient client(espClient);

// -------------------- PINS --------------------
const int buzzerPin   = 33;
const int greenLedPin = 26;
const int redLedPin   = 25;

// -------------------- BUZZER (PWM) --------------------
const int buzzerChannel = 0;
const int buzzerFreq = 2000;
const int buzzerResolution = 8;

// -------------------- STATE --------------------
bool fireActive = false;
bool buzzerOn = false;
unsigned long lastBuzzerToggle = 0;
const unsigned long buzzerInterval = 1000; // 1 second

// -------------------- LEDs --------------------
ezLED greenLed(greenLedPin);
ezLED redLed(redLedPin); 

// -------------------- SETUP --------------------
void setup() {
  Serial.begin(9600);

  pinMode(greenLedPin, OUTPUT);
  pinMode(redLedPin, OUTPUT);

  // Buzzer PWM setup
  ledcSetup(buzzerChannel, buzzerFreq, buzzerResolution);
  ledcAttachPin(buzzerPin, buzzerChannel);
  ledcWrite(buzzerChannel, 0);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");

  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);

  while (!client.connected()) {
    client.connect("ESP32_FIRE_NODE");
    delay(500);
  }

  client.subscribe("fire/system/alert");

  greenLed.turnON();
  redLed.turnOFF();
}

// -------------------- LOOP --------------------
void loop() {
  client.loop();

  // Non-blocking buzzer pulse
  if (fireActive) {
    unsigned long currentMillis = millis();

    if (currentMillis - lastBuzzerToggle >= buzzerInterval) {
      lastBuzzerToggle = currentMillis;
      buzzerOn = !buzzerOn;

      if (buzzerOn) {
        ledcWrite(buzzerChannel, 128);  // buzzer ON
      } else {
        ledcWrite(buzzerChannel, 0);    // buzzer OFF
      }
    }
  }
}

// -------------------- MQTT CALLBACK --------------------
void callback(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (int i = 0; i < length; i++) msg += (char)payload[i];

  Serial.println(msg);

  if (msg.indexOf("FIRE") >= 0) {
    fireActive = true;
    redLed.turnON();
    greenLed.turnOFF();
    Serial.println("Fire detected!");
  } 
  else if (msg.indexOf("OFF") >= 0) {
    fireActive = false;
    ledcWrite(buzzerChannel, 0); // ensure buzzer OFF
    buzzerOn = false;
    redLed.turnOFF();
    greenLed.turnON();
    Serial.println("Alarm off");
  }
}
