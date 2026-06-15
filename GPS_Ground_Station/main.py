"""GPS Ground Station entry point."""

from __future__ import annotations

import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPushButton, QComboBox, QTextEdit, QVBoxLayout,
    QWidget,
)

from dashboard import Dashboard
from map_widget import MapWidget
from serial_handler import SerialWorker, TelemetryPacket, configure_file_logger
from ui.theme import APP_STYLE
from widgets.status_widgets import GlowIndicator, MetricCard


class GroundStationWindow(QMainWindow):
    """Main professional ground control station window."""

    GPS_TIMEOUT_SECONDS = 5.0

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GPS Ground Station — HC-12 Drone Telemetry")
        self.resize(1580, 920)
        self.serial_worker: SerialWorker | None = None
        self.packet_count = 0
        self.last_packet_time = 0.0
        self.logger = configure_file_logger(Path(__file__).resolve().parent / "logs")
        self._build_ui()
        self._refresh_ports()
        self.timeout_timer = QTimer(self)
        self.timeout_timer.timeout.connect(self._check_gps_timeout)
        self.timeout_timer.start(1000)
        self._log("Application started")

    def _build_ui(self) -> None:
        root = QWidget(objectName="Root")
        self.setCentralWidget(root)
        main = QGridLayout(root)
        main.setContentsMargins(18, 18, 18, 18)
        main.setSpacing(16)

        left = self._panel()
        left_layout = QVBoxLayout(left)
        title = QLabel("GPS TELEMETRY")
        title.setObjectName("Title")
        subtitle = QLabel("Live Arduino + HC-12 aircraft position")
        subtitle.setObjectName("Subtitle")
        left_layout.addWidget(title)
        left_layout.addWidget(subtitle)
        self.lat_card = MetricCard("Latitude")
        self.lon_card = MetricCard("Longitude")
        self.alt_card = MetricCard("Altitude")
        self.speed_card = MetricCard("Speed")
        self.packets_card = MetricCard("Received packets", "0")
        self.last_update_card = MetricCard("Last update")
        for card in (self.lat_card, self.lon_card, self.alt_card, self.speed_card, self.packets_card, self.last_update_card):
            left_layout.addWidget(card)
        left_layout.addStretch()

        center = self._panel()
        center_layout = QVBoxLayout(center)
        header = QHBoxLayout()
        map_title = QLabel("MISSION MAP")
        map_title.setObjectName("Title")
        self.warning = QLabel("GPS SIGNAL LOST")
        self.warning.setObjectName("Warning")
        self.warning.hide()
        header.addWidget(map_title)
        header.addStretch()
        header.addWidget(self.warning)
        center_layout.addLayout(header)
        self.map_widget = MapWidget()
        center_layout.addWidget(self.map_widget, 1)

        right = self._panel()
        right_layout = QVBoxLayout(right)
        right_title = QLabel("LINK CONTROL")
        right_title.setObjectName("Title")
        right_layout.addWidget(right_title)
        status_row = QHBoxLayout()
        self.status_led = GlowIndicator()
        self.status_label = QLabel("Disconnected")
        self.status_label.setObjectName("MetricValue")
        status_row.addWidget(self.status_led)
        status_row.addWidget(self.status_label, 1)
        right_layout.addLayout(status_row)
        self.port_combo = QComboBox()
        self.refresh_button = QPushButton("Refresh COM")
        self.connect_button = QPushButton("Connect")
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setObjectName("Danger")
        self.disconnect_button.setEnabled(False)
        self.export_csv_button = QPushButton("Export CSV")
        self.export_csv_button.setObjectName("Ghost")
        self.export_gpx_button = QPushButton("Export GPX")
        self.export_gpx_button.setObjectName("Ghost")
        for widget in (QLabel("COM port"), self.port_combo, self.refresh_button, self.connect_button, self.disconnect_button):
            right_layout.addWidget(widget)
        self.dashboard = Dashboard()
        right_layout.addWidget(self.dashboard)
        export_row = QHBoxLayout()
        export_row.addWidget(self.export_csv_button)
        export_row.addWidget(self.export_gpx_button)
        right_layout.addLayout(export_row)
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        right_layout.addWidget(QLabel("Message log"))
        right_layout.addWidget(self.log_box, 1)

        main.addWidget(left, 0, 0)
        main.addWidget(center, 0, 1)
        main.addWidget(right, 0, 2)
        main.setColumnStretch(0, 1)
        main.setColumnStretch(1, 4)
        main.setColumnStretch(2, 1)

        self.refresh_button.clicked.connect(self._refresh_ports)
        self.connect_button.clicked.connect(self._connect_serial)
        self.disconnect_button.clicked.connect(self._disconnect_serial)
        self.export_csv_button.clicked.connect(self._export_csv)
        self.export_gpx_button.clicked.connect(self._export_gpx)

    def _panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("GlassPanel")
        return frame

    def _refresh_ports(self) -> None:
        current = self.port_combo.currentText() or SerialWorker.load_last_port()
        self.port_combo.clear()
        ports = SerialWorker.available_ports()
        self.port_combo.addItems(ports)
        if current in ports:
            self.port_combo.setCurrentText(current)
        elif ports:
            self.port_combo.setCurrentIndex(0)
        self._log(f"COM ports refreshed: {', '.join(ports) if ports else 'none found'}")

    def _connect_serial(self) -> None:
        port = self.port_combo.currentText().strip()
        if not port:
            QMessageBox.warning(self, "No COM port", "Connect Arduino and press Refresh COM.")
            return
        self.serial_worker = SerialWorker(port, 9600, self)
        self.serial_worker.packet_received.connect(self._on_packet)
        self.serial_worker.status_changed.connect(self._on_status)
        self.serial_worker.log_message.connect(self._log)
        self.serial_worker.error_occurred.connect(self._error)
        self.serial_worker.start()
        self.connect_button.setEnabled(False)
        self.disconnect_button.setEnabled(True)

    def _disconnect_serial(self) -> None:
        if self.serial_worker:
            self.serial_worker.stop()
            self.serial_worker.wait(1500)
            self.serial_worker = None
        self._on_status(False, "Disconnected")

    def _on_status(self, connected: bool, message: str) -> None:
        self.status_led.set_connected(connected)
        self.status_label.setText("Connected" if connected else "Disconnected")
        self.connect_button.setEnabled(not connected)
        self.disconnect_button.setEnabled(connected)
        self._log(message)

    def _on_packet(self, packet: TelemetryPacket) -> None:
        self.packet_count += 1
        self.last_packet_time = time.time()
        self.warning.hide()
        self.status_led.set_connected(True)
        self.lat_card.set_value(f"{packet.latitude:.7f}°")
        self.lon_card.set_value(f"{packet.longitude:.7f}°")
        self.alt_card.set_value(f"{packet.altitude:.1f} m")
        self.speed_card.set_value(f"{packet.speed:.1f} m/s" if packet.speed is not None else "--")
        self.packets_card.set_value(str(self.packet_count))
        self.last_update_card.set_value(datetime.fromtimestamp(packet.timestamp).strftime("%H:%M:%S"))
        quality = 100 if self.packet_count < 2 else max(15, min(100, int(100 - (time.time() - self.last_packet_time) * 20)))
        self.dashboard.update_values(packet.altitude, packet.heading, quality, self.packet_count)
        self.map_widget.update_position(packet)
        self._log(f"GPS {packet.latitude:.7f}, {packet.longitude:.7f}, alt {packet.altitude:.1f} m")

    def _check_gps_timeout(self) -> None:
        if self.serial_worker and self.last_packet_time and time.time() - self.last_packet_time > self.GPS_TIMEOUT_SECONDS:
            self.warning.show()
            self.status_led.set_connected(False)
            self.dashboard.update_values(self.dashboard.altimeter.get_value(), self.dashboard.compass.get_value(), 0, self.packet_count)
            self._log("WARNING: GPS signal lost")
            self.last_packet_time = 0.0

    def _export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export route CSV", "route.csv", "CSV files (*.csv)")
        if path:
            MapWidget.export_csv(Path(path), self.map_widget.route)
            self._log(f"CSV route exported: {path}")

    def _export_gpx(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export route GPX", "route.gpx", "GPX files (*.gpx)")
        if path:
            MapWidget.export_gpx(Path(path), self.map_widget.route)
            self._log(f"GPX route exported: {path}")

    def _log(self, message: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log_box.append(f"[{stamp}] {message}") if hasattr(self, "log_box") else None
        self.logger.info(message)

    def _error(self, message: str) -> None:
        self._log(f"ERROR: {message}")
        logging.getLogger("GPSGroundStation").error(message)
        QMessageBox.critical(self, "Ground Station error", message)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._disconnect_serial()
        event.accept()


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)
    window = GroundStationWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
