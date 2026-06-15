# VAYLLEM UAV Command Center V2 Professional

Professional military-style PyQt6 Ground Control Station for Arduino Nano + HC-12 GPS telemetry at 9600 baud.

## V2 Features

- Artificial Horizon, Compass, Aircraft Altimeter, Vertical Speed Indicator and Radar widgets rendered with `QPainter`.
- Digital UTC clock, neon glow effects, animated startup and smooth instrument transitions through `QPropertyAnimation`.
- Folium + QtWebEngine tactical map with animated drone marker, direction arrow, runtime layer switching, auto-center tracking, HUD overlay and distance traveled calculation.
- Signal quality monitor, RSSI visualization, packet loss statistics and live link status.
- Flight analytics dashboard with flight timer, distance, packets, max/min/average altitude and vertical speed.
- Session recorder and replay system using JSONL telemetry streams.
- Camera panel placeholder for future EO/IR payload integration.

## Install

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r project/requirements.txt
```

## Run

```bash
python project/main.py
```

## Arduino + HC-12

Upload receiver firmware that prints three lines per packet:

```text
Latitude : 38.856670
Longitude: 65.817260
Altitude : 373.6 m
```

Connect the receiver Arduino Nano by USB, select COM port in Settings, keep baudrate 9600, then press Connect.

## Replay

Press **Record** to save a session into `sessions/flight_YYYYMMDD_HHMMSS.jsonl`. Press **Replay** and select a recorded JSONL file to play it back through the same dashboard pipeline.

## Troubleshooting

Close Arduino Serial Monitor before connecting, verify the baudrate, confirm HC-12 modules share channel/settings, and wait outdoors for GPS fix. If QtWebEngine does not open on Linux, install the distribution OpenGL/WebEngine runtime packages.
