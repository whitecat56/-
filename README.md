# Drone Command Center

A complete PyQt6 Ground Control Station for an Arduino Nano + u-blox NEO-6M GPS + EBYTE E22-230T30D LoRa telemetry transmitter.

## Hardware packet

The receiver expects one ASCII line per telemetry packet at 9600 baud:

```text
latitude,longitude,altitude,speed,heading,satellites
```

Optional future fields are supported:

```text
latitude,longitude,altitude,speed,heading,satellites,rssi,snr
```

Example:

```text
41.311081,69.240562,450.3,35.5,180.0,12
```

## Features

- Leaflet/Folium map in `QWebEngineView` with drone marker, nose heading, track history, mouse-wheel zoom, center button, and `FOLLOW DRONE` mode.
- `SET HOME`, distance from home, bearing to home, and Return-To-Home direction arrow.
- Flight data page/cards with large altitude, speed, heading, and satellite count.
- Aviation compass and synthetic radar that displays HOME and DRONE.
- Mission statistics: elapsed time, travelled distance, max speed, and max altitude.
- GPS quality colors: BAD (0-3 satellites), MEDIUM (4-6), GOOD (7+).
- LoRa status, RSSI, and SNR fields.
- Sound notifications using the Qt application beep for GPS fix, signal loss, LoRa connected, and LoRa disconnected.
- Automatic mission recording under `missions/mission_YYYYMMDD_HHMMSS/` as `telemetry.csv`, `telemetry.json`, and `track.gpx`.
- Replay mission support from recorded CSV or JSON files.
- Settings window for serial port, baud rate, timeout, theme, and mission folder.
- Themes: Dark Tactical, Military Green, and Blue Cyberpunk.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Linux, `PyQt6-WebEngine` may require system OpenGL/WebEngine libraries from your distribution.

## Run

```bash
python drone_command_center.py
```

Open **SETTINGS**, choose the receiver serial port, keep UART at `9600`, and press **CONNECT LORA**.
