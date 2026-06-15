from __future__ import annotations
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout

class TelemetryCard(QFrame):
    def __init__(self, title: str, unit: str = "") -> None:
        super().__init__()
        self.setObjectName("TelemetryCard")
        layout = QVBoxLayout(self)
        self.title = QLabel(title)
        self.title.setObjectName("CardTitle")
        self.value = QLabel("--")
        self.value.setObjectName("CardValue")
        self.unit = QLabel(unit)
        self.unit.setObjectName("CardUnit")
        layout.addWidget(self.title); layout.addWidget(self.value); layout.addWidget(self.unit)
    def set_value(self, value: str) -> None:
        self.value.setText(value)

class TelemetryPanel(QFrame):
    def __init__(self) -> None:
        super().__init__(); self.setObjectName("GlassPanel")
        layout = QVBoxLayout(self)
        title = QLabel("GPS TELEMETRY"); title.setObjectName("PanelTitle")
        self.fix = QLabel("NO FIX"); self.fix.setObjectName("NoFix")
        self.lat = TelemetryCard("Latitude", "deg")
        self.lon = TelemetryCard("Longitude", "deg")
        self.alt = TelemetryCard("Altitude", "m")
        layout.addWidget(title); layout.addWidget(self.fix)
        for w in (self.lat, self.lon, self.alt): layout.addWidget(w)
        layout.addStretch()
    def update_values(self, lat: float, lon: float, alt: float) -> None:
        self.fix.setText("GPS FIX"); self.fix.setObjectName("GpsFix"); self.fix.style().polish(self.fix)
        self.lat.set_value(f"{lat:.6f}"); self.lon.set_value(f"{lon:.6f}"); self.alt.set_value(f"{alt:.1f}")
    def reset(self) -> None:
        self.fix.setText("NO FIX")
        for card in (self.lat, self.lon, self.alt): card.set_value("--")
