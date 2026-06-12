#include <TinyGPS++.h>
#include <SoftwareSerial.h>
#include "LoRa_E22.h"

/*
  GPS + LoRa transmitter for Arduino Nano.

  Hardware:
  - u-blox NEO-6M GPS TX -> D4, RX -> D3 (optional)
  - EBYTE E22-230T30D TXD -> D10, RXD -> D11
  - All GND lines common; power the 1W LoRa module from a strong 3.3V supply.

  Packet sent once per second after GPS fix:
  latitude,longitude,altitude,speed,heading,satellites
*/

SoftwareSerial gpsSerial(4, 3);     // Arduino RX, TX for GPS
SoftwareSerial loraSerial(10, 11);  // Arduino RX, TX for E22

TinyGPSPlus gps;
LoRa_E22 e22(&loraSerial);

bool fixFound = false;
unsigned long lastSendMs = 0;

void setup() {
  Serial.begin(9600);
  gpsSerial.begin(9600);
  loraSerial.begin(9600);
  e22.begin();

  Serial.println(F("SYSTEM START"));
  Serial.println(F("GPS START..."));
}

void loop() {
  while (gpsSerial.available()) {
    gps.encode(gpsSerial.read());
  }

  if (millis() - lastSendMs < 1000) {
    return;
  }
  lastSendMs = millis();

  Serial.print(F("Satellites: "));
  Serial.println(gps.satellites.value());

  if (!gps.location.isValid()) {
    Serial.println(F("Waiting GPS fix..."));
    Serial.println(F("----------------"));
    return;
  }

  if (!fixFound) {
    fixFound = true;
    Serial.println();
    Serial.println(F("GPS FIX DETECTED"));
    Serial.println(F("STARTING LORA TRANSMISSION"));
    Serial.println();
  }

  String data;
  data.reserve(90);
  data += String(gps.location.lat(), 6);
  data += ',';
  data += String(gps.location.lng(), 6);
  data += ',';
  data += String(gps.altitude.meters(), 1);
  data += ',';
  data += String(gps.speed.kmph(), 1);
  data += ',';
  data += String(gps.course.deg(), 1);
  data += ',';
  data += String(gps.satellites.value());

  char message[100];
  data.toCharArray(message, sizeof(message));

  Serial.print(F("TX DATA: "));
  Serial.println(message);

  ResponseStatus rs = e22.sendMessage(message);
  Serial.println(rs.code == SUCCESS ? F("SEND OK") : F("SEND ERROR"));
  Serial.println(F("----------------"));
}
