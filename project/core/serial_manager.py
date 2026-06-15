"""Non-blocking PyQt serial telemetry reader."""
from __future__ import annotations

import time
from PyQt6.QtCore import QThread, pyqtSignal
from serial import Serial, SerialException
from serial.tools import list_ports
from .telemetry_parser import TelemetryParser, TelemetryPoint

class SerialManager(QThread):
    telemetry_received = pyqtSignal(object)
    raw_received = pyqtSignal(str)
    error = pyqtSignal(str)
    connected_changed = pyqtSignal(bool)

    def __init__(self, port: str, baudrate: int = 9600, parent=None) -> None:
        super().__init__(parent)
        self.port = port
        self.baudrate = baudrate
        self._running = False
        self._parser = TelemetryParser()

    @staticmethod
    def available_ports() -> list[str]:
        ports = [p.device for p in list_ports.comports()]
        return ports or [f"COM{i}" for i in range(1, 6)]

    @staticmethod
    def baudrates() -> list[int]:
        return [9600, 19200, 38400, 57600, 115200]

    def stop(self) -> None:
        self._running = False
        self.wait(1500)

    def run(self) -> None:
        self._running = True
        try:
            with Serial(self.port, self.baudrate, timeout=0.2) as serial:
                self.connected_changed.emit(True)
                while self._running:
                    line = serial.readline().decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue
                    self.raw_received.emit(line)
                    point = self._parser.feed_line(line)
                    if isinstance(point, TelemetryPoint):
                        self.telemetry_received.emit(point)
        except SerialException as exc:
            self.error.emit(str(exc))
        finally:
            self.connected_changed.emit(False)
            time.sleep(0.05)
