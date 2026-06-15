"""Small reusable status widgets."""

from __future__ import annotations

from PyQt6.QtCore import QPropertyAnimation, Qt, pyqtProperty
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class GlowIndicator(QWidget):
    """Animated circular status LED."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._color = QColor("#ff3856")
        self._pulse = 0.35
        self.setFixedSize(28, 28)
        self.animation = QPropertyAnimation(self, b"pulse", self)
        self.animation.setStartValue(0.25)
        self.animation.setEndValue(1.0)
        self.animation.setDuration(900)
        self.animation.setLoopCount(-1)
        self.animation.start()

    def set_connected(self, connected: bool) -> None:
        self._color = QColor("#29ffbf" if connected else "#ff3856")
        self.update()

    def get_pulse(self) -> float:
        return self._pulse

    def set_pulse(self, pulse: float) -> None:
        self._pulse = pulse
        self.update()

    pulse = pyqtProperty(float, fget=get_pulse, fset=set_pulse)

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        glow = QColor(self._color)
        glow.setAlpha(int(80 * self._pulse))
        painter.setBrush(glow)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())
        painter.setBrush(self._color)
        painter.drawEllipse(7, 7, 14, 14)


class MetricCard(QWidget):
    """Glass card with telemetry name and value."""

    def __init__(self, name: str, value: str = "--", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("GlassPanel")
        layout = QVBoxLayout(self)
        self.name_label = QLabel(name)
        self.name_label.setObjectName("MetricName")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("MetricValue")
        layout.addWidget(self.name_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)
