"""Mission replay utilities for recorded JSON missions."""
from __future__ import annotations

import json
from pathlib import Path

from telemetry import TelemetryPacket, parse_gps_fix


def load_json_mission(path: Path) -> list[TelemetryPacket]:
    """Load recorder JSON output as telemetry packets for map replay."""
    data = json.loads(path.read_text(encoding="utf-8"))
    packets: list[TelemetryPacket] = []
    for item in data:
        if "gps_fix" in item:
            item["gps_fix"] = parse_gps_fix(item["gps_fix"])
        packets.append(TelemetryPacket(**item))
    return packets
