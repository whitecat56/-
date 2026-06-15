"""CSV/JSON telemetry logger."""
from __future__ import annotations

import csv, json
from pathlib import Path
from .telemetry_parser import TelemetryPoint

class TelemetryLogger:
    def __init__(self, directory: Path | str = "logs") -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.points: list[TelemetryPoint] = []

    def add(self, point: TelemetryPoint) -> None:
        self.points.append(point)

    def clear(self) -> None:
        self.points.clear()

    def export_csv(self, path: Path | str) -> None:
        with Path(path).open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["Timestamp", "Latitude", "Longitude", "Altitude"])
            writer.writeheader()
            for point in self.points:
                writer.writerow(point.as_dict())

    def export_json(self, path: Path | str) -> None:
        Path(path).write_text(json.dumps([p.as_dict() for p in self.points], indent=2), encoding="utf-8")
