#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>  // ← BME280
#include "MAX30105.h"
#include "heartRate.h"

// === SEUILS ===
#define HUMIDITY_THRESHOLD   70.0
#define CO2_THRESHOLD       1200.0
#define SPO2_LOW_THRESHOLD    94.0
#define BPM_HIGH_THRESHOLD   100.0

// === PINs ===
#define MQ135_PIN 34

// === OBJETS ===
Adafruit_BME280 bme;
MAX30105 particleSensor;

// Variables
float humidity = 0;
float co2_ppm = 0;
float spo2 = 0;
long bpm = 0;
bool alertSent = false;
long lastBeat = 0;

void setup() {
  Serial.begin(115200);
  Wire.begin();

  // --- BME280 ---
  if (!bme.begin(0x76) && !bme.begin(0x77)) {
    Serial.println("BME280 non détecté → on continue sans humidité");
  } else {
    Serial.println("BME280 détecté !");
  }

  // --- MAX30102 ---
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    Serial.println("MAX30102 non détecté → on continue sans SpO2/BPM");
  } else {
    Serial.println("MAX30102 détecté !");
    particleSensor.setup();
    particleSensor.setPulseAmplitudeRed(0x0A);
    particleSensor.setPulseAmplitudeIR(0x0A);
  }

  Serial.println("Système prêt. Surveillance en cours...");
}

void loop() {
  // --- BME280 ---
  if (bme.begin(0x76) || bme.begin(0x77)) {
    humidity = bme.readHumidity();
  } else {
    humidity = 0;
  }

  // --- MQ-135 ---
  int analogValue = analogRead(MQ135_PIN);
  co2_ppm = map(analogValue, 100, 1000, 400, 2000);
  co2_ppm = constrain(co2_ppm, 400, 5000);

  // --- MAX30102 ---
  long irValue = particleSensor.getIR();
  if (irValue > 50000) {
    if (checkForBeat(irValue)) {
      long delta = millis() - lastBeat;
      lastBeat = millis();
      if (delta > 300) {
        bpm = 60000 / delta;
        if (bpm > 30 && bpm < 220) {
          long redValue = particleSensor.getRed();
          float ratio = (float)redValue / irValue;
          spo2 = 104 - 17 * ratio;
          spo2 = constrain(spo2, 70, 100);
        }
      }
    }
  } else {
    spo2 = 0;
    bpm = 0;
  }

  // --- AFFICHAGE ---
  Serial.println("=== ÉTAT ===");
  Serial.printf("Humidité: %.1f %%\n", humidity);
  Serial.printf("CO2 approx: %.0f PPM\n", co2_ppm);
  Serial.printf("SpO2: %.1f %% | BPM: %ld\n", spo2, bpm);

  // --- ALERTE ---
  String alert = "";
  if (humidity > HUMIDITY_THRESHOLD && co2_ppm > CO2_THRESHOLD) {
    alert = "Risque de crise élevé. Aérez ou quittez la pièce.";
  } else if (co2_ppm > CO2_THRESHOLD) {
    alert = "Activez un purificateur d'air automatiquement.";
  } else if (spo2 > 0 && spo2 < SPO2_LOW_THRESHOLD) {
    alert = "Utilisez votre inhalateur.";
  } else if (bpm > BPM_HIGH_THRESHOLD) {
    alert = "Fréquence cardiaque élevée. Respirez calmement.";
  }

  if (alert != "" && !alertSent) {
    Serial.println("\nALERTE : " + alert + "\n");
    alertSent = true;
  } else if (alert == "") {
    alertSent = false;
  }

  delay(2000);
}