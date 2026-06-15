"""Flight analytics and link quality statistics for VAYLLEM UAV Command Center V2."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from typing import Iterable

from core.telemetry_parser import TelemetryPoint

@dataclass(slots=True)
class FlightSnapshot:
    packets: int
    packet_loss_percent: float
    distance_km: float
    min_altitude: float | None
    max_altitude: float | None
    average_altitude: float | None
    vertical_speed_mps: float
    elapsed_seconds: float
    signal_quality: int

class FlightStatistics:
    """Maintains live mission analytics without blocking the UI thread."""

    def __init__(self, expected_hz: float = 1.0) -> None:
        self.expected_hz = max(expected_hz, 0.1)
        self.reset()

    def reset(self) -> None:
        self.points: list[TelemetryPoint] = []
        self.started_at: datetime | None = None
        self.last_at: datetime | None = None
        self.last_rssi: int | None = None

    def add_point(self, point: TelemetryPoint, rssi: int | None = None) -> FlightSnapshot:
        if self.started_at is None:
            self.started_at = point.timestamp
        self.last_at = point.timestamp
        self.points.append(point)
        if rssi is not None:
            self.last_rssi = rssi
        return self.snapshot()

    def snapshot(self) -> FlightSnapshot:
        alts = [p.altitude for p in self.points]
        elapsed = self.elapsed_seconds
        expected = max(int(elapsed * self.expected_hz), len(self.points), 1)
        loss = max(0.0, (expected - len(self.points)) / expected * 100.0)
        return FlightSnapshot(
            packets=len(self.points),
            packet_loss_percent=loss,
            distance_km=self.distance_km,
            min_altitude=min(alts) if alts else None,
            max_altitude=max(alts) if alts else None,
            average_altitude=sum(alts) / len(alts) if alts else None,
            vertical_speed_mps=self.vertical_speed_mps,
            elapsed_seconds=elapsed,
            signal_quality=self.signal_quality,
        )

    @property
    def elapsed_seconds(self) -> float:
        if not self.started_at:
            return 0.0
        end = self.last_at or datetime.now(timezone.utc)
        return max(0.0, (end - self.started_at).total_seconds())

    @property
    def distance_km(self) -> float:
        return sum(self._haversine(a, b) for a, b in zip(self.points, self.points[1:]))

    @property
    def vertical_speed_mps(self) -> float:
        if len(self.points) < 2:
            return 0.0
        a, b = self.points[-2], self.points[-1]
        dt = max((b.timestamp - a.timestamp).total_seconds(), 0.001)
        return (b.altitude - a.altitude) / dt

    @property
    def heading_deg(self) -> float:
        if len(self.points) < 2:
            return 0.0
        return self._bearing(self.points[-2], self.points[-1])

    @property
    def signal_quality(self) -> int:
        if self.last_rssi is None:
            snap = self.snapshot_from_packets_only()
            return max(0, min(100, int(100 - snap.packet_loss_percent)))
        return max(0, min(100, int((self.last_rssi + 120) / 70 * 100)))

    def snapshot_from_packets_only(self) -> FlightSnapshot:
        elapsed = self.elapsed_seconds
        expected = max(int(elapsed * self.expected_hz), len(self.points), 1)
        loss = max(0.0, (expected - len(self.points)) / expected * 100.0)
        return FlightSnapshot(len(self.points), loss, self.distance_km, None, None, None, self.vertical_speed_mps, elapsed, int(100 - loss))

    @staticmethod
    def _haversine(a: TelemetryPoint, b: TelemetryPoint) -> float:
        radius_km = 6371.0088
        lat1, lat2 = math.radians(a.latitude), math.radians(b.latitude)
        dlat = math.radians(b.latitude - a.latitude)
        dlon = math.radians(b.longitude - a.longitude)
        h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return 2 * radius_km * math.atan2(math.sqrt(h), math.sqrt(1 - h))

    @staticmethod
    def _bearing(a: TelemetryPoint, b: TelemetryPoint) -> float:
        lat1, lat2 = math.radians(a.latitude), math.radians(b.latitude)
        dlon = math.radians(b.longitude - a.longitude)
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        return (math.degrees(math.atan2(y, x)) + 360) % 360
