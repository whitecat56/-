"""Mission recorder writing every real telemetry packet to common GIS formats."""
from __future__ import annotations

import csv
import json
import time
from pathlib import Path

from telemetry import TelemetryPacket


class MissionRecorder:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.session_dir = self.base_dir / time.strftime("mission_%Y%m%d_%H%M%S")
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.packets: list[TelemetryPacket] = []
        self.csv_path = self.session_dir / "telemetry.csv"
        with self.csv_path.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(list(TelemetryPacket.__dataclass_fields__.keys()))

    def append(self, packet: TelemetryPacket) -> None:
        self.packets.append(packet)
        with self.csv_path.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([packet.to_dict()[k] for k in TelemetryPacket.__dataclass_fields__.keys()])
        self._write_json(); self._write_gpx(); self._write_kml()

    def _write_json(self) -> None:
        (self.session_dir / "telemetry.json").write_text(json.dumps([p.to_dict() for p in self.packets], indent=2), encoding="utf-8")

    def _write_gpx(self) -> None:
        pts = [f'      <trkpt lat="{p.latitude:.8f}" lon="{p.longitude:.8f}"><ele>{p.altitude:.2f}</ele><time>{p.timestamp:.3f}</time></trkpt>' for p in self.packets]
        text = "\n".join(['<?xml version="1.0" encoding="UTF-8"?>','<gpx version="1.1" creator="Aircraft Command Center" xmlns="http://www.topografix.com/GPX/1/1">','  <trk><name>Aircraft mission</name><trkseg>',*pts,'  </trkseg></trk>','</gpx>'])
        (self.session_dir / "track.gpx").write_text(text + "\n", encoding="utf-8")

    def _write_kml(self) -> None:
        coords = " ".join([f"{p.longitude:.8f},{p.latitude:.8f},{p.altitude:.2f}" for p in self.packets])
        text = f'<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark><name>Aircraft mission</name><LineString><altitudeMode>absolute</altitudeMode><coordinates>{coords}</coordinates></LineString></Placemark></Document></kml>\n'
        (self.session_dir / "track.kml").write_text(text, encoding="utf-8")
