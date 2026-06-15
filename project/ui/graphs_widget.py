from __future__ import annotations
from collections import deque
import pyqtgraph as pg
from PyQt6.QtWidgets import QFrame, QVBoxLayout

class GraphsWidget(QFrame):
    def __init__(self, max_points: int = 600) -> None:
        super().__init__(); self.setObjectName("GlassPanel")
        self.x = deque(maxlen=max_points); self.series = {"Latitude": deque(maxlen=max_points), "Longitude": deque(maxlen=max_points), "Altitude": deque(maxlen=max_points)}
        self.plots = {}; self.curves = {}; layout = QVBoxLayout(self)
        pg.setConfigOptions(antialias=True, background=None, foreground="#B8F7FF")
        colors = {"Latitude":"#00E5FF", "Longitude":"#00FF88", "Altitude":"#F8E16C"}
        for name in self.series:
            plot = pg.PlotWidget(title=name); plot.showGrid(x=True, y=True, alpha=0.25); plot.setMinimumHeight(92)
            curve = plot.plot(pen=pg.mkPen(colors[name], width=2))
            self.plots[name]=plot; self.curves[name]=curve; layout.addWidget(plot)
        self._tick = 0
    def add_point(self, lat: float, lon: float, alt: float) -> None:
        self._tick += 1; self.x.append(self._tick)
        for name, val in (("Latitude", lat),("Longitude", lon),("Altitude", alt)):
            self.series[name].append(val); self.curves[name].setData(list(self.x), list(self.series[name]))
    def clear(self) -> None:
        self.x.clear(); self._tick = 0
        for name in self.series: self.series[name].clear(); self.curves[name].clear()
