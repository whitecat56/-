"""Robust parser for Arduino GPS telemetry text."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re

@dataclass(slots=True)
class TelemetryPoint:
    timestamp: datetime
    latitude: float
    longitude: float
    altitude: float

    def as_dict(self) -> dict[str, str | float]:
        return {
            "Timestamp": self.timestamp.isoformat(),
            "Latitude": self.latitude,
            "Longitude": self.longitude,
            "Altitude": self.altitude,
        }

class TelemetryParser:
    """Parses either three Arduino label lines or compact CSV packets."""
    _lat = re.compile(r"lat(?:itude)?\s*[:=]\s*([-+]?\d+(?:\.\d+)?)", re.I)
    _lon = re.compile(r"lon(?:gitude)?\s*[:=]\s*([-+]?\d+(?:\.\d+)?)", re.I)
    _alt = re.compile(r"alt(?:itude)?\s*[:=]\s*([-+]?\d+(?:\.\d+)?)", re.I)

    def __init__(self) -> None:
        self._pending: dict[str, float] = {}

    def feed_line(self, line: str) -> TelemetryPoint | None:
        text = line.strip()
        if not text:
            return None
        csv_point = self._parse_csv(text)
        if csv_point:
            self._pending.clear()
            return csv_point
        for key, pattern in (("latitude", self._lat), ("longitude", self._lon), ("altitude", self._alt)):
            match = pattern.search(text)
            if match:
                self._pending[key] = float(match.group(1))
        if {"latitude", "longitude", "altitude"}.issubset(self._pending):
            point = TelemetryPoint(datetime.now(timezone.utc), self._pending["latitude"], self._pending["longitude"], self._pending["altitude"])
            self._pending.clear()
            return point
        return None

    def _parse_csv(self, text: str) -> TelemetryPoint | None:
        parts = [p.strip() for p in text.split(",")]
        if len(parts) < 3:
            return None
        try:
            lat, lon, alt = map(float, parts[:3])
        except ValueError:
            return None
        return TelemetryPoint(datetime.now(timezone.utc), lat, lon, alt)
