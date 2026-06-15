"""PyQtGraph telemetry charts with bounded buffers, zoom/pan and PNG export."""
from __future__ import annotations

from collections import deque
from pathlib import Path
from time import time
from typing import Optional

import pyqtgraph as pg
from pyqtgraph.exporters import ImageExporter
from PyQt6.QtWidgets import QFileDialog, QMenu, QVBoxLayout, QWidget


class TelemetryChart(QWidget):
    """A high-performance strip chart backed by PyQtGraph.

    PyQtGraph provides native zoom, pan, mouse hover readouts and GPU-friendly
    drawing. The deque cap prevents memory growth during long missions.
    """

    def __init__(self, title: str, unit: str, color: str = "#3cf0b1", max_points: int = 600, parent=None) -> None:
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.max_points = max_points
        self.times: deque[float] = deque(maxlen=max_points)
        self.values: deque[float] = deque(maxlen=max_points)
        self.start_time = time()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.plot = pg.PlotWidget(background=(7, 18, 30, 180))
        self.plot.setTitle(title, color="#eef7ff", size="10pt")
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.setLabel("bottom", "Time", units="s")
        self.plot.setLabel("left", title, units=unit)
        self.plot.setMouseEnabled(x=True, y=True)
        self.plot.addLegend(offset=(-8, 8))
        self.curve = self.plot.plot([], [], pen=pg.mkPen(color, width=2), name=title)
        self.hover = pg.TextItem("", color="#ffffff", anchor=(0, 1))
        self.plot.addItem(self.hover)
        self.plot.scene().sigMouseMoved.connect(self._on_hover)
        layout.addWidget(self.plot)
        self.setMinimumHeight(130)
        from PyQt6.QtCore import Qt
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)

    def add_value(self, value: Optional[float]) -> None:
        """Append a real telemetry value; missing fields are not fabricated."""
        if value is None:
            return
        self.times.append(time() - self.start_time)
        self.values.append(float(value))
        self.curve.setData(list(self.times), list(self.values))

    def export_png(self, path: Path) -> None:
        """Export the current chart view to a PNG image."""
        exporter = ImageExporter(self.plot.plotItem)
        exporter.export(str(path))

    def _menu(self, pos) -> None:
        menu = QMenu(self)
        export_action = menu.addAction("Export PNG")
        if menu.exec(self.mapToGlobal(pos)) == export_action:
            path, _ = QFileDialog.getSaveFileName(self, "Export chart PNG", f"{self.title.lower()}.png", "PNG (*.png)")
            if path:
                self.export_png(Path(path))

    def _on_hover(self, pos) -> None:
        if not self.times:
            return
        point = self.plot.plotItem.vb.mapSceneToView(pos)
        xs = list(self.times)
        idx = min(range(len(xs)), key=lambda i: abs(xs[i] - point.x()))
        value = list(self.values)[idx]
        self.hover.setText(f"{xs[idx]:.1f}s  {value:.2f} {self.unit}")
        self.hover.setPos(xs[idx], value)
