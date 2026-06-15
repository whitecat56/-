"""Custom telemetry instruments: altimeter, compass and link quality."""

from __future__ import annotations

import math
from PyQt6.QtCore import Qt, QRectF, pyqtProperty
from PyQt6.QtGui import QColor, QConicalGradient, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout


class Gauge(QWidget):
    """Circular glass gauge for altitude/heading style values."""

    def __init__(self, title: str, unit: str, maximum: float, parent=None) -> None:
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.maximum = maximum
        self._value = 0.0
        self.setMinimumSize(155, 155)

    def get_value(self) -> float:
        return self._value

    def set_value(self, value: float) -> None:
        self._value = max(0.0, min(float(value), self.maximum))
        self.update()

    value = pyqtProperty(float, fget=get_value, fset=set_value)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt override
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(16, 16, self.width() - 32, self.height() - 32)
        painter.setPen(QPen(QColor(55, 82, 120), 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(rect, 225 * 16, -270 * 16)
        gradient = QConicalGradient(rect.center(), -45)
        gradient.setColorAt(0.0, QColor("#28ffc6"))
        gradient.setColorAt(0.55, QColor("#24a8ff"))
        gradient.setColorAt(1.0, QColor("#ff4d7d"))
        painter.setPen(QPen(gradient, 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        span = int(-270 * 16 * (self._value / self.maximum if self.maximum else 0))
        painter.drawArc(rect, 225 * 16, span)
        painter.setPen(QColor("#EAF2FF"))
        painter.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self._value:.0f}\n{self.unit}")
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        painter.setPen(QColor("#8EA7C6"))
        painter.drawText(0, 8, self.width(), 24, Qt.AlignmentFlag.AlignCenter, self.title)


class Compass(Gauge):
    """Compass gauge that points to heading when available."""

    def __init__(self, parent=None) -> None:
        super().__init__("HEADING", "°", 360.0, parent)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = self.rect().center()
        angle = math.radians(self._value - 90)
        end_x = center.x() + math.cos(angle) * 48
        end_y = center.y() + math.sin(angle) * 48
        painter.setPen(QPen(QColor("#ff456e"), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(center.x(), center.y(), int(end_x), int(end_y))


class Dashboard(QWidget):
    """Instrument cluster with altitude, compass, link quality and packet count."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        self.altimeter = Gauge("ALTITUDE", "m", 1000.0)
        self.compass = Compass()
        row.addWidget(self.altimeter)
        row.addWidget(self.compass)
        layout.addLayout(row)
        self.link_label = QLabel("LINK QUALITY")
        self.link_label.setObjectName("MetricName")
        self.link_bar = QProgressBar()
        self.link_bar.setRange(0, 100)
        self.packet_label = QLabel("Packets: 0")
        self.packet_label.setObjectName("MetricValue")
        layout.addWidget(self.link_label)
        layout.addWidget(self.link_bar)
        layout.addWidget(self.packet_label)

    def update_values(self, altitude: float, heading: float | None, quality: int, packets: int) -> None:
        """Refresh all dashboard instruments."""
        self.altimeter.set_value(altitude)
        if heading is not None:
            self.compass.set_value(heading % 360)
        self.link_bar.setValue(max(0, min(100, quality)))
        self.packet_label.setText(f"Packets: {packets}")
