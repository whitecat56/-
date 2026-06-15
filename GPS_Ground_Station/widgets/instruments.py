"""Real PyQt6 aviation instruments bound to telemetry channels."""
from __future__ import annotations

import math
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QWidget


class RoundGauge(QWidget):
    def __init__(self, title: str, unit: str, maximum: float, parent=None) -> None:
        super().__init__(parent); self.title=title; self.unit=unit; self.maximum=maximum; self.value=0.0; self.setMinimumSize(150,150)
    def set_value(self, value: float) -> None:
        self.value = max(0.0, min(float(value), self.maximum)); self.update()
    def paintEvent(self, event) -> None:
        del event; p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); c=self.rect().center(); r=min(self.width(),self.height())/2-16
        p.setPen(QPen(QColor('#29425f'),10,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap)); p.drawArc(int(c.x()-r),int(c.y()-r),int(2*r),int(2*r),225*16,-270*16)
        p.setPen(QPen(QColor('#3cf0b1'),10,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap)); p.drawArc(int(c.x()-r),int(c.y()-r),int(2*r),int(2*r),225*16,int(-270*16*self.value/self.maximum))
        p.setPen(QColor('#f5fbff')); p.setFont(QFont('Segoe UI',18,QFont.Weight.Bold)); p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,f'{self.value:.0f}\n{self.unit}')
        p.setFont(QFont('Segoe UI',9,QFont.Weight.Bold)); p.setPen(QColor('#9eb6d0')); p.drawText(0,8,self.width(),20,Qt.AlignmentFlag.AlignCenter,self.title)

class Compass(QWidget):
    def __init__(self,parent=None): super().__init__(parent); self.heading=0.0; self.setMinimumSize(150,150)
    def set_heading(self,h:float)->None: self.heading=h%360; self.update()
    def paintEvent(self,event)->None:
        del event; p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); c=self.rect().center(); r=min(self.width(),self.height())/2-18
        p.setPen(QPen(QColor('#41617f'),2)); p.drawEllipse(c,int(r),int(r))
        for deg,label in [(0,'N'),(90,'E'),(180,'S'),(270,'W')]:
            a=math.radians(deg-90); p.setPen(QColor('#dcecff')); p.setFont(QFont('Segoe UI',11,QFont.Weight.Bold)); p.drawText(int(c.x()+math.cos(a)*(r-18)-8),int(c.y()+math.sin(a)*(r-18)+6),label)
        a=math.radians(self.heading-90); end=QPointF(c.x()+math.cos(a)*(r-28),c.y()+math.sin(a)*(r-28)); p.setPen(QPen(QColor('#3cf0b1'),4,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap)); p.drawLine(QPointF(c),end)
        p.setPen(QColor('#fff')); p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,f'{self.heading:.0f}°')

class Horizon(QWidget):
    def __init__(self,parent=None): super().__init__(parent); self.pitch=0.0; self.roll=0.0; self.setMinimumSize(210,160)
    def set_attitude(self,pitch:float|None,roll:float|None)->None: self.pitch=0.0 if pitch is None else pitch; self.roll=0.0 if roll is None else roll; self.update()
    def paintEvent(self,event)->None:
        del event; p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); p.translate(self.width()/2,self.height()/2); p.rotate(-self.roll); y=self.pitch*2
        p.fillRect(-self.width(),-self.height()*2+y,self.width()*2,self.height()*2,QColor('#143a5c')); p.fillRect(-self.width(),y,self.width()*2,self.height()*2,QColor('#4c3827'))
        p.setPen(QPen(QColor('#f5fbff'),3)); p.drawLine(-80,int(y),80,int(y)); p.resetTransform(); p.setPen(QPen(QColor('#3cf0b1'),3)); mid=self.rect().center(); p.drawLine(mid.x()-35,mid.y(),mid.x()-8,mid.y()); p.drawLine(mid.x()+8,mid.y(),mid.x()+35,mid.y()); p.drawEllipse(mid,3,3)
        p.setPen(QColor('#fff')); p.setFont(QFont('Segoe UI',9,QFont.Weight.Bold)); p.drawText(8,18,f'P {self.pitch:.1f}°  R {self.roll:.1f}°')

class Radar(QWidget):
    def __init__(self,parent=None): super().__init__(parent); self.distance=None; self.bearing=None; self.heading=0.0; self.setMinimumSize(180,180)
    def set_values(self,distance,bearing,heading): self.distance=distance; self.bearing=bearing; self.heading=heading; self.update()
    def paintEvent(self,event)->None:
        del event; p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); c=self.rect().center(); r=min(self.width(),self.height())/2-12; p.setPen(QPen(QColor('#29425f'),1));
        for f in (.33,.66,1): p.drawEllipse(c,int(r*f),int(r*f))
        p.setPen(QPen(QColor('#3cf0b1'),2)); p.drawText(8,18,'RADAR HOME')
        if self.bearing is not None:
            rel=math.radians((self.bearing-self.heading)-90); end=QPointF(c.x()+math.cos(rel)*(r-15),c.y()+math.sin(rel)*(r-15)); p.drawLine(QPointF(c),end); p.setBrush(QColor('#3cf0b1')); p.drawEllipse(end,5,5)
        p.setPen(QColor('#fff')); p.drawText(8,self.height()-12,'-- m' if self.distance is None else f'{self.distance:.0f} m')
