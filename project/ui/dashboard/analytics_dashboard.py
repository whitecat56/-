"""Flight analytics dashboard widgets."""
from __future__ import annotations
from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
from core.statistics import FlightSnapshot

class StatTile(QFrame):
    def __init__(self, title: str, unit: str = "") -> None:
        super().__init__(); self.setObjectName("StatTile"); layout=QVBoxLayout(self); self.title=QLabel(title); self.value=QLabel("--"); self.unit=QLabel(unit); self.value.setObjectName("StatValue"); layout.addWidget(self.title); layout.addWidget(self.value); layout.addWidget(self.unit)
    def set_value(self, value: str) -> None: self.value.setText(value)

class FlightAnalyticsDashboard(QFrame):
    def __init__(self) -> None:
        super().__init__(); self.setObjectName("GlassPanel"); grid=QGridLayout(self); title=QLabel("FLIGHT ANALYTICS"); title.setObjectName("PanelTitle"); grid.addWidget(title,0,0,1,3)
        self.tiles={
            "timer": StatTile("Flight Timer"), "distance": StatTile("Distance", "km"), "packets": StatTile("Packets"),
            "min_alt": StatTile("Min Alt", "m"), "avg_alt": StatTile("Avg Alt", "m"), "max_alt": StatTile("Max Alt", "m"),
            "vsi": StatTile("Vertical Speed", "m/s"), "loss": StatTile("Packet Loss", "%"), "quality": StatTile("GPS/Link Quality", "%"),
        }
        for i, tile in enumerate(self.tiles.values()): grid.addWidget(tile, 1 + i//3, i%3)
    def update_snapshot(self, s: FlightSnapshot) -> None:
        mins, secs = divmod(int(s.elapsed_seconds), 60); hrs, mins = divmod(mins, 60)
        self.tiles["timer"].set_value(f"{hrs:02d}:{mins:02d}:{secs:02d}")
        self.tiles["distance"].set_value(f"{s.distance_km:.3f}"); self.tiles["packets"].set_value(str(s.packets))
        self.tiles["min_alt"].set_value("--" if s.min_altitude is None else f"{s.min_altitude:.1f}")
        self.tiles["avg_alt"].set_value("--" if s.average_altitude is None else f"{s.average_altitude:.1f}")
        self.tiles["max_alt"].set_value("--" if s.max_altitude is None else f"{s.max_altitude:.1f}")
        self.tiles["vsi"].set_value(f"{s.vertical_speed_mps:+.2f}"); self.tiles["loss"].set_value(f"{s.packet_loss_percent:.1f}"); self.tiles["quality"].set_value(str(s.signal_quality))
