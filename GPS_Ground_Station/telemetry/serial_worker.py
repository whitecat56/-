"""Threaded serial telemetry reader with robust parsing and reconnect.

All serial I/O lives inside this QThread so the Qt GUI thread remains smooth.
The worker accepts:

* base packet: latitude,longitude,altitude,speed,heading,satellites
* extended packet: base + rssi,snr,voltage,current,mah,pitch,roll,yaw,
  temperature,pressure,flightMode,packetCounter[,gpsFix]
"""
from __future__ import annotations

import csv
import logging
import time
from typing import Optional

from PyQt6.QtCore import QSettings, QThread, pyqtSignal
import serial
from serial.tools import list_ports

from .packet import TelemetryPacket, parse_gps_fix


class SerialWorker(QThread):
    """Background serial reader that emits real decoded telemetry packets."""

    packet_received = pyqtSignal(object)
    status_changed = pyqtSignal(bool, str)
    log_message = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, port: str, baudrate: int = 9600, reconnect: bool = True, parent=None) -> None:
        super().__init__(parent)
        self.port = port
        self.baudrate = baudrate
        self.reconnect = reconnect
        self._running = False
        self._serial: Optional[serial.Serial] = None
        self._last_packet: Optional[TelemetryPacket] = None
        self._packet_times: list[float] = []

    @staticmethod
    def available_ports() -> list[str]:
        """Return visible serial ports sorted by operating-system device name."""
        return [p.device for p in sorted(list_ports.comports(), key=lambda item: item.device)]

    @staticmethod
    def baudrates() -> list[int]:
        """Common Arduino and LoRa receiver baudrates."""
        return [9600, 19200, 38400, 57600, 115200, 230400]

    @staticmethod
    def settings() -> QSettings:
        return QSettings("AircraftCommandCenter", "GroundControlStation")

    def stop(self) -> None:
        """Request a clean thread shutdown."""
        self._running = False
        if self._serial and self._serial.is_open:
            self._serial.close()

    def run(self) -> None:
        """Connect, read, reconnect, and never block the GUI thread."""
        self._running = True
        while self._running:
            try:
                self._serial = serial.Serial(self.port, self.baudrate, timeout=0.15)
                self.settings().setValue("last_port", self.port)
                self.settings().setValue("baudrate", self.baudrate)
                self.status_changed.emit(True, f"Connected to {self.port} @ {self.baudrate}")
                self._read_loop()
            except serial.SerialException as exc:
                self.status_changed.emit(False, f"Serial unavailable: {exc}")
                self.error_occurred.emit(str(exc))
            finally:
                if self._serial and self._serial.is_open:
                    self._serial.close()
            if self._running and self.reconnect:
                self.log_message.emit("Reconnecting serial link in 2 seconds")
                self.msleep(2000)
            else:
                break
        self.status_changed.emit(False, "Disconnected")

    def _read_loop(self) -> None:
        assert self._serial is not None
        while self._running and self._serial.is_open:
            raw = self._serial.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", errors="ignore").strip()
            packet = self._parse_line(line)
            if packet is not None:
                self.packet_received.emit(packet)

    def _parse_line(self, line: str) -> Optional[TelemetryPacket]:
        """Parse one CSV telemetry line and reject malformed data safely."""
        cleaned = line.replace(";", ",").replace("\t", ",")
        try:
            fields = [value.strip() for value in next(csv.reader([cleaned]))]
            fields = [value for value in fields if value != ""]
            if len(fields) not in (6, 18, 19):
                self.log_message.emit(f"Ignored packet with {len(fields)} fields: {line}")
                return None

            now = time.time()
            packet = TelemetryPacket(
                latitude=float(fields[0]),
                longitude=float(fields[1]),
                altitude=float(fields[2]),
                speed=float(fields[3]),
                heading=float(fields[4]),
                satellites=int(float(fields[5])),
                rssi=float(fields[6]) if len(fields) >= 18 else None,
                snr=float(fields[7]) if len(fields) >= 18 else None,
                voltage=float(fields[8]) if len(fields) >= 18 else None,
                current=float(fields[9]) if len(fields) >= 18 else None,
                mah=float(fields[10]) if len(fields) >= 18 else None,
                pitch=float(fields[11]) if len(fields) >= 18 else None,
                roll=float(fields[12]) if len(fields) >= 18 else None,
                yaw=float(fields[13]) if len(fields) >= 18 else None,
                temperature=float(fields[14]) if len(fields) >= 18 else None,
                pressure=float(fields[15]) if len(fields) >= 18 else None,
                flight_mode=fields[16] if len(fields) >= 18 else None,
                packet_counter=int(float(fields[17])) if len(fields) >= 18 else None,
                gps_fix=parse_gps_fix(fields[18]) if len(fields) == 19 else None,
                timestamp=now,
            )
            if self._last_packet:
                dt = max(0.001, packet.timestamp - self._last_packet.timestamp)
                packet.vertical_speed = (packet.altitude - self._last_packet.altitude) / dt
            self._packet_times = [t for t in self._packet_times if now - t <= 5.0]
            self._packet_times.append(now)
            packet.packet_rate_hz = len(self._packet_times) / 5.0
            self._last_packet = packet
            return packet if packet.is_valid_coordinates() else None
        except (ValueError, csv.Error) as exc:
            logging.getLogger("AircraftCommandCenter").warning("Parser rejected %s: %s", line, exc)
            self.log_message.emit(f"Unrecognized telemetry: {line}")
            return None
