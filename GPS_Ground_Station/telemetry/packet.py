"""Telemetry packet model and derived values for the Aircraft Command Center.

The UI never fabricates telemetry. Optional fields stay ``None`` until the
Arduino/LoRa stream sends them, and every widget decides how to display missing
real data. The dataclass supports the legacy six-field packet and the extended
professional packet described in the project requirements.
"""
from __future__ import annotations

import math
import time
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Optional


class GpsFix(str, Enum):
    """Human-readable GPS fix states used by the status banner."""

    NO_FIX = "NO FIX"
    FIX_2D = "2D FIX"
    FIX_3D = "3D FIX"
    DGPS = "DGPS"
    RTK = "RTK"


@dataclass(slots=True)
class TelemetryPacket:
    """One decoded telemetry sample from the aircraft.

    Required fields are present in both supported packet formats. Optional
    fields become available when the extended Arduino packet is transmitted:
    ``rssi,snr,voltage,current,mah,pitch,roll,yaw,temperature,pressure,
    flightMode,packetCounter``.
    """

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
    mah: Optional[float] = None
    pitch: Optional[float] = None
    roll: Optional[float] = None
    yaw: Optional[float] = None
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    flight_mode: Optional[str] = None
    packet_counter: Optional[int] = None
    gps_fix: Optional[GpsFix] = None
    timestamp: float = 0.0
    vertical_speed: float = 0.0
    packet_rate_hz: float = 0.0

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = time.time()
        self.heading %= 360.0
        if self.gps_fix is None:
            self.gps_fix = self.derive_gps_fix()

    def is_valid_coordinates(self) -> bool:
        """Return ``True`` when coordinates are in legal WGS84 ranges."""
        return -90.0 <= self.latitude <= 90.0 and -180.0 <= self.longitude <= 180.0

    def has_gps_fix(self) -> bool:
        """Return ``True`` only when the packet is usable for navigation."""
        return self.is_valid_coordinates() and self.gps_fix is not GpsFix.NO_FIX

    def derive_gps_fix(self) -> GpsFix:
        """Infer GPS fix from satellite count when firmware does not send one."""
        if self.satellites <= 0 or not self.is_valid_coordinates():
            return GpsFix.NO_FIX
        if self.flight_mode and "RTK" in self.flight_mode.upper():
            return GpsFix.RTK
        if self.flight_mode and "DGPS" in self.flight_mode.upper():
            return GpsFix.DGPS
        if self.satellites >= 4:
            return GpsFix.FIX_3D
        return GpsFix.FIX_2D

    def link_quality(self) -> Optional[int]:
        """Calculate a conservative 0-100% link score from RSSI and SNR."""
        if self.rssi is None and self.snr is None:
            return None
        rssi_q = 100 if self.rssi is None else max(0, min(100, int((self.rssi + 120.0) / 75.0 * 100.0)))
        snr_q = 100 if self.snr is None else max(0, min(100, int((self.snr + 20.0) / 32.0 * 100.0)))
        rate_q = max(0, min(100, int(self.packet_rate_hz / 5.0 * 100.0))) if self.packet_rate_hz else 100
        return int(rssi_q * 0.50 + snr_q * 0.30 + rate_q * 0.20)

    def battery_percent(self, cells: int = 3) -> Optional[int]:
        """Estimate LiPo remaining percentage from voltage per cell."""
        if self.voltage is None:
            return None
        per_cell = self.voltage / max(1, cells)
        pct = (per_cell - 3.3) / (4.2 - 3.3) * 100.0
        return max(0, min(100, int(pct)))

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["gps_fix"] = self.gps_fix.value if isinstance(self.gps_fix, GpsFix) else self.gps_fix
        return data


def parse_gps_fix(value: str | float | int | None) -> Optional[GpsFix]:
    """Convert optional firmware fix code/name to :class:`GpsFix`."""
    if value is None or value == "":
        return None
    text = str(value).strip().upper().replace("_", " ")
    numeric = {"0": GpsFix.NO_FIX, "1": GpsFix.FIX_2D, "2": GpsFix.FIX_3D, "3": GpsFix.DGPS, "4": GpsFix.RTK}
    aliases = {"NO FIX": GpsFix.NO_FIX, "2D FIX": GpsFix.FIX_2D, "3D FIX": GpsFix.FIX_3D, "DGPS": GpsFix.DGPS, "RTK": GpsFix.RTK}
    return numeric.get(text) or aliases.get(text)


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two WGS84 points in meters."""
    r = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial bearing from the first WGS84 point to the second."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    y = math.sin(dlambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0
