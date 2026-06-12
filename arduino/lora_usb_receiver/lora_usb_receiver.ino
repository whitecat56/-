#include <SoftwareSerial.h>
#include "LoRa_E22.h"

/*
  LoRa USB receiver for the PyQt Drone Command Center.

  Hardware:
  - EBYTE E22-230T30D TXD -> D10, RXD -> D11
  - Arduino Nano USB -> laptop/PC running drone_command_center.py

  The desktop app expects a CSV telemetry line on Serial:
  latitude,longitude,altitude,speed,heading,satellites[,rssi]

  E22 RSSI note:
  The xreef EByte E22 library exposes receiveMessageRSSI() and ResponseContainer.rssi
  when RSSI output is enabled in the module configuration.
*/

SoftwareSerial loraSerial(10, 11);  // Arduino RX, TX for E22
LoRa_E22 e22(&loraSerial);

void setup() {
  Serial.begin(9600);
  loraSerial.begin(9600);
  e22.begin();
  enablePacketRssi();

  Serial.println(F("LORA USB RECEIVER READY"));
  Serial.println(F("Waiting telemetry: lat,lon,alt,speed,heading,sats"));
}

void enablePacketRssi() {
  ResponseStructContainer c = e22.getConfiguration();
  if (c.status.code != SUCCESS) {
    Serial.print(F("RSSI CONFIG READ ERROR: "));
    Serial.println(c.status.getResponseDescription());
    return;
  }

  Configuration configuration = *(Configuration*) c.data;
  configuration.TRANSMISSION_MODE.enableRSSI = RSSI_ENABLED;
  ResponseStatus rs = e22.setConfiguration(configuration, WRITE_CFG_PWR_DWN_LOSE);
  c.close();

  Serial.print(F("RSSI CONFIG: "));
  Serial.println(rs.getResponseDescription());
}

void loop() {
  if (e22.available() <= 1) {
    delay(10);
    return;
  }

  ResponseContainer rc = e22.receiveMessageRSSI();
  if (rc.status.code != SUCCESS) {
    Serial.print(F("RX ERROR: "));
    Serial.println(rc.status.getResponseDescription());
    return;
  }

  rc.data.trim();
  if (rc.data.length() == 0) {
    return;
  }

  // Important: this clean CSV line is what the Python dashboard parses.
  // E22 exposes packet RSSI as an unsigned byte. The common dBm approximation is -RSSI/2.
  float packetRssiDbm = -float(rc.rssi) / 2.0;
  Serial.print(rc.data);
  Serial.print(',');
  Serial.println(packetRssiDbm, 1);
}
