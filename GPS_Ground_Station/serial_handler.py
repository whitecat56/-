"""Serial communication layer for Arduino/HC-12 GPS telemetry.

The receiver Arduino can forward the original 12-byte C++ structure directly or
print comma/space separated text. This handler supports both formats so the PC
station remains usable while firmware evolves.
"""

from __future__ import annotations

import csv
import logging
import struct
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QSettings, QThread, pyqtSignal
import serial
from serial.tools import list_ports


@dataclass(slots=True)
class TelemetryPacket:
    """One decoded telemetry sample from the aircraft."""

    latitude: float
    longitude: float
    altitude: float
    speed: Optional[float] = None
    heading: Optional[float] = None
    battery_voltage: Optional[float] = None
    rssi: Optional[float] = None
    timestamp: float = 0.0

    def is_valid_gps(self) -> bool:
        """Return True when coordinates are inside valid GPS ranges."""
        return -90.0 <= self.latitude <= 90.0 and -180.0 <= self.longitude <= 180.0


class SerialWorker(QThread):
    """Background serial reader that emits decoded telemetry packets."""

    packet_received = pyqtSignal(object)
    status_changed = pyqtSignal(bool, str)
    log_message = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    STRUCT_SIZE = 12

    def __init__(self, port: str, baudrate: int = 9600, parent=None) -> None:
        super().__init__(parent)
        self.port = port
        self.baudrate = baudrate
        self._running = False
        self._serial: Optional[serial.Serial] = None
        self._binary_buffer = bytearray()
        self._line_buffer = bytearray()

    @staticmethod
    def available_ports() -> list[str]:
        """Return sorted COM ports currently visible to Windows/Linux/macOS."""
        return [port.device for port in sorted(list_ports.comports(), key=lambda p: p.device)]

    @staticmethod
    def save_last_port(port: str) -> None:
        """Persist the last selected COM port with QSettings."""
        QSettings("GPSGroundStation", "GroundStation").setValue("last_port", port)

    @staticmethod
    def load_last_port() -> str:
        """Load the previously selected COM port, if any."""
        return str(QSettings("GPSGroundStation", "GroundStation").value("last_port", ""))

    def stop(self) -> None:
        """Request thread shutdown and close the serial port."""
        self._running = False
        if self._serial and self._serial.is_open:
            self._serial.close()

    def run(self) -> None:
        """Open the serial port and decode incoming binary/text telemetry."""
        self._running = True
        try:
            self._serial = serial.Serial(self.port, self.baudrate, timeout=0.08)
            SerialWorker.save_last_port(self.port)
            self.status_changed.emit(True, f"Connected to {self.port} @ {self.baudrate}")
            self.log_message.emit(f"Serial link opened: {self.port}")
        except serial.SerialException as exc:
            self.status_changed.emit(False, "Connection failed")
            self.error_occurred.emit(f"Cannot open {self.port}: {exc}")
            return

        while self._running:
            try:
                chunk = self._serial.read(64)
                if chunk:
                    self._consume(chunk)
            except serial.SerialException as exc:
                self.error_occurred.emit(f"Serial error: {exc}")
                break
            except Exception as exc:  # Defensive: keep UI alive and log parser bugs.
                self.error_occurred.emit(f"Telemetry parser error: {exc}")

        if self._serial and self._serial.is_open:
            self._serial.close()
        self.status_changed.emit(False, "Disconnected")
        self.log_message.emit("Serial link closed")

    def _consume(self, chunk: bytes) -> None:
        """Route incoming bytes to text parser or binary structure parser."""
        if any(byte in chunk for byte in (10, 13)):
            for byte in chunk:
                if byte in (10, 13):
                    if self._line_buffer:
                        self._parse_text_line(bytes(self._line_buffer).decode("utf-8", errors="ignore"))
                        self._line_buffer.clear()
                else:
                    self._line_buffer.append(byte)
        else:
            self._binary_buffer.extend(chunk)
            while len(self._binary_buffer) >= self.STRUCT_SIZE:
                frame = bytes(self._binary_buffer[: self.STRUCT_SIZE])
                del self._binary_buffer[: self.STRUCT_SIZE]
                self._parse_binary_frame(frame)

    def _parse_binary_frame(self, frame: bytes) -> None:
        """Decode the Arduino `struct GPSData { float lat, lon, alt; }`."""
        for fmt in ("<fff", "fff"):
            lat, lon, alt = struct.unpack(fmt, frame)
            packet = TelemetryPacket(lat, lon, alt, timestamp=time.time())
            if packet.is_valid_gps():
                self.packet_received.emit(packet)
                return
        self.log_message.emit("Ignored invalid binary GPS frame")

    def _parse_text_line(self, line: str) -> None:
        """Decode CSV telemetry: lat,lon,alt[,speed,heading,battery,rssi]."""
        cleaned = line.strip().replace(";", ",").replace("\t", ",")
        if not cleaned:
            return
        try:
            values = [float(item.strip()) for item in next(csv.reader([cleaned])) if item.strip()]
            if len(values) < 3:
                self.log_message.emit(f"Ignored short telemetry line: {line}")
                return
            packet = TelemetryPacket(
                latitude=values[0], longitude=values[1], altitude=values[2],
                speed=values[3] if len(values) > 3 else None,
                heading=values[4] if len(values) > 4 else None,
                battery_voltage=values[5] if len(values) > 5 else None,
                rssi=values[6] if len(values) > 6 else None,
                timestamp=time.time(),
            )
            if packet.is_valid_gps():
                self.packet_received.emit(packet)
            else:
                self.log_message.emit(f"Invalid GPS coordinates: {line}")
        except ValueError:
            self.log_message.emit(f"Unrecognized telemetry line: {line}")


def configure_file_logger(log_dir: Path) -> logging.Logger:
    """Create a rotating plain-text log for operator and diagnostics events."""
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("GPSGroundStation")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(log_dir / "ground_station.log", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(handler)
    return logger
