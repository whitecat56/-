#!/usr/bin/env python3
"""Drone Command Center: PyQt6 ground control station for GPS + LoRa telemetry."""

from __future__ import annotations

import csv
import json
import math
import os
import re
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
from PyQt6.QtGui import QAction, QColor, QFont, QPainter, QPainterPath, QPen, QPolygonF, QRadialGradient
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
EXTENDED_PACKET = "latitude,longitude,altitude,speed,heading,satellites,rssi,snr,voltage,current,mah,pitch,roll"
DEFAULT_BATTERY_WARNING_V = 10.5
DEFAULT_DISTANCE_LIMIT_M = 1000.0
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
    voltage: Optional[float] = None
    current: Optional[float] = None
    mah_consumed: Optional[float] = None
    pitch: float = 0.0
    roll: float = 0.0

    @classmethod
    def from_line(cls, line: str) -> "TelemetryPoint":
        """Parse current and extended GPS/LoRa CSV telemetry.

        Compatible formats:
        - latitude,longitude,altitude,speed,heading,satellites
        - latitude,longitude,altitude,speed,heading,satellites,rssi,snr
        - latitude,longitude,altitude,speed,heading,satellites,rssi,snr,voltage,current,mAh,pitch,roll
        """
        packet = cls._extract_numeric_packet(line)
        parts = [part.strip() for part in packet.split(",")]
        if len(parts) < 6:
            raise ValueError("Telemetry packet must contain at least 6 comma-separated fields")

        def optional_float(index: int) -> Optional[float]:
            return float(parts[index]) if len(parts) > index and parts[index] else None

        point = cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            latitude=float(parts[0]),
            longitude=float(parts[1]),
            altitude=float(parts[2]),
            speed=float(parts[3]),
            heading=float(parts[4]) % 360.0,
            satellites=int(float(parts[5])),
            rssi=optional_float(6),
            snr=optional_float(7),
            voltage=optional_float(8),
            current=optional_float(9),
            mah_consumed=optional_float(10),
            pitch=optional_float(11) or 0.0,
            roll=optional_float(12) or 0.0,
        )
        point.validate()
        return point

    @staticmethod
    def _extract_numeric_packet(line: str) -> str:
        cleaned = line.strip()
        if not cleaned:
            raise ValueError("Telemetry packet is empty")
        numeric_csv = re.search(
            r"(-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*,"
            r"\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*,\s*\d+(?:\.\d+)?"
            r"(?:\s*,\s*-?\d+(?:\.\d+)?){0,7})",
            cleaned,
        )
        return numeric_csv.group(1) if numeric_csv else cleaned

    def validate(self) -> None:
        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError(f"Latitude out of range: {self.latitude}")
        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError(f"Longitude out of range: {self.longitude}")
        if self.satellites < 0:
            raise ValueError(f"Satellite count out of range: {self.satellites}")
        if self.voltage is not None and self.voltage < 0:
            raise ValueError(f"Battery voltage out of range: {self.voltage}")


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
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.directory: Optional[Path] = None
        self.csv_path: Optional[Path] = None
        self.json_path: Optional[Path] = None
        self.gpx_path: Optional[Path] = None
        self.kml_path: Optional[Path] = None
        self.points: list[TelemetryPoint] = []
        self._csv_file = None
        self._writer: Optional[csv.DictWriter] = None

    @property
    def active(self) -> bool:
        return self.directory is not None

    def start(self) -> None:
        if self.active:
            return
        mission_name = datetime.now().strftime("mission_%Y%m%d_%H%M%S")
        self.directory = self.root / mission_name
        self.directory.mkdir(parents=True, exist_ok=True)
        self.csv_path = self.directory / "telemetry.csv"
        self.json_path = self.directory / "telemetry.json"
        self.gpx_path = self.directory / "track.gpx"
        self.kml_path = self.directory / "track.kml"
        self._csv_file = self.csv_path.open("w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._csv_file, fieldnames=list(asdict(TelemetryPoint("", 0, 0, 0, 0, 0, 0)).keys()))
        self._writer.writeheader()
        self._csv_file.flush()
        self._write_json()
        self._write_gpx()
        self._write_kml()

    def add(self, point: TelemetryPoint) -> None:
        if not self.active:
            self.start()
        self.points.append(point)
        if self._writer and self._csv_file:
            self._writer.writerow(asdict(point))
            self._csv_file.flush()
        self._write_json()
        self._write_gpx()
        self._write_kml()

    def close(self) -> None:
        if self._csv_file and not self._csv_file.closed:
            self._csv_file.close()
        if self.active:
            self._write_json()
            self._write_gpx()
            self._write_kml()

    def _write_json(self) -> None:
        if not self.json_path:
            return
        payload = {"hardware": HARDWARE_INFO, "packet": EXTENDED_PACKET, "points": [asdict(p) for p in self.points]}
        self.json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_gpx(self) -> None:
        if not self.gpx_path:
            return
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

    def _write_kml(self) -> None:
        if not self.kml_path:
            return
        coordinates = " ".join(f"{p.longitude:.8f},{p.latitude:.8f},{p.altitude:.2f}" for p in self.points)
        placemarks = "\n".join(
            f'    <Placemark><name>{idx}</name><Point><coordinates>{p.longitude:.8f},{p.latitude:.8f},{p.altitude:.2f}</coordinates></Point></Placemark>'
            for idx, p in enumerate(self.points, start=1)
        )
        content = "\n".join([
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
            '  <name>UAV LoRa Mission</name>',
            '  <Placemark><name>Flight Track</name><LineString><tessellate>1</tessellate>',
            f'    <coordinates>{coordinates}</coordinates>',
            '  </LineString></Placemark>',
            placemarks,
            '</Document></kml>',
        ])
        self.kml_path.write_text(content, encoding="utf-8")


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
        p.setBrush(grad); p.setPen(QPen(QColor("#00ffc6"), 2)); p.drawEllipse(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2))
        p.translate(center); p.rotate(-self.heading)
        for deg in range(0, 360, 10):
            p.save(); p.rotate(deg)
            length = 18 if deg % 30 == 0 else 9
            p.setPen(QPen(QColor("#d8fff4"), 2 if deg % 30 == 0 else 1))
            p.drawLine(QPointF(0.0, -radius + 8), QPointF(0.0, -radius + 8 + length))
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
            p.drawEllipse(QRectF(center.x() - radius * factor, center.y() - radius * factor, radius * factor * 2, radius * factor * 2))
        p.drawLine(QPointF(center.x() - radius, center.y()), QPointF(center.x() + radius, center.y()))
        p.drawLine(QPointF(center.x(), center.y() - radius), QPointF(center.x(), center.y() + radius))
        p.setPen(QPen(QColor("#86ff4f"), 2)); p.setBrush(QColor("#86ff4f")); p.drawEllipse(QRectF(center.x() - 5, center.y() - 5, 10, 10))
        p.drawText(center + QPointF(8, -8), "HOME")
        if self.home and self.drone:
            dist = GeoMath.distance_m(self.home.latitude, self.home.longitude, self.drone.latitude, self.drone.longitude)
            bearing = GeoMath.bearing_deg(self.home.latitude, self.home.longitude, self.drone.latitude, self.drone.longitude)
            scaled = min(radius - 15, max(12, dist / max(1.0, dist) * min(radius - 15, dist / 8)))
            angle = math.radians(bearing - 90)
            point = QPointF(center.x() + math.cos(angle) * scaled, center.y() + math.sin(angle) * scaled)
            p.setPen(QPen(QColor("#00ffc6"), 2)); p.drawLine(center, point)
            p.setBrush(QColor("#00b7ff")); p.drawEllipse(QRectF(point.x() - 7, point.y() - 7, 14, 14)); p.drawText(point + QPointF(9, -9), f"DRONE {dist:.0f}m")


class SignalBarsWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.quality = 0
        self.setMinimumSize(150, 42)

    def set_quality(self, quality: int) -> None:
        self.quality = max(0, min(100, quality))
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        active = int(round(self.quality / 20.0))
        width = max(12.0, (self.width() - 28.0) / 5.0)
        for idx in range(5):
            height = 8.0 + idx * 6.0
            x = 8.0 + idx * (width + 4.0)
            y = self.height() - height - 6.0
            color = QColor("#49ff70" if self.quality >= 70 else "#ffd23f" if self.quality >= 40 else "#ff355e")
            if idx >= active:
                color = QColor(35, 58, 64)
            painter.setBrush(color)
            painter.setPen(QPen(QColor("#0b1b22"), 1))
            painter.drawRoundedRect(QRectF(x, y, width, height), 3.0, 3.0)
        painter.setPen(QColor("#d8fff4"))
        painter.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        painter.drawText(QRectF(0, 0, self.width(), 14), Qt.AlignmentFlag.AlignCenter, f"SIGNAL {self.quality}%")


class ArtificialHorizonWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.pitch = 0.0
        self.roll = 0.0
        self.setMinimumSize(260, 170)

    def set_attitude(self, pitch: float, roll: float) -> None:
        self.pitch = max(-45.0, min(45.0, pitch))
        self.roll = max(-90.0, min(90.0, roll))
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(8.0, 8.0, self.width() - 16.0, self.height() - 16.0)
        center = rect.center()
        painter.save()
        painter.setClipPath(self._rounded_path(rect, 14.0))
        painter.translate(center)
        painter.rotate(-self.roll)
        pitch_offset = self.pitch * 2.0
        painter.fillRect(QRectF(-self.width(), -self.height() * 2 + pitch_offset, self.width() * 2, self.height() * 2), QColor("#123e68"))
        painter.fillRect(QRectF(-self.width(), pitch_offset, self.width() * 2, self.height() * 2), QColor("#5a3a19"))
        painter.setPen(QPen(QColor("#ffffff"), 3))
        painter.drawLine(QPointF(-self.width(), pitch_offset), QPointF(self.width(), pitch_offset))
        painter.setPen(QPen(QColor("#d8fff4"), 1))
        for deg in range(-30, 31, 10):
            y = pitch_offset - deg * 2.0
            painter.drawLine(QPointF(-38.0, y), QPointF(38.0, y))
            painter.drawText(QRectF(42.0, y - 8.0, 30.0, 16.0), Qt.AlignmentFlag.AlignLeft, str(deg))
        painter.restore()
        painter.setPen(QPen(QColor("#00ffc6"), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 14.0, 14.0)
        painter.setPen(QPen(QColor("#ffb000"), 3))
        painter.drawLine(QPointF(center.x() - 42.0, center.y()), QPointF(center.x() - 10.0, center.y()))
        painter.drawLine(QPointF(center.x() + 10.0, center.y()), QPointF(center.x() + 42.0, center.y()))
        painter.drawLine(QPointF(center.x(), center.y() - 8.0), QPointF(center.x(), center.y() + 8.0))
        painter.setPen(QColor("#d8fff4"))
        painter.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        painter.drawText(QRectF(0, self.height() - 24.0, self.width(), 18.0), Qt.AlignmentFlag.AlignCenter, f"PITCH {self.pitch:+.1f}°  ROLL {self.roll:+.1f}°")

    def _rounded_path(self, rect: QRectF, radius: float) -> QPainterPath:
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        return path


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
        detected_port = MainWindow.detect_serial_port()
        for port in serial.tools.list_ports.comports():
            label = f"{port.device} — {port.description}"
            self.port.addItem(label, port.device)
        self.port.setCurrentText(settings.value("serial/port", detected_port))
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
        self.settings.setValue("serial/port", self.port.currentData() or self.port.currentText().split(" — ")[0])
        self.settings.setValue("serial/baud", self.baud.value())
        self.settings.setValue("serial/timeout", self.timeout.value())
        self.settings.setValue("ui/theme", self.theme.currentText())
        self.settings.setValue("missions/root", self.mission_root.text())
        super().accept()


class MapWidget(QWebEngineView):
    def __init__(self) -> None:
        super().__init__()
        self.map_name = ""
        cache_dir = Path.cwd() / "offline_map_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.page().profile().setCachePath(str(cache_dir))
        self.page().profile().setPersistentStoragePath(str(cache_dir))
        self.setHtml(self._build_html(41.311081, 69.240562), QUrl("https://local.gcs/"))

    def _build_html(self, lat: float, lon: float) -> str:
        fmap = folium.Map(location=[lat, lon], zoom_start=15, tiles="OpenStreetMap", control_scale=True)
        self.map_name = fmap.get_name()
        script = f"""
        <style>
        html, body, .folium-map {{ width:100%; height:100%; margin:0; background:#061014; }}
        .leaflet-control-attribution {{ background:rgba(6,16,20,.75)!important; color:#9ff!important; }}
        .drone-icon {{ width:40px; height:40px; transform-origin:50% 50%; filter:drop-shadow(0 0 10px #00ffc6); transition:transform .25s linear; }}
        .home-icon {{ color:#86ff4f; font:bold 20px monospace; text-shadow:0 0 8px #86ff4f; }}
        .wp-icon {{ color:#ffb000; font:bold 18px monospace; text-shadow:0 0 8px #ffb000; }}
        </style>
        <script>
        window.gcsState = {{ droneMarker:null, homeMarker:null, track:null, rth:null, follow:false, points:[], waypoints:[], wpLayer:null, wpLine:null }};
        function droneDiv(heading) {{
          return L.divIcon({{className:'', iconSize:[40,40], iconAnchor:[20,20], html:`<svg class="drone-icon" style="transform:rotate(${{heading}}deg)" viewBox="0 0 64 64"><path d="M32 2 L47 60 L32 50 L17 60 Z" fill="#00ffc6" stroke="#001" stroke-width="3"/><circle cx="32" cy="34" r="5" fill="#ffb000"/><path d="M32 2 L32 50" stroke="#ffffff" stroke-width="3"/></svg>`}});
        }}
        function homeDiv() {{ return L.divIcon({{className:'home-icon', iconSize:[60,24], iconAnchor:[30,12], html:'⌂ HOME'}}); }}
        function waypointDiv(i) {{ return L.divIcon({{className:'wp-icon', iconSize:[36,24], iconAnchor:[18,12], html:'◆ WP'+i}}); }}
        function ensureLayers() {{
          if (!window.gcsState.track) window.gcsState.track = L.polyline([], {{color:'#00ffc6', weight:3, opacity:.9}}).addTo({self.map_name});
          if (!window.gcsState.rth) window.gcsState.rth = L.polyline([], {{color:'#ffb000', weight:2, dashArray:'8 8', opacity:.95}}).addTo({self.map_name});
          if (!window.gcsState.wpLayer) window.gcsState.wpLayer = L.layerGroup().addTo({self.map_name});
          if (!window.gcsState.wpLine) window.gcsState.wpLine = L.polyline([], {{color:'#ffb000', weight:3, dashArray:'4 10', opacity:.95}}).addTo({self.map_name});
        }}
        window.setFollow = function(enabled) {{ window.gcsState.follow = enabled; }};
        window.centerDrone = function() {{ if (window.gcsState.droneMarker) {self.map_name}.panTo(window.gcsState.droneMarker.getLatLng()); }};
        function refreshWaypoints() {{
          ensureLayers(); window.gcsState.wpLayer.clearLayers();
          window.gcsState.waypoints.forEach((wp, idx) => L.marker([wp.latitude, wp.longitude], {{icon:waypointDiv(idx + 1)}}).addTo(window.gcsState.wpLayer));
          window.gcsState.wpLine.setLatLngs(window.gcsState.waypoints.map(wp => [wp.latitude, wp.longitude]));
        }}
        window.addWaypoint = function(lat, lon, alt) {{
          window.gcsState.waypoints.push({{latitude:lat, longitude:lon, altitude:alt || 0}}); refreshWaypoints();
        }};
        window.setWaypoints = function(points) {{ window.gcsState.waypoints = points || []; refreshWaypoints(); }};
        window.getWaypoints = function() {{ return JSON.stringify(window.gcsState.waypoints); }};
        {self.map_name}.on('click', function(e) {{ window.addWaypoint(e.latlng.lat, e.latlng.lng, 0); }});
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

    def add_waypoint(self, lat: float, lon: float, alt: float = 0.0) -> None:
        self.page().runJavaScript(f"window.addWaypoint({lat}, {lon}, {alt});")

    def set_waypoints(self, waypoints: list[dict[str, float]]) -> None:
        self.page().runJavaScript(f"window.setWaypoints({json.dumps(waypoints)});")

    def get_waypoints(self, callback) -> None:
        self.page().runJavaScript("window.getWaypoints();", callback)


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
        self._battery_warning_active = False
        self._distance_warning_active = False
        self._rth_recommendation = "WAITING GPS"
        self.distance_limit_m = float(self.settings.value("safety/distance_limit_m", DEFAULT_DISTANCE_LIMIT_M))
        self.battery_warning_v = float(self.settings.value("safety/battery_warning_v", DEFAULT_BATTERY_WARNING_V))
        self._sim_angle = 0.0
        self._sim_timer = QTimer(self)
        self._sim_timer.timeout.connect(self.emit_demo_packet)
        self._build_ui()
        self.apply_theme(self.theme_name)
        self.stats_timer = QTimer(self); self.stats_timer.timeout.connect(self.refresh_stats); self.stats_timer.start(1000)

    def _build_ui(self) -> None:
        toolbar = self.addToolBar("Mission")
        connect_action = QAction("CONNECT LORA", self); connect_action.triggered.connect(self.toggle_serial)
        replay_action = QAction("REPLAY MISSION", self); replay_action.triggered.connect(self.replay_mission)
        demo_action = QAction("DEMO GPS", self); demo_action.triggered.connect(self.toggle_demo)
        save_mission_action = QAction("SAVE MISSION", self); save_mission_action.triggered.connect(self.save_waypoint_mission)
        load_mission_action = QAction("LOAD MISSION", self); load_mission_action.triggered.connect(self.load_waypoint_mission)
        export_action = QAction("EXPORT CSV/GPX/KML", self); export_action.triggered.connect(self.open_mission_folder)
        fullscreen_action = QAction("TACTICAL MAP", self); fullscreen_action.triggered.connect(self.toggle_tactical_map)
        settings_action = QAction("SETTINGS", self); settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(connect_action); toolbar.addAction(replay_action); toolbar.addAction(demo_action); toolbar.addAction(save_mission_action); toolbar.addAction(load_mission_action); toolbar.addAction(export_action); toolbar.addAction(fullscreen_action); toolbar.addAction(settings_action)
        self.connect_action = connect_action
        self.demo_action = demo_action
        self.fullscreen_action = fullscreen_action

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
        add_wp_btn = QPushButton("ADD WP HERE"); add_wp_btn.clicked.connect(self.add_current_waypoint)
        controls.addWidget(self.follow); controls.addWidget(center_btn); controls.addWidget(home_btn); controls.addWidget(add_wp_btn); controls.addStretch()
        center.addLayout(controls)
        self.emergency_banner = QLabel("LOST SIGNAL — HOLD POSITION / RETURN HOME")
        self.emergency_banner.setObjectName("emergencyBanner")
        self.emergency_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.emergency_banner.hide()
        center.addWidget(self.emergency_banner)

        hardware = QGroupBox("HARDWARE")
        hw_layout = QFormLayout(hardware)
        for key, value in HARDWARE_INFO.items():
            hw_layout.addRow(QLabel(f"{key}:"), QLabel(value))
        left.addWidget(hardware)

        self.flight_data = FlightDataWidget(); left.addWidget(self.flight_data)
        self.compass = CompassWidget(); left.addWidget(self.compass)
        self.horizon = ArtificialHorizonWidget(); left.addWidget(self.horizon)
        self.radar = RadarWidget(); left.addWidget(self.radar)

        position_box = QGroupBox("GPS POSITION")
        position_layout = QFormLayout(position_box)
        self.latitude_label = QLabel("--.------")
        self.longitude_label = QLabel("--.------")
        self.utc_label = QLabel("--:--:-- UTC")
        self.maps_label = QLabel("Waiting for GPS fix")
        self.maps_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        position_layout.addRow("Latitude", self.latitude_label)
        position_layout.addRow("Longitude", self.longitude_label)
        position_layout.addRow("Packet time", self.utc_label)
        position_layout.addRow("Maps", self.maps_label)
        right.addWidget(position_box)

        self.link_label = QLabel("DISCONNECTED"); self.link_label.setObjectName("linkBad")
        self.gps_quality = QLabel("GPS: NO FIX"); self.gps_quality.setObjectName("gpsBad")
        self.rssi_label = QLabel("RSSI: -- dBm")
        self.snr_label = QLabel("SNR: -- dB")
        self.signal_bars = SignalBarsWidget()
        status_box = QGroupBox("LINK & GPS QUALITY")
        s_layout = QVBoxLayout(status_box); s_layout.addWidget(self.link_label); s_layout.addWidget(self.gps_quality); s_layout.addWidget(self.rssi_label); s_layout.addWidget(self.snr_label); s_layout.addWidget(self.signal_bars)
        right.addWidget(status_box)

        battery_box = QGroupBox("BATTERY TELEMETRY")
        b_layout = QFormLayout(battery_box)
        self.voltage_label = QLabel("-- V")
        self.current_label = QLabel("-- A")
        self.mah_label = QLabel("-- mAh")
        self.battery_state_label = QLabel("BATTERY: WAITING")
        self.battery_state_label.setObjectName("gpsMedium")
        b_layout.addRow("Voltage", self.voltage_label)
        b_layout.addRow("Current", self.current_label)
        b_layout.addRow("Consumed", self.mah_label)
        b_layout.addRow("Status", self.battery_state_label)
        right.addWidget(battery_box)

        nav_box = QGroupBox("HOME NAVIGATION")
        n_layout = QGridLayout(nav_box)
        self.home_distance = QLabel("-- m / -- km"); self.bearing_home = QLabel("--°"); self.rth_arrow = QLabel("▲"); self.rth_arrow.setObjectName("rthArrow")
        self.rth_recommendation_label = QLabel("WAITING GPS")
        self.rth_recommendation_label.setObjectName("gpsMedium")
        n_layout.addWidget(QLabel("Distance From Home"), 0, 0); n_layout.addWidget(self.home_distance, 0, 1)
        n_layout.addWidget(QLabel("Bearing To Home"), 1, 0); n_layout.addWidget(self.bearing_home, 1, 1)
        n_layout.addWidget(QLabel("Return To Home Arrow"), 2, 0); n_layout.addWidget(self.rth_arrow, 2, 1, Qt.AlignmentFlag.AlignCenter)
        n_layout.addWidget(QLabel("Recommendation"), 3, 0); n_layout.addWidget(self.rth_recommendation_label, 3, 1)
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
        QLabel#emergencyBanner {{ background:{theme['danger']}; color:#ffffff; border:2px solid #ffffff; border-radius:8px; padding:18px; font-size:28px; font-weight:900; letter-spacing:2px; }}
        QTextEdit {{ background:#020809; border:1px solid {theme['grid']}; color:{theme['text']}; }}
        """)
        for plot in (self.alt_plot, self.speed_plot):
            plot.setBackground(theme["panel"])
            plot.getAxis("left").setPen(theme["accent"]); plot.getAxis("bottom").setPen(theme["accent"])
            plot.showGrid(x=True, y=True, alpha=0.25)

    @staticmethod
    def detect_serial_port() -> str:
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            return ""
        preferred = [p for p in ports if any(token in (p.description or "").lower() for token in ("arduino", "ch340", "usb serial", "cp210", "nano"))]
        return (preferred[0] if preferred else ports[0]).device

    def toggle_serial(self) -> None:
        if self.serial_thread and self.serial_thread.isRunning():
            self.serial_thread.stop(); self.serial_thread.wait(1500); self.serial_thread = None
            self.set_link(False); self.connect_action.setText("CONNECT LORA"); return
        port = self.settings.value("serial/port", "") or self.detect_serial_port()
        if port and not self.settings.value("serial/port", ""):
            self.settings.setValue("serial/port", port)
            self.add_log(f"AUTO COM DETECTED: {port}")
        if not port:
            self.open_settings(); port = self.settings.value("serial/port", "")
        if not port:
            QMessageBox.warning(self, "Serial port", "Select a serial port in Settings before connecting."); return
        self.serial_thread = TelemetrySerialThread(port, int(self.settings.value("serial/baud", 9600)), float(self.settings.value("serial/timeout", 5.0)))
        self.serial_thread.telemetry.connect(self.process_telemetry)
        self.serial_thread.link_changed.connect(self.set_link)
        self.serial_thread.error.connect(self.add_log)
        self.serial_thread.start(); self.connect_action.setText("DISCONNECT LORA")

    def toggle_demo(self) -> None:
        if self._sim_timer.isActive():
            self._sim_timer.stop()
            self.demo_action.setText("DEMO GPS")
            self.set_link(False)
            self.add_log("DEMO GPS STOPPED")
            return
        self.set_link(True)
        self.demo_action.setText("STOP DEMO")
        self.add_log("DEMO GPS STARTED: simulated NEO-6M packets")
        self._sim_timer.start(1000)

    def emit_demo_packet(self) -> None:
        self._sim_angle = (self._sim_angle + 7.5) % 360.0
        radius = 0.0016
        angle = math.radians(self._sim_angle)
        center_lat, center_lon = 41.311081, 69.240562
        point = TelemetryPoint(
            timestamp=datetime.now(timezone.utc).isoformat(),
            latitude=center_lat + math.sin(angle) * radius,
            longitude=center_lon + math.cos(angle) * radius,
            altitude=450.0 + 24.0 * math.sin(angle * 0.7),
            speed=28.0 + 9.0 * abs(math.cos(angle)),
            heading=self._sim_angle,
            satellites=10,
            rssi=-72.0 + 4.0 * math.sin(angle),
            snr=8.5 + 1.5 * math.cos(angle),
            voltage=11.7 + 0.3 * math.sin(angle * 0.4),
            current=4.2 + 1.1 * abs(math.sin(angle)),
            mah_consumed=120.0 + self.stats.elapsed_seconds() * 1.4,
            pitch=8.0 * math.sin(angle * 1.4),
            roll=24.0 * math.sin(angle),
        )
        self.process_telemetry(point)

    def process_telemetry(self, p: TelemetryPoint) -> None:
        if self.points:
            previous = self.points[-1]
            self.stats.total_distance_m += GeoMath.distance_m(previous.latitude, previous.longitude, p.latitude, p.longitude)
        self.points.append(p)
        if p.satellites >= 4:
            self.recorder.add(p)
        self.stats.max_speed = max(self.stats.max_speed, p.speed)
        self.stats.max_altitude = max(self.stats.max_altitude, p.altitude)
        self.map.update_telemetry(p); self.flight_data.update_telemetry(p); self.compass.set_heading(p.heading); self.horizon.set_attitude(p.pitch, p.roll)
        self.update_position_labels(p)
        self.update_gps_quality(p.satellites)
        self.update_link_quality(p)
        self.update_battery(p)
        self.update_safety(p)
        if self.home:
            distance = GeoMath.distance_m(self.home.latitude, self.home.longitude, p.latitude, p.longitude)
            bearing = GeoMath.bearing_deg(p.latitude, p.longitude, self.home.latitude, self.home.longitude)
            self.home_distance.setText(f"{distance:.1f} m / {distance / 1000:.3f} km")
            self.bearing_home.setText(f"{bearing:03.0f}°")
            self.rth_arrow.setStyleSheet(f"transform: rotate({bearing}deg);")
            self.rth_arrow.setText(self.arrow_for_bearing(bearing))
            self.update_rth_recommendation(p, distance)
        self.radar.update_points(self.home, p)
        self.refresh_plots(); self.refresh_stats()
        if p.satellites >= 4 and not self._gps_fix_announced:
            self._gps_fix_announced = True; self.audio.notify("GPS FIX ACQUIRED"); self.add_log("GPS FIX ACQUIRED")

    def update_link_quality(self, p: TelemetryPoint) -> None:
        self.rssi_label.setText(f"RSSI: {p.rssi:.1f} dBm" if p.rssi is not None else "RSSI: -- dBm")
        self.snr_label.setText(f"SNR: {p.snr:.1f} dB" if p.snr is not None else "SNR: -- dB")
        if p.rssi is None and p.snr is None:
            quality = min(100, max(0, p.satellites * 10))
        else:
            rssi_quality = 100 if p.rssi is None else int(max(0, min(100, (p.rssi + 125.0) / 75.0 * 100.0)))
            snr_quality = 100 if p.snr is None else int(max(0, min(100, (p.snr + 20.0) / 35.0 * 100.0)))
            quality = int((rssi_quality * 0.65) + (snr_quality * 0.35))
        self.signal_bars.set_quality(quality)

    def update_battery(self, p: TelemetryPoint) -> None:
        self.voltage_label.setText(f"{p.voltage:.2f} V" if p.voltage is not None else "-- V")
        self.current_label.setText(f"{p.current:.2f} A" if p.current is not None else "-- A")
        self.mah_label.setText(f"{p.mah_consumed:.0f} mAh" if p.mah_consumed is not None else "-- mAh")
        low = p.voltage is not None and p.voltage <= self.battery_warning_v
        self.battery_state_label.setText("BATTERY: LOW — RETURN HOME" if low else "BATTERY: OK" if p.voltage is not None else "BATTERY: WAITING")
        self.battery_state_label.setObjectName("gpsBad" if low else "gpsGood" if p.voltage is not None else "gpsMedium")
        self.battery_state_label.style().unpolish(self.battery_state_label); self.battery_state_label.style().polish(self.battery_state_label)
        if low and not self._battery_warning_active:
            self._battery_warning_active = True
            self.audio.notify("BATTERY WARNING")
            self.add_log(f"BATTERY WARNING: {p.voltage:.2f} V")
        elif not low:
            self._battery_warning_active = False

    def update_safety(self, p: TelemetryPoint) -> None:
        if not self.home:
            return
        distance = GeoMath.distance_m(self.home.latitude, self.home.longitude, p.latitude, p.longitude)
        too_far = distance >= self.distance_limit_m
        if too_far and not self._distance_warning_active:
            self._distance_warning_active = True
            self.audio.notify("DISTANCE LIMIT")
            self.add_log(f"DISTANCE LIMIT WARNING: {distance:.1f} m")
        elif not too_far:
            self._distance_warning_active = False

    def update_rth_recommendation(self, p: TelemetryPoint, distance_m: float) -> None:
        low_battery = p.voltage is not None and p.voltage <= self.battery_warning_v
        if low_battery:
            recommendation = "RTH NOW: LOW BATTERY"
            object_name = "gpsBad"
        elif distance_m >= self.distance_limit_m:
            recommendation = "RTH NOW: DISTANCE LIMIT"
            object_name = "gpsBad"
        elif not self.link_connected:
            recommendation = "RTH: LINK LOST"
            object_name = "gpsBad"
        elif p.satellites < 6:
            recommendation = "HOLD: WEAK GPS"
            object_name = "gpsMedium"
        else:
            recommendation = "CONTINUE MISSION"
            object_name = "gpsGood"
        self.rth_recommendation_label.setText(recommendation)
        self.rth_recommendation_label.setObjectName(object_name)
        self.rth_recommendation_label.style().unpolish(self.rth_recommendation_label); self.rth_recommendation_label.style().polish(self.rth_recommendation_label)

    def update_position_labels(self, p: TelemetryPoint) -> None:
        self.latitude_label.setText(f"{p.latitude:.6f}°")
        self.longitude_label.setText(f"{p.longitude:.6f}°")
        packet_time = datetime.fromisoformat(p.timestamp).astimezone(timezone.utc).strftime("%H:%M:%S UTC")
        self.utc_label.setText(packet_time)
        self.maps_label.setText(f"https://maps.google.com/?q={p.latitude:.6f},{p.longitude:.6f}")

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
        self.emergency_banner.setVisible(not connected and bool(self.points))
        if not connected:
            self.signal_bars.set_quality(0)
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

    def add_current_waypoint(self) -> None:
        if not self.points:
            QMessageBox.information(self, "Waypoint", "No GPS position has been received yet.")
            return
        p = self.points[-1]
        self.map.add_waypoint(p.latitude, p.longitude, p.altitude)
        self.add_log(f"WAYPOINT ADDED: {p.latitude:.6f}, {p.longitude:.6f}")

    def save_waypoint_mission(self) -> None:
        self.map.get_waypoints(self._save_waypoints_json)

    def _save_waypoints_json(self, payload: str) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Mission", str(Path.cwd() / "mission_plan.json"), "Mission plan (*.json)")
        if not path:
            return
        waypoints = json.loads(payload or "[]")
        Path(path).write_text(json.dumps({"created": datetime.now(timezone.utc).isoformat(), "waypoints": waypoints}, indent=2), encoding="utf-8")
        self.add_log(f"MISSION SAVED: {len(waypoints)} waypoints -> {path}")

    def load_waypoint_mission(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load Mission", str(Path.cwd()), "Mission plan (*.json)")
        if not path:
            return
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        waypoints = data.get("waypoints", []) if isinstance(data, dict) else data
        self.map.set_waypoints(waypoints)
        self.add_log(f"MISSION LOADED: {len(waypoints)} waypoints from {path}")

    def open_mission_folder(self) -> None:
        target = self.recorder.directory or self.recorder.root
        target.mkdir(parents=True, exist_ok=True)
        webbrowser.open(target.as_uri())

    def toggle_tactical_map(self) -> None:
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_action.setText("TACTICAL MAP")
        else:
            self.showFullScreen()
            self.fullscreen_action.setText("EXIT TACTICAL")

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
                loaded = []
                for row in csv.DictReader(f):
                    row.update({
                        "latitude": float(row["latitude"]),
                        "longitude": float(row["longitude"]),
                        "altitude": float(row["altitude"]),
                        "speed": float(row["speed"]),
                        "heading": float(row["heading"]),
                        "satellites": int(float(row["satellites"])),
                        "rssi": float(row["rssi"]) if row.get("rssi") else None,
                        "snr": float(row["snr"]) if row.get("snr") else None,
                        "voltage": float(row["voltage"]) if row.get("voltage") else None,
                        "current": float(row["current"]) if row.get("current") else None,
                        "mah_consumed": float(row["mah_consumed"]) if row.get("mah_consumed") else None,
                        "pitch": float(row["pitch"]) if row.get("pitch") else 0.0,
                        "roll": float(row["roll"]) if row.get("roll") else 0.0,
                    })
                    loaded.append(TelemetryPoint(**row))
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
        if self._sim_timer.isActive():
            self._sim_timer.stop()
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
