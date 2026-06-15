"""Qt timer based replay system for recorded JSONL sessions."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from core.telemetry_parser import TelemetryPoint

class ReplayPlayer(QObject):
    point = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent); self.timer = QTimer(self); self.timer.timeout.connect(self._tick); self.points: list[TelemetryPoint] = []; self.index = 0; self.speed = 1.0

    def load(self, path: str | Path) -> int:
        self.stop(); self.points.clear(); self.index = 0
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip(): continue
            row = json.loads(line)
            ts = datetime.fromisoformat(row["Timestamp"])
            self.points.append(TelemetryPoint(ts, float(row["Latitude"]), float(row["Longitude"]), float(row["Altitude"])))
        return len(self.points)

    def play(self, speed: float = 1.0) -> None:
        self.speed = max(0.25, speed)
        self.timer.start(max(20, int(1000 / self.speed)))

    def pause(self) -> None:
        self.timer.stop()

    def stop(self) -> None:
        self.timer.stop(); self.index = 0

    def _tick(self) -> None:
        if self.index >= len(self.points):
            self.timer.stop(); self.finished.emit(); return
        self.point.emit(self.points[self.index]); self.index += 1
