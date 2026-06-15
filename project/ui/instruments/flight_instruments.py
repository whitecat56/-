"""QPainter based military UAV flight instruments."""
from __future__ import annotations

from datetime import datetime, timezone
import math
from PyQt6.QtCore import QEasingCurve, QPointF, QPropertyAnimation, QTimer, Qt, pyqtProperty
from PyQt6.QtGui import QColor, QConicalGradient, QFont, QLinearGradient, QPainter, QPen, QBrush
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget, QProgressBar, QGraphicsDropShadowEffect

NEON = QColor("#00E5FF"); GREEN = QColor("#00FF88"); BG = QColor("#0D1117")

def add_neon(widget: QWidget, color: QColor = NEON, blur: int = 28) -> None:
    glow = QGraphicsDropShadowEffect(widget); glow.setBlurRadius(blur); glow.setColor(color); glow.setOffset(0, 0); widget.setGraphicsEffect(glow)

class AnimatedValueWidget(QWidget):
    def __init__(self) -> None:
        super().__init__(); self._value = 0.0; self.anim = QPropertyAnimation(self, b"value", self); self.anim.setDuration(420); self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    def get_value(self) -> float: return self._value
    def set_value(self, value: float) -> None: self._value = value; self.update()
    value = pyqtProperty(float, get_value, set_value)
    def animate_to(self, value: float) -> None:
        self.anim.stop(); self.anim.setStartValue(self._value); self.anim.setEndValue(float(value)); self.anim.start()

class ArtificialHorizon(AnimatedValueWidget):
    def __init__(self) -> None:
        super().__init__(); self.pitch = 0.0; self.roll = 0.0; self.setMinimumSize(210, 160)
    def set_attitude(self, pitch: float, roll: float) -> None:
        self.pitch = max(-45, min(45, pitch)); self.animate_to(roll)
    def paintEvent(self, _):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); r=self.rect().adjusted(8,8,-8,-8); c=r.center(); radius=min(r.width(),r.height())/2
        p.save(); p.setClipRect(r); p.translate(c); p.rotate(self._value); p.translate(0, self.pitch*2)
        p.fillRect(-500,-500,1000,500,QColor("#123B68")); p.fillRect(-500,0,1000,500,QColor("#4A2D18")); p.setPen(QPen(QColor("#FFFFFF"),2)); p.drawLine(-500,0,500,0); p.restore()
        p.setPen(QPen(NEON,2)); p.drawEllipse(QPointF(c), radius, radius); p.drawLine(c.x()-45,c.y(),c.x()-10,c.y()); p.drawLine(c.x()+10,c.y(),c.x()+45,c.y()); p.drawText(r, Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignHCenter, "ARTIFICIAL HORIZON")

class CompassWidget(AnimatedValueWidget):
    def __init__(self) -> None: super().__init__(); self.setMinimumSize(170,170)
    def set_heading(self, deg: float) -> None: self.animate_to(deg % 360)
    def paintEvent(self, _):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); r=self.rect().adjusted(10,10,-10,-10); c=r.center(); rad=min(r.width(),r.height())/2
        p.setPen(QPen(NEON,2)); p.drawEllipse(QPointF(c),rad,rad); p.save(); p.translate(c); p.rotate(-self._value)
        for a in range(0,360,15):
            p.rotate(15); p.setPen(QPen(GREEN if a%90==0 else NEON,2 if a%90==0 else 1)); p.drawLine(0,-rad,0,-rad+12)
        p.restore(); p.setPen(QPen(GREEN,3)); p.drawLine(c.x(),c.y()-rad+8,c.x()-8,c.y()-rad+28); p.drawLine(c.x(),c.y()-rad+8,c.x()+8,c.y()-rad+28); p.drawText(r, Qt.AlignmentFlag.AlignCenter, f"{self._value:03.0f}°")

class AircraftAltimeter(AnimatedValueWidget):
    def __init__(self) -> None: super().__init__(); self.setMinimumSize(170,170)
    def set_altitude(self, meters: float) -> None: self.animate_to(meters)
    def paintEvent(self, _):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); r=self.rect().adjusted(10,10,-10,-10); c=r.center(); rad=min(r.width(),r.height())/2
        p.setPen(QPen(NEON,2)); p.drawEllipse(QPointF(c),rad,rad); angle=(self._value%1000)/1000*270-135; end=QPointF(c.x()+math.cos(math.radians(angle))*rad*.72,c.y()+math.sin(math.radians(angle))*rad*.72)
        p.setPen(QPen(GREEN,4)); p.drawLine(QPointF(c),end); p.setPen(QPen(QColor("#CFFAFF"),1)); p.drawText(r,Qt.AlignmentFlag.AlignCenter,f"ALT\n{self._value:.0f} m")

class VerticalSpeedIndicator(AnimatedValueWidget):
    def __init__(self) -> None: super().__init__(); self.setMinimumSize(150,170)
    def set_vspeed(self, mps: float) -> None: self.animate_to(max(-20,min(20,mps)))
    def paintEvent(self, _):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); r=self.rect().adjusted(12,12,-12,-12); p.setPen(QPen(NEON,2)); p.drawRoundedRect(r,18,18); mid=r.center().y(); p.drawLine(r.left()+30,mid,r.right()-30,mid); y=mid-(self._value/20)*(r.height()/2-25); p.setBrush(GREEN); p.drawEllipse(QPointF(r.center().x(),y),9,9); p.drawText(r,Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignHCenter,f"VSI {self._value:+.1f} m/s")

class RadarWidget(QWidget):
    def __init__(self) -> None: super().__init__(); self.angle=0; self.distance_km=0.0; self.timer=QTimer(self); self.timer.timeout.connect(self._spin); self.timer.start(50); self.setMinimumSize(170,170)
    def set_distance(self, km: float) -> None: self.distance_km=km; self.update()
    def _spin(self): self.angle=(self.angle+4)%360; self.update()
    def paintEvent(self,_):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); r=self.rect().adjusted(10,10,-10,-10); c=r.center(); rad=min(r.width(),r.height())/2; p.setPen(QPen(NEON,1))
        for f in (.33,.66,1): p.drawEllipse(QPointF(c),rad*f,rad*f)
        p.drawLine(c.x()-rad,c.y(),c.x()+rad,c.y()); p.drawLine(c.x(),c.y()-rad,c.x(),c.y()+rad); p.setPen(QPen(GREEN,3)); p.drawLine(QPointF(c),QPointF(c.x()+math.cos(math.radians(self.angle))*rad,c.y()+math.sin(math.radians(self.angle))*rad)); p.drawText(r,Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignHCenter,f"RADAR {self.distance_km:.2f} km")

class DigitalUTCClock(QLabel):
    def __init__(self) -> None:
        super().__init__(); self.setAlignment(Qt.AlignmentFlag.AlignCenter); self.setObjectName("UtcClock"); self.timer=QTimer(self); self.timer.timeout.connect(self._tick); self.timer.start(1000); self._tick()
    def _tick(self) -> None: self.setText(datetime.now(timezone.utc).strftime("UTC %H:%M:%S"))

class SignalQualityMonitor(QFrame):
    def __init__(self) -> None:
        super().__init__(); self.setObjectName("InstrumentPanel"); layout=QVBoxLayout(self); self.label=QLabel("SIGNAL QUALITY"); self.bar=QProgressBar(); self.bar.setRange(0,100); layout.addWidget(self.label); layout.addWidget(self.bar)
    def set_quality(self, quality: int, loss: float) -> None:
        self.bar.setValue(max(0,min(100,quality))); self.label.setText(f"SIGNAL {quality}% | LOSS {loss:.1f}%")

class RSSIVisualization(QFrame):
    def __init__(self) -> None:
        super().__init__(); self.setObjectName("InstrumentPanel"); layout=QVBoxLayout(self); self.label=QLabel("RSSI -- dBm"); self.bar=QProgressBar(); self.bar.setRange(-120,-50); layout.addWidget(self.label); layout.addWidget(self.bar)
    def set_rssi(self, rssi: int | None) -> None:
        value = -95 if rssi is None else rssi; self.bar.setValue(value); self.label.setText(f"RSSI {value} dBm")

class CameraPanel(QFrame):
    def __init__(self) -> None:
        super().__init__(); self.setObjectName("CameraPanel"); layout=QVBoxLayout(self); label=QLabel("CAMERA FEED\nPLACEHOLDER\nEO/IR PAYLOAD OFFLINE"); label.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.addWidget(label)
