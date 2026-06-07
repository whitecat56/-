#!/usr/bin/env python3
"""Drone Command Center: PyQt6 ground control station for GPS + LoRa telemetry."""

from __future__ import annotations

import csv
import json
import math
import os
import sys
import time
import webbrowser
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import folium
import pyqtgraph as pg
import serial
import serial.tools.list_ports
from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, QRectF, QSettings, Qt, QThread, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QFont, QPainter, QPen, QPolygonF, QRadialGradient
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QSplashScreen,
    QStackedWidget,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

APP_NAME = "Drone Command Center"
ORGANIZATION = "OpenAI UAV Systems"
HARDWARE_INFO = {
    "GPS Module": "u-blox NEO-6M",
    "Radio": "EBYTE E22-230T30D",
    "Frequency": "433 MHz",
    "Protocol": "LoRa",
    "UART": "9600 baud",
    "Packet": "latitude,longitude,altitude,speed,heading,satellites",
}
THEMES = {
    "Dark Tactical": {
        "bg": "#061014", "panel": "#0b1b22", "panel2": "#102a34", "text": "#d8fff4", "muted": "#7fa9a2",
        "accent": "#00ffc6", "accent2": "#ffb000", "danger": "#ff355e", "grid": "#17424b",
    },
    "Military Green": {
        "bg": "#071007", "panel": "#101c10", "panel2": "#183018", "text": "#e0ffcf", "muted": "#9ab98b",
        "accent": "#86ff4f", "accent2": "#d7ff6b", "danger": "#ff4d3d", "grid": "#2f542f",
    },
    "Blue Cyberpunk": {
        "bg": "#050818", "panel": "#0a1230", "panel2": "#0d2152", "text": "#e6f3ff", "muted": "#7ba3d9",
        "accent": "#00b7ff", "accent2": "#da6bff", "danger": "#ff2f7d", "grid": "#173777",
    },
}


@dataclass
class TelemetryPoint:
    timestamp: str
    latitude: float
    longitude: float
    altitude: float
    speed: float
    heading: float
    satellites: int
    rssi: Optional[float] = None
    snr: Optional[float] = None

    @classmethod
    def from_line(cls, line: str) -> "TelemetryPoint":
        parts = [part.strip() for part in line.strip().split(",")]
        if len(parts) < 6:
            raise ValueError("Telemetry packet must contain at least 6 comma-separated fields")
        rssi = float(parts[6]) if len(parts) >= 7 and parts[6] else None
        snr = float(parts[7]) if len(parts) >= 8 and parts[7] else None
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            latitude=float(parts[0]), longitude=float(parts[1]), altitude=float(parts[2]),
            speed=float(parts[3]), heading=float(parts[4]) % 360.0, satellites=int(float(parts[5])), rssi=rssi, snr=snr,
        )


@dataclass
class MissionStats:
    started_at: float
    total_distance_m: float = 0.0
    max_speed: float = 0.0
    max_altitude: float = -100000.0

    def elapsed_seconds(self) -> int:
        return int(time.time() - self.started_at)


class GeoMath:
    EARTH_RADIUS_M = 6371000.0

    @staticmethod
    def distance_m(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
        lat1 = math.radians(a_lat); lat2 = math.radians(b_lat)
        d_lat = math.radians(b_lat - a_lat); d_lon = math.radians(b_lon - a_lon)
        h = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
        return GeoMath.EARTH_RADIUS_M * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))

    @staticmethod
    def bearing_deg(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
        lat1 = math.radians(a_lat); lat2 = math.radians(b_lat); d_lon = math.radians(b_lon - a_lon)
        y = math.sin(d_lon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)
        return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


class MissionRecorder:
    def __init__(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=True)
        mission_name = datetime.now().strftime("mission_%Y%m%d_%H%M%S")
        self.directory = root / mission_name
        self.directory.mkdir(parents=True, exist_ok=True)
        self.csv_path = self.directory / "telemetry.csv"
        self.json_path = self.directory / "telemetry.json"
        self.gpx_path = self.directory / "track.gpx"
        self.points: list[TelemetryPoint] = []
        self._csv_file = self.csv_path.open("w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._csv_file, fieldnames=list(asdict(TelemetryPoint("", 0, 0, 0, 0, 0, 0)).keys()))
        self._writer.writeheader()
        self._csv_file.flush()
        self._write_json()
        self._write_gpx()

    def add(self, point: TelemetryPoint) -> None:
        self.points.append(point)
        self._writer.writerow(asdict(point))
        self._csv_file.flush()
        self._write_json()
        self._write_gpx()

    def close(self) -> None:
        self._csv_file.close()
        self._write_json()
        self._write_gpx()

    def _write_json(self) -> None:
        payload = {"hardware": HARDWARE_INFO, "points": [asdict(p) for p in self.points]}
        self.json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_gpx(self) -> None:
        segments = []
        for p in self.points:
            segments.append(
                f'      <trkpt lat="{p.latitude:.8f}" lon="{p.longitude:.8f}">\n'
                f"        <ele>{p.altitude:.2f}</ele>\n"
                f"        <time>{p.timestamp}</time>\n"
                f"      </trkpt>"
            )
        content = "\n".join([
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<gpx version="1.1" creator="Drone Command Center" xmlns="http://www.topografix.com/GPX/1/1">',
            '  <trk><name>UAV LoRa Mission</name><trkseg>',
            *segments,
            '  </trkseg></trk>',
            '</gpx>',
        ])
        self.gpx_path.write_text(content, encoding="utf-8")


class TelemetrySerialThread(QThread):
    telemetry = pyqtSignal(TelemetryPoint)
    link_changed = pyqtSignal(bool)
    error = pyqtSignal(str)

    def __init__(self, port: str, baud: int, timeout_s: float) -> None:
        super().__init__()
        self.port = port
        self.baud = baud
        self.timeout_s = timeout_s
        self._running = True

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        last_packet = time.time()
        connected = False
        try:
            with serial.Serial(self.port, self.baud, timeout=0.2) as ser:
                while self._running:
                    raw = ser.readline().decode("ascii", errors="ignore").strip()
                    now = time.time()
                    if raw:
                        try:
                            point = TelemetryPoint.from_line(raw)
                            self.telemetry.emit(point)
                            last_packet = now
                            if not connected:
                                connected = True
                                self.link_changed.emit(True)
                        except ValueError as exc:
                            self.error.emit(f"Invalid packet: {raw} ({exc})")
                    if connected and now - last_packet > self.timeout_s:
                        connected = False
                        self.link_changed.emit(False)
        except serial.SerialException as exc:
            self.error.emit(f"Serial port error: {exc}")
            self.link_changed.emit(False)


class AudioNotifier:
    def __init__(self) -> None:
        self.player = QMediaPlayer()
        self.output = QAudioOutput()
        self.player.setAudioOutput(self.output)
        self.output.setVolume(0.35)
        self._last_messages: dict[str, float] = {}

    def notify(self, message: str) -> None:
        now = time.time()
        if now - self._last_messages.get(message, 0.0) < 2.0:
            return
        self._last_messages[message] = now
        QApplication.beep()


class Splash(QSplashScreen):
    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(720, 380)
        self.text = "DRONE COMMAND CENTER\nGPS + LORA TRACKING SYSTEM\nEBYTE E22-230T30D\nu-blox NEO-6M\n\nLOADING MODULES..."

    def drawContents(self, painter: QPainter) -> None:
        painter.fillRect(self.rect(), QColor("#050b0d"))
        pen = QPen(QColor("#00ffc6"), 2)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(12, 12, -12, -12))
        painter.setFont(QFont("Consolas", 28, QFont.Weight.Bold))
        painter.drawText(QRectF(0, 45, self.width(), 55), Qt.AlignmentFlag.AlignCenter, "DRONE COMMAND CENTER")
        painter.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        painter.setPen(QColor("#d8fff4"))
        painter.drawText(QRectF(0, 118, self.width(), 210), Qt.AlignmentFlag.AlignCenter, self.text.split("\n", 1)[1])
        painter.setPen(QPen(QColor("#00ffc6"), 3))
        painter.drawLine(90, 330, 630, 330)
        painter.setPen(QColor("#ffb000"))
        painter.drawText(QRectF(0, 342, self.width(), 30), Qt.AlignmentFlag.AlignCenter, "SECURE TELEMETRY INTERFACE ONLINE")


class CompassWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.heading = 0.0
        self.setMinimumSize(240, 240)

    def set_heading(self, heading: float) -> None:
        self.heading = heading % 360.0
        self.update()

    def paintEvent(self, event) -> None:
        side = min(self.width(), self.height()) - 12
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = side / 2
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QRadialGradient(center, radius); grad.setColorAt(0, QColor(20, 45, 52)); grad.setColorAt(1, QColor(3, 10, 12))
        p.setBrush(grad); p.setPen(QPen(QColor("#00ffc6"), 2)); p.drawEllipse(center, radius, radius)
        p.translate(center); p.rotate(-self.heading)
        for deg in range(0, 360, 10):
            p.save(); p.rotate(deg)
            length = 18 if deg % 30 == 0 else 9
            p.setPen(QPen(QColor("#d8fff4"), 2 if deg % 30 == 0 else 1))
            p.drawLine(0, -radius + 8, 0, -radius + 8 + length)
            if deg % 90 == 0:
                label = {0: "N", 90: "E", 180: "S", 270: "W"}[deg]
                p.setPen(QColor("#ffb000") if deg == 0 else QColor("#d8fff4")); p.setFont(QFont("Consolas", 16, QFont.Weight.Bold))
                p.drawText(QRectF(-15, -radius + 30, 30, 25), Qt.AlignmentFlag.AlignCenter, label)
            p.restore()
        p.rotate(self.heading)
        p.setBrush(QColor("#ff355e")); p.setPen(Qt.PenStyle.NoPen)
        p.drawPolygon(QPolygonF([QPointF(0, -radius + 34), QPointF(-10, -20), QPointF(0, -32), QPointF(10, -20)]))
        p.setPen(QColor("#00ffc6")); p.setFont(QFont("Consolas", 20, QFont.Weight.Bold))
        p.drawText(QRectF(-55, 18, 110, 38), Qt.AlignmentFlag.AlignCenter, f"{self.heading:03.0f}°")


class RadarWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.home: Optional[TelemetryPoint] = None
        self.drone: Optional[TelemetryPoint] = None
        self.setMinimumSize(260, 260)

    def update_points(self, home: Optional[TelemetryPoint], drone: Optional[TelemetryPoint]) -> None:
        self.home = home; self.drone = drone; self.update()

    def paintEvent(self, event) -> None:
        side = min(self.width(), self.height()) - 14
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = side / 2
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor("#061014")); p.setPen(QPen(QColor("#17424b"), 1))
        for factor in (0.25, 0.5, 0.75, 1.0):
            p.drawEllipse(center, radius * factor, radius * factor)
        p.drawLine(center.x() - radius, center.y(), center.x() + radius, center.y())
        p.drawLine(center.x(), center.y() - radius, center.x(), center.y() + radius)
        p.setPen(QPen(QColor("#86ff4f"), 2)); p.setBrush(QColor("#86ff4f")); p.drawEllipse(center, 5, 5)
        p.drawText(center + QPointF(8, -8), "HOME")
        if self.home and self.drone:
            dist = GeoMath.distance_m(self.home.latitude, self.home.longitude, self.drone.latitude, self.drone.longitude)
            bearing = GeoMath.bearing_deg(self.home.latitude, self.home.longitude, self.drone.latitude, self.drone.longitude)
            scaled = min(radius - 15, max(12, dist / max(1.0, dist) * min(radius - 15, dist / 8)))
            angle = math.radians(bearing - 90)
            point = QPointF(center.x() + math.cos(angle) * scaled, center.y() + math.sin(angle) * scaled)
            p.setPen(QPen(QColor("#00ffc6"), 2)); p.drawLine(center, point)
            p.setBrush(QColor("#00b7ff")); p.drawEllipse(point, 7, 7); p.drawText(point + QPointF(9, -9), f"DRONE {dist:.0f}m")


class FlightDataWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QGridLayout(self)
        self.values: dict[str, QLabel] = {}
        for idx, (key, title, unit) in enumerate([
            ("altitude", "ALTITUDE", "m"), ("speed", "GROUND SPEED", "km/h"),
            ("heading", "HEADING", "°"), ("satellites", "SATELLITES", ""),
        ]):
            box = QFrame(); box.setObjectName("dataCard")
            v = QVBoxLayout(box)
            caption = QLabel(title); caption.setObjectName("caption")
            value = QLabel("--"); value.setObjectName("bigNumber")
            suffix = QLabel(unit); suffix.setObjectName("unit")
            v.addWidget(caption); v.addWidget(value); v.addWidget(suffix)
            layout.addWidget(box, idx // 2, idx % 2)
            self.values[key] = value

    def update_telemetry(self, p: TelemetryPoint) -> None:
        self.values["altitude"].setText(f"{p.altitude:.1f}")
        self.values["speed"].setText(f"{p.speed:.1f}")
        self.values["heading"].setText(f"{p.heading:03.0f}")
        self.values["satellites"].setText(str(p.satellites))


class SettingsDialog(QDialog):
    def __init__(self, settings: QSettings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ground Station Settings")
        self.settings = settings
        self.port = QComboBox(); self.port.setEditable(True)
        for port in serial.tools.list_ports.comports():
            self.port.addItem(port.device)
        self.port.setCurrentText(settings.value("serial/port", ""))
        self.baud = QSpinBox(); self.baud.setRange(1200, 921600); self.baud.setValue(int(settings.value("serial/baud", 9600)))
        self.timeout = QDoubleSpinBox(); self.timeout.setRange(1.0, 60.0); self.timeout.setValue(float(settings.value("serial/timeout", 5.0))); self.timeout.setSuffix(" s")
        self.theme = QComboBox(); self.theme.addItems(THEMES.keys()); self.theme.setCurrentText(settings.value("ui/theme", "Dark Tactical"))
        self.mission_root = QLineEdit(settings.value("missions/root", str(Path.cwd() / "missions")))
        browse = QPushButton("Browse")
        browse.clicked.connect(self.choose_root)
        root_row = QHBoxLayout(); root_row.addWidget(self.mission_root); root_row.addWidget(browse)
        form = QFormLayout(); form.addRow("Serial port", self.port); form.addRow("UART baud", self.baud); form.addRow("Link timeout", self.timeout); form.addRow("Theme", self.theme); form.addRow("Missions folder", root_row)
        save = QPushButton("SAVE SETTINGS"); cancel = QPushButton("CANCEL")
        save.clicked.connect(self.accept); cancel.clicked.connect(self.reject)
        buttons = QHBoxLayout(); buttons.addStretch(); buttons.addWidget(cancel); buttons.addWidget(save)
        layout = QVBoxLayout(self); layout.addLayout(form); layout.addLayout(buttons)

    def choose_root(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select missions folder", self.mission_root.text())
        if directory:
            self.mission_root.setText(directory)

    def accept(self) -> None:
        self.settings.setValue("serial/port", self.port.currentText())
        self.settings.setValue("serial/baud", self.baud.value())
        self.settings.setValue("serial/timeout", self.timeout.value())
        self.settings.setValue("ui/theme", self.theme.currentText())
        self.settings.setValue("missions/root", self.mission_root.text())
        super().accept()


class MapWidget(QWebEngineView):
    def __init__(self) -> None:
        super().__init__()
        self.map_name = ""
        self.setHtml(self._build_html(41.311081, 69.240562), QUrl("https://local.gcs/"))

    def _build_html(self, lat: float, lon: float) -> str:
        fmap = folium.Map(location=[lat, lon], zoom_start=15, tiles="OpenStreetMap", control_scale=True)
        self.map_name = fmap.get_name()
        script = f"""
        <style>
        html, body, .folium-map {{ width:100%; height:100%; margin:0; background:#061014; }}
        .leaflet-control-attribution {{ background:rgba(6,16,20,.75)!important; color:#9ff!important; }}
        .drone-icon {{ width:34px; height:34px; transform-origin:50% 50%; filter:drop-shadow(0 0 7px #00ffc6); }}
        .home-icon {{ color:#86ff4f; font:bold 20px monospace; text-shadow:0 0 8px #86ff4f; }}
        </style>
        <script>
        window.gcsState = {{ droneMarker:null, homeMarker:null, track:null, rth:null, follow:false, points:[] }};
        function droneDiv(heading) {{
          return L.divIcon({{className:'', iconSize:[34,34], iconAnchor:[17,17], html:`<svg class="drone-icon" style="transform:rotate(${{heading}}deg)" viewBox="0 0 64 64"><path d="M32 4 L44 58 L32 48 L20 58 Z" fill="#00ffc6" stroke="#001" stroke-width="3"/><path d="M32 4 L32 48" stroke="#ffffff" stroke-width="3"/></svg>`}});
        }}
        function homeDiv() {{ return L.divIcon({{className:'home-icon', iconSize:[60,24], iconAnchor:[30,12], html:'⌂ HOME'}}); }}
        function ensureLayers() {{
          if (!window.gcsState.track) window.gcsState.track = L.polyline([], {{color:'#00ffc6', weight:3, opacity:.9}}).addTo({self.map_name});
          if (!window.gcsState.rth) window.gcsState.rth = L.polyline([], {{color:'#ffb000', weight:2, dashArray:'8 8', opacity:.95}}).addTo({self.map_name});
        }}
        window.setFollow = function(enabled) {{ window.gcsState.follow = enabled; }};
        window.centerDrone = function() {{ if (window.gcsState.droneMarker) {self.map_name}.panTo(window.gcsState.droneMarker.getLatLng()); }};
        window.setHome = function(lat, lon) {{
          if (!lat && !lon && window.gcsState.droneMarker) {{ var p=window.gcsState.droneMarker.getLatLng(); lat=p.lat; lon=p.lng; }}
          if (window.gcsState.homeMarker) window.gcsState.homeMarker.setLatLng([lat, lon]);
          else window.gcsState.homeMarker = L.marker([lat, lon], {{icon:homeDiv()}}).addTo({self.map_name});
        }};
        window.updateTelemetry = function(p) {{
          ensureLayers();
          const latlng = [p.latitude, p.longitude];
          window.gcsState.points.push(latlng);
          if (window.gcsState.droneMarker) window.gcsState.droneMarker.setLatLng(latlng).setIcon(droneDiv(p.heading));
          else window.gcsState.droneMarker = L.marker(latlng, {{icon:droneDiv(p.heading)}}).addTo({self.map_name});
          window.gcsState.track.setLatLngs(window.gcsState.points);
          if (window.gcsState.homeMarker) window.gcsState.rth.setLatLngs([window.gcsState.homeMarker.getLatLng(), latlng]);
          if (window.gcsState.follow) {self.map_name}.panTo(latlng, {{animate:true, duration:.35}});
        }};
        </script>
        """
        fmap.get_root().html.add_child(folium.Element(script))
        return fmap.get_root().render()

    def update_telemetry(self, p: TelemetryPoint) -> None:
        self.page().runJavaScript(f"window.updateTelemetry({json.dumps(asdict(p))});")

    def set_home(self, p: TelemetryPoint) -> None:
        self.page().runJavaScript(f"window.setHome({p.latitude}, {p.longitude});")

    def set_follow(self, enabled: bool) -> None:
        self.page().runJavaScript(f"window.setFollow({str(enabled).lower()});")

    def center_drone(self) -> None:
        self.page().runJavaScript("window.centerDrone();")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1560, 920)
        self.settings = QSettings(ORGANIZATION, APP_NAME)
        self.theme_name = self.settings.value("ui/theme", "Dark Tactical")
        self.audio = AudioNotifier()
        self.serial_thread: Optional[TelemetrySerialThread] = None
        self.points: list[TelemetryPoint] = []
        self.home: Optional[TelemetryPoint] = None
        self.stats = MissionStats(time.time())
        self.recorder = MissionRecorder(Path(self.settings.value("missions/root", str(Path.cwd() / "missions"))))
        self.link_connected = False
        self._gps_fix_announced = False
        self._build_ui()
        self.apply_theme(self.theme_name)
        self.stats_timer = QTimer(self); self.stats_timer.timeout.connect(self.refresh_stats); self.stats_timer.start(1000)

    def _build_ui(self) -> None:
        toolbar = self.addToolBar("Mission")
        connect_action = QAction("CONNECT LORA", self); connect_action.triggered.connect(self.toggle_serial)
        replay_action = QAction("REPLAY MISSION", self); replay_action.triggered.connect(self.replay_mission)
        settings_action = QAction("SETTINGS", self); settings_action.triggered.connect(self.open_settings)
        open_folder_action = QAction("OPEN MISSION FOLDER", self); open_folder_action.triggered.connect(lambda: webbrowser.open(self.recorder.directory.as_uri()))
        toolbar.addAction(connect_action); toolbar.addAction(replay_action); toolbar.addAction(settings_action); toolbar.addAction(open_folder_action)
        self.connect_action = connect_action

        central = QWidget(); self.setCentralWidget(central)
        root = QHBoxLayout(central)
        left = QVBoxLayout(); center = QVBoxLayout(); right = QVBoxLayout()
        root.addLayout(left, 2); root.addLayout(center, 5); root.addLayout(right, 2)

        title = QLabel("DRONE COMMAND CENTER"); title.setObjectName("title")
        subtitle = QLabel("GPS + LORA TRACKING SYSTEM | NATO-STYLE UAV GROUND CONTROL")
        subtitle.setObjectName("subtitle")
        center.addWidget(title); center.addWidget(subtitle)
        self.map = MapWidget(); center.addWidget(self.map, 1)
        controls = QHBoxLayout()
        self.follow = QCheckBox("FOLLOW DRONE"); self.follow.toggled.connect(self.map.set_follow)
        center_btn = QPushButton("CENTER DRONE"); center_btn.clicked.connect(self.map.center_drone)
        home_btn = QPushButton("SET HOME"); home_btn.clicked.connect(self.set_home)
        controls.addWidget(self.follow); controls.addWidget(center_btn); controls.addWidget(home_btn); controls.addStretch()
        center.addLayout(controls)

        hardware = QGroupBox("HARDWARE")
        hw_layout = QFormLayout(hardware)
        for key, value in HARDWARE_INFO.items():
            hw_layout.addRow(QLabel(f"{key}:"), QLabel(value))
        left.addWidget(hardware)

        self.flight_data = FlightDataWidget(); left.addWidget(self.flight_data)
        self.compass = CompassWidget(); left.addWidget(self.compass)
        self.radar = RadarWidget(); left.addWidget(self.radar)

        self.link_label = QLabel("DISCONNECTED"); self.link_label.setObjectName("linkBad")
        self.gps_quality = QLabel("GPS: NO FIX"); self.gps_quality.setObjectName("gpsBad")
        self.rssi_label = QLabel("RSSI: -- dBm")
        self.snr_label = QLabel("SNR: -- dB")
        status_box = QGroupBox("LINK & GPS QUALITY")
        s_layout = QVBoxLayout(status_box); s_layout.addWidget(self.link_label); s_layout.addWidget(self.gps_quality); s_layout.addWidget(self.rssi_label); s_layout.addWidget(self.snr_label)
        right.addWidget(status_box)

        nav_box = QGroupBox("HOME NAVIGATION")
        n_layout = QGridLayout(nav_box)
        self.home_distance = QLabel("-- m / -- km"); self.bearing_home = QLabel("--°"); self.rth_arrow = QLabel("▲"); self.rth_arrow.setObjectName("rthArrow")
        n_layout.addWidget(QLabel("Distance From Home"), 0, 0); n_layout.addWidget(self.home_distance, 0, 1)
        n_layout.addWidget(QLabel("Bearing To Home"), 1, 0); n_layout.addWidget(self.bearing_home, 1, 1)
        n_layout.addWidget(QLabel("Return To Home Arrow"), 2, 0); n_layout.addWidget(self.rth_arrow, 2, 1, Qt.AlignmentFlag.AlignCenter)
        right.addWidget(nav_box)

        stats_box = QGroupBox("MISSION STATISTICS")
        m_layout = QFormLayout(stats_box)
        self.elapsed_label = QLabel("00:00:00"); self.distance_label = QLabel("0 m"); self.max_speed_label = QLabel("0 km/h"); self.max_alt_label = QLabel("0 m")
        m_layout.addRow("Time", self.elapsed_label); m_layout.addRow("Travelled", self.distance_label); m_layout.addRow("Max Speed", self.max_speed_label); m_layout.addRow("Max Altitude", self.max_alt_label)
        right.addWidget(stats_box)

        chart_box = QGroupBox("TELEMETRY GRAPHS")
        c_layout = QVBoxLayout(chart_box)
        self.alt_plot = pg.PlotWidget(title="Altitude")
        self.speed_plot = pg.PlotWidget(title="Ground Speed")
        self.alt_curve = self.alt_plot.plot(pen=pg.mkPen("#00ffc6", width=2))
        self.speed_curve = self.speed_plot.plot(pen=pg.mkPen("#ffb000", width=2))
        c_layout.addWidget(self.alt_plot); c_layout.addWidget(self.speed_plot)
        right.addWidget(chart_box, 1)

        self.log = QTextEdit(); self.log.setReadOnly(True); self.log.setMaximumHeight(130); center.addWidget(self.log)

    def apply_theme(self, name: str) -> None:
        theme = THEMES.get(name, THEMES["Dark Tactical"])
        self.setStyleSheet(f"""
        QMainWindow, QWidget {{ background:{theme['bg']}; color:{theme['text']}; font-family:Consolas, monospace; }}
        QGroupBox {{ border:1px solid {theme['grid']}; border-radius:8px; margin-top:18px; padding:10px; background:{theme['panel']}; font-weight:bold; }}
        QGroupBox::title {{ subcontrol-origin: margin; left:12px; color:{theme['accent']}; }}
        QLabel#title {{ color:{theme['accent']}; font-size:30px; font-weight:900; letter-spacing:3px; }}
        QLabel#subtitle, QLabel#caption, QLabel.caption {{ color:{theme['muted']}; }}
        QLabel#bigNumber {{ font-size:42px; color:{theme['accent']}; font-weight:900; }}
        QLabel#unit {{ color:{theme['accent2']}; }}
        QFrame#dataCard {{ background:{theme['panel2']}; border:1px solid {theme['grid']}; border-radius:10px; padding:8px; }}
        QPushButton, QToolButton {{ background:{theme['panel2']}; color:{theme['text']}; border:1px solid {theme['accent']}; border-radius:6px; padding:8px 12px; font-weight:bold; }}
        QPushButton:hover, QToolButton:hover {{ background:{theme['accent']}; color:#001010; }}
        QCheckBox {{ color:{theme['accent2']}; font-weight:bold; }}
        QLabel#linkGood, QLabel#gpsGood {{ color:#49ff70; font-size:18px; font-weight:bold; }}
        QLabel#linkBad, QLabel#gpsBad {{ color:{theme['danger']}; font-size:18px; font-weight:bold; }}
        QLabel#gpsMedium {{ color:#ffd23f; font-size:18px; font-weight:bold; }}
        QLabel#rthArrow {{ color:{theme['accent2']}; font-size:64px; font-weight:bold; }}
        QTextEdit {{ background:#020809; border:1px solid {theme['grid']}; color:{theme['text']}; }}
        """)
        for plot in (self.alt_plot, self.speed_plot):
            plot.setBackground(theme["panel"])
            plot.getAxis("left").setPen(theme["accent"]); plot.getAxis("bottom").setPen(theme["accent"])
            plot.showGrid(x=True, y=True, alpha=0.25)

    def toggle_serial(self) -> None:
        if self.serial_thread and self.serial_thread.isRunning():
            self.serial_thread.stop(); self.serial_thread.wait(1500); self.serial_thread = None
            self.set_link(False); self.connect_action.setText("CONNECT LORA"); return
        port = self.settings.value("serial/port", "")
        if not port:
            self.open_settings(); port = self.settings.value("serial/port", "")
        if not port:
            QMessageBox.warning(self, "Serial port", "Select a serial port in Settings before connecting."); return
        self.serial_thread = TelemetrySerialThread(port, int(self.settings.value("serial/baud", 9600)), float(self.settings.value("serial/timeout", 5.0)))
        self.serial_thread.telemetry.connect(self.process_telemetry)
        self.serial_thread.link_changed.connect(self.set_link)
        self.serial_thread.error.connect(self.add_log)
        self.serial_thread.start(); self.connect_action.setText("DISCONNECT LORA")

    def process_telemetry(self, p: TelemetryPoint) -> None:
        if self.points:
            previous = self.points[-1]
            self.stats.total_distance_m += GeoMath.distance_m(previous.latitude, previous.longitude, p.latitude, p.longitude)
        self.points.append(p); self.recorder.add(p)
        self.stats.max_speed = max(self.stats.max_speed, p.speed)
        self.stats.max_altitude = max(self.stats.max_altitude, p.altitude)
        self.map.update_telemetry(p); self.flight_data.update_telemetry(p); self.compass.set_heading(p.heading)
        self.update_gps_quality(p.satellites)
        self.rssi_label.setText(f"RSSI: {p.rssi:.1f} dBm" if p.rssi is not None else "RSSI: -- dBm")
        self.snr_label.setText(f"SNR: {p.snr:.1f} dB" if p.snr is not None else "SNR: -- dB")
        if self.home:
            distance = GeoMath.distance_m(self.home.latitude, self.home.longitude, p.latitude, p.longitude)
            bearing = GeoMath.bearing_deg(p.latitude, p.longitude, self.home.latitude, self.home.longitude)
            self.home_distance.setText(f"{distance:.1f} m / {distance / 1000:.3f} km")
            self.bearing_home.setText(f"{bearing:03.0f}°")
            self.rth_arrow.setStyleSheet(f"transform: rotate({bearing}deg);")
            self.rth_arrow.setText(self.arrow_for_bearing(bearing))
        self.radar.update_points(self.home, p)
        self.refresh_plots(); self.refresh_stats()
        if p.satellites >= 4 and not self._gps_fix_announced:
            self._gps_fix_announced = True; self.audio.notify("GPS FIX ACQUIRED"); self.add_log("GPS FIX ACQUIRED")

    def update_gps_quality(self, satellites: int) -> None:
        if satellites <= 3:
            self.gps_quality.setText(f"GPS: BAD ({satellites} SAT)"); self.gps_quality.setObjectName("gpsBad")
        elif satellites <= 6:
            self.gps_quality.setText(f"GPS: MEDIUM ({satellites} SAT)"); self.gps_quality.setObjectName("gpsMedium")
        else:
            self.gps_quality.setText(f"GPS: GOOD ({satellites} SAT)"); self.gps_quality.setObjectName("gpsGood")
        self.gps_quality.style().unpolish(self.gps_quality); self.gps_quality.style().polish(self.gps_quality)

    def set_link(self, connected: bool) -> None:
        if connected == self.link_connected:
            return
        self.link_connected = connected
        self.link_label.setText("CONNECTED" if connected else "DISCONNECTED")
        self.link_label.setObjectName("linkGood" if connected else "linkBad")
        self.link_label.style().unpolish(self.link_label); self.link_label.style().polish(self.link_label)
        self.audio.notify("LORA CONNECTED" if connected else "LORA DISCONNECTED")
        self.add_log("LORA CONNECTED" if connected else "LORA DISCONNECTED")
        if not connected:
            self.audio.notify("SIGNAL LOST")

    def set_home(self) -> None:
        if not self.points:
            QMessageBox.information(self, "SET HOME", "No drone position has been received yet."); return
        self.home = self.points[0] if self.home is None else self.points[-1]
        self.map.set_home(self.home); self.radar.update_points(self.home, self.points[-1])
        self.add_log(f"HOME SET: {self.home.latitude:.6f}, {self.home.longitude:.6f}")

    def arrow_for_bearing(self, bearing: float) -> str:
        arrows = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]
        return arrows[int(((bearing + 22.5) % 360) // 45)]

    def refresh_plots(self) -> None:
        x = list(range(len(self.points)))
        self.alt_curve.setData(x, [p.altitude for p in self.points])
        self.speed_curve.setData(x, [p.speed for p in self.points])

    def refresh_stats(self) -> None:
        elapsed = self.stats.elapsed_seconds(); h, rem = divmod(elapsed, 3600); m, s = divmod(rem, 60)
        self.elapsed_label.setText(f"{h:02d}:{m:02d}:{s:02d}")
        d = self.stats.total_distance_m
        self.distance_label.setText(f"{d:.1f} m / {d / 1000:.3f} km")
        self.max_speed_label.setText(f"{self.stats.max_speed:.1f} km/h")
        self.max_alt_label.setText(f"{max(0.0, self.stats.max_altitude):.1f} m")

    def replay_mission(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Replay Mission", str(Path.cwd() / "missions"), "Mission JSON (telemetry.json);;CSV telemetry (telemetry.csv)")
        if not path:
            return
        loaded: list[TelemetryPoint] = []
        if path.endswith(".json"):
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            loaded = [TelemetryPoint(**item) for item in data.get("points", [])]
        else:
            with Path(path).open(newline="", encoding="utf-8") as f:
                loaded = [TelemetryPoint(**{**row, "latitude": float(row["latitude"]), "longitude": float(row["longitude"]), "altitude": float(row["altitude"]), "speed": float(row["speed"]), "heading": float(row["heading"]), "satellites": int(row["satellites"]), "rssi": float(row["rssi"]) if row.get("rssi") else None, "snr": float(row["snr"]) if row.get("snr") else None}) for row in csv.DictReader(f)]
        self.add_log(f"REPLAY LOADED: {len(loaded)} points from {path}")
        self._replay_points = loaded; self._replay_index = 0
        self._replay_timer = QTimer(self); self._replay_timer.timeout.connect(self._replay_next); self._replay_timer.start(500)

    def _replay_next(self) -> None:
        if self._replay_index >= len(self._replay_points):
            self._replay_timer.stop(); self.add_log("REPLAY COMPLETE"); return
        self.process_telemetry(self._replay_points[self._replay_index]); self._replay_index += 1

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.theme_name = self.settings.value("ui/theme", "Dark Tactical")
            self.apply_theme(self.theme_name)

    def add_log(self, message: str) -> None:
        self.log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def closeEvent(self, event) -> None:
        if self.serial_thread and self.serial_thread.isRunning():
            self.serial_thread.stop(); self.serial_thread.wait(1500)
        self.recorder.close()
        super().closeEvent(event)


def main() -> int:
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME); app.setOrganizationName(ORGANIZATION)
    splash = Splash(); splash.show(); app.processEvents()
    QTimer.singleShot(1100, splash.close)
    window = MainWindow()
    QTimer.singleShot(1150, window.show)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
