"""Professional Aircraft Command Center entry point."""
from __future__ import annotations

import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QSettings, QTimer
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QTextEdit, QVBoxLayout, QWidget,
)

from map.leaflet_map import LeafletMap
from replay.player import load_json_mission
from storage.mission_recorder import MissionRecorder
from telemetry import GpsFix, SerialWorker, TelemetryPacket, bearing_deg, haversine_m
from ui.theme import APP_STYLE
from widgets.charts import TelemetryChart
from widgets.instruments import Compass, Horizon, Radar, RoundGauge
from widgets.status_widgets import GlowIndicator, MetricCard


class GroundStationWindow(QMainWindow):
    """Main Ground Control Station window driven only by real telemetry."""

    SIGNAL_TIMEOUT_S = 5.0
    GPS_TIMEOUT_S = 8.0

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Aircraft Command Center — Professional GPS/LoRa GCS")
        self.resize(1820, 1040)
        self.settings = QSettings("AircraftCommandCenter", "GroundControlStation")
        self.worker: SerialWorker | None = None
        self.packet_count = 0
        self.last_packet_time = 0.0
        self.last_gps_fix_time = 0.0
        self.home: tuple[float, float] | None = None
        self.last_packet: TelemetryPacket | None = None
        self.replay_packets: list[TelemetryPacket] = []
        self.replay_index = 0
        self.replay_speed = 1.0

        base_dir = Path(__file__).resolve().parent
        (base_dir / "missions").mkdir(exist_ok=True)
        logging.basicConfig(filename=base_dir / "missions" / "errors.log", level=logging.INFO)
        self.recorder = MissionRecorder(base_dir / "missions")
        self._build_ui()
        self._refresh_ports()

        self.health_timer = QTimer(self)
        self.health_timer.timeout.connect(self._health_check)
        self.health_timer.start(1000)
        self.replay_timer = QTimer(self)
        self.replay_timer.timeout.connect(self._replay_tick)

        if self.settings.value("autoconnect", False, type=bool):
            self._connect()

    def _panel(self) -> QFrame:
        return QFrame(objectName="GlassPanel")

    def _build_ui(self) -> None:
        root = QWidget(objectName="Root")
        self.setCentralWidget(root)
        grid = QGridLayout(root)
        grid.setContentsMargins(14, 14, 14, 14)
        grid.setSpacing(12)

        left = self._panel()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("FLIGHT DATA", objectName="Title"))
        self.gps_banner = QLabel("NO FIX", objectName="GpsNoFix")
        left_layout.addWidget(self.gps_banner)
        self.cards = {name: MetricCard(name) for name in [
            "Altitude", "Speed", "Heading", "Coordinates", "Satellites",
            "Last Packet", "Distance Home", "Bearing Home", "Packet Rate", "Mode",
        ]}
        for card in self.cards.values():
            left_layout.addWidget(card)
        left_layout.addStretch()

        center = self._panel()
        center_layout = QVBoxLayout(center)
        map_top = QHBoxLayout()
        map_top.addWidget(QLabel("MISSION MAP", objectName="Title"))
        self.follow = QCheckBox("Follow Aircraft")
        self.follow.setChecked(True)
        self.home_button = QPushButton("Set Home Here")
        map_top.addStretch()
        map_top.addWidget(self.follow)
        map_top.addWidget(self.home_button)
        center_layout.addLayout(map_top)
        self.map = LeafletMap()
        center_layout.addWidget(self.map, 1)
        self.alert = QLabel("", objectName="AlertBanner")
        center_layout.addWidget(self.alert)

        right = self._panel()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel("LINK / POWER / REPLAY", objectName="Title"))
        status_row = QHBoxLayout()
        self.led = GlowIndicator()
        self.status = QLabel("Disconnected", objectName="MetricValue")
        status_row.addWidget(self.led)
        status_row.addWidget(self.status, 1)
        right_layout.addLayout(status_row)
        self.port = QComboBox()
        self.baud = QComboBox()
        self.baud.addItems([str(b) for b in SerialWorker.baudrates()])
        self.baud.setCurrentText(str(self.settings.value("baudrate", 9600)))
        self.autoconnect = QCheckBox("Autoconnect")
        self.autoconnect.setChecked(self.settings.value("autoconnect", False, type=bool))
        self.scan_button = QPushButton("Scan COM")
        self.connect_button = QPushButton("Connect")
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setObjectName("Danger")
        for widget in [QLabel("Port"), self.port, QLabel("Baudrate"), self.baud, self.autoconnect, self.scan_button, self.connect_button, self.disconnect_button]:
            right_layout.addWidget(widget)

        self.link_quality = QProgressBar()
        self.battery = QProgressBar()
        self.rssi = MetricCard("RSSI")
        self.snr = MetricCard("SNR")
        self.voltage = MetricCard("Voltage")
        self.current = MetricCard("Current")
        self.mah = MetricCard("mAh")
        self.temperature = MetricCard("Temperature")
        self.pressure = MetricCard("Pressure")
        for widget in [QLabel("Link Quality"), self.link_quality, self.rssi, self.snr, QLabel("Battery"), self.battery, self.voltage, self.current, self.mah, self.temperature, self.pressure]:
            right_layout.addWidget(widget)

        replay_row = QHBoxLayout()
        self.load_replay = QPushButton("Load")
        self.play_replay = QPushButton("Play")
        self.pause_replay = QPushButton("Pause")
        self.stop_replay = QPushButton("Stop")
        self.speed2 = QPushButton("x2")
        self.speed4 = QPushButton("x4")
        for button in [self.load_replay, self.play_replay, self.pause_replay, self.stop_replay, self.speed2, self.speed4]:
            replay_row.addWidget(button)
        right_layout.addLayout(replay_row)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        right_layout.addWidget(self.log, 1)

        instruments = self._panel()
        instruments_layout = QGridLayout(instruments)
        self.airspeed = RoundGauge("AIRSPEED", "m/s", 120)
        self.altimeter = RoundGauge("ALTIMETER", "m", 5000)
        self.vsi = RoundGauge("VSI", "m/s", 35)
        self.compass = Compass()
        self.horizon = Horizon()
        self.radar = Radar()
        self.alt_chart = TelemetryChart("Altitude", "m")
        self.speed_chart = TelemetryChart("Speed", "m/s", "#7fb7ff")
        self.rssi_chart = TelemetryChart("RSSI", "dBm", "#ffffff")
        self.voltage_chart = TelemetryChart("Voltage", "V")
        self.link_chart = TelemetryChart("Link Quality", "%", "#3cf0b1")
        widgets = [self.airspeed, self.altimeter, self.compass, self.vsi, self.horizon, self.radar, self.alt_chart, self.speed_chart, self.rssi_chart, self.voltage_chart, self.link_chart]
        for index, widget in enumerate(widgets):
            instruments_layout.addWidget(widget, index // 6, index % 6)

        grid.addWidget(left, 0, 0)
        grid.addWidget(center, 0, 1)
        grid.addWidget(right, 0, 2)
        grid.addWidget(instruments, 1, 0, 1, 3)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 5)
        grid.setColumnStretch(2, 1)

        self.scan_button.clicked.connect(self._refresh_ports)
        self.connect_button.clicked.connect(self._connect)
        self.disconnect_button.clicked.connect(self._disconnect)
        self.follow.toggled.connect(self.map.set_follow)
        self.home_button.clicked.connect(self._set_home_from_current)
        self.autoconnect.toggled.connect(lambda value: self.settings.setValue("autoconnect", value))
        self.load_replay.clicked.connect(self._load_replay)
        self.play_replay.clicked.connect(self._play_replay)
        self.pause_replay.clicked.connect(self.replay_timer.stop)
        self.stop_replay.clicked.connect(self._stop_replay)
        self.speed2.clicked.connect(lambda: self._set_replay_speed(2.0))
        self.speed4.clicked.connect(lambda: self._set_replay_speed(4.0))

    def _refresh_ports(self) -> None:
        current = str(self.settings.value("last_port", ""))
        ports = SerialWorker.available_ports()
        self.port.clear()
        self.port.addItems(ports)
        if current in ports:
            self.port.setCurrentText(current)
        elif ports:
            self.port.setCurrentIndex(0)
        self._log("Ports: " + (", ".join(ports) if ports else "none"))

    def _connect(self) -> None:
        if not self.port.currentText():
            QMessageBox.warning(self, "Serial", "No serial port found. Connect receiver and press Scan COM.")
            return
        self.worker = SerialWorker(self.port.currentText(), int(self.baud.currentText()), reconnect=True, parent=self)
        self.worker.packet_received.connect(self._on_packet)
        self.worker.status_changed.connect(self._on_status)
        self.worker.log_message.connect(self._log)
        self.worker.error_occurred.connect(lambda message: logging.error(message))
        self.worker.start()

    def _disconnect(self) -> None:
        if self.worker:
            self.worker.stop()
            self.worker.wait(1500)
            self.worker = None

    def _on_status(self, connected: bool, message: str) -> None:
        self.led.set_connected(connected)
        self.status.setText("Connected" if connected else "Disconnected")
        self._log(message)

    def _on_packet(self, packet: TelemetryPacket) -> None:
        self.packet_count += 1
        self.last_packet = packet
        self.last_packet_time = time.time()
        if packet.has_gps_fix():
            self.last_gps_fix_time = self.last_packet_time
            if self.home is None:
                self.home = (packet.latitude, packet.longitude)
                self._log("Home point automatically set on first GPS fix")
        self.recorder.append(packet)
        self._render_packet(packet, record_to_map=True)

    def _render_packet(self, packet: TelemetryPacket, record_to_map: bool) -> None:
        distance = bearing = None
        if self.home:
            distance = haversine_m(packet.latitude, packet.longitude, self.home[0], self.home[1])
            bearing = bearing_deg(packet.latitude, packet.longitude, self.home[0], self.home[1])
        self.map.update_packet(packet, self.home, bearing) if record_to_map else None
        self._update_flight_data(packet, distance, bearing)
        self._update_instruments(packet, distance, bearing)
        self._update_link_and_power(packet)
        self._update_alerts(packet, distance)

    def _update_flight_data(self, packet: TelemetryPacket, distance: float | None, bearing: float | None) -> None:
        values = {
            "Altitude": f"{packet.altitude:.1f} m",
            "Speed": f"{packet.speed:.1f} m/s",
            "Heading": f"{packet.heading:.0f}°",
            "Coordinates": f"{packet.latitude:.6f}, {packet.longitude:.6f}",
            "Satellites": str(packet.satellites),
            "Last Packet": datetime.fromtimestamp(packet.timestamp).strftime("%H:%M:%S"),
            "Distance Home": "--" if distance is None else f"{distance:.0f} m",
            "Bearing Home": "--" if bearing is None else f"{bearing:.0f}°",
            "Packet Rate": f"{packet.packet_rate_hz:.1f} Hz",
            "Mode": packet.flight_mode or "--",
        }
        for key, value in values.items():
            self.cards[key].set_value(value)
        self._set_gps_banner(packet.gps_fix or GpsFix.NO_FIX)

    def _update_instruments(self, packet: TelemetryPacket, distance: float | None, bearing: float | None) -> None:
        self.airspeed.set_value(packet.speed)
        self.altimeter.set_value(packet.altitude)
        self.vsi.set_value(abs(packet.vertical_speed))
        self.compass.set_heading(packet.heading)
        self.horizon.set_attitude(packet.pitch, packet.roll)
        self.radar.set_values(distance, bearing, packet.heading)
        self.alt_chart.add_value(packet.altitude)
        self.speed_chart.add_value(packet.speed)
        self.rssi_chart.add_value(packet.rssi)
        self.voltage_chart.add_value(packet.voltage)
        quality = packet.link_quality()
        self.link_chart.add_value(None if quality is None else float(quality))

    def _update_link_and_power(self, packet: TelemetryPacket) -> None:
        quality = packet.link_quality()
        self.link_quality.setValue(0 if quality is None else quality)
        self.rssi.set_value("--" if packet.rssi is None else f"{packet.rssi:.0f} dBm")
        self.snr.set_value("--" if packet.snr is None else f"{packet.snr:.1f} dB")
        pct = packet.battery_percent()
        self.battery.setValue(0 if pct is None else pct)
        self.voltage.set_value("--" if packet.voltage is None else f"{packet.voltage:.2f} V")
        self.current.set_value("--" if packet.current is None else f"{packet.current:.2f} A")
        self.mah.set_value("--" if packet.mah is None else f"{packet.mah:.0f} mAh")
        self.temperature.set_value("--" if packet.temperature is None else f"{packet.temperature:.1f} °C")
        self.pressure.set_value("--" if packet.pressure is None else f"{packet.pressure:.0f} Pa")

    def _update_alerts(self, packet: TelemetryPacket, distance: float | None) -> None:
        alerts: list[str] = []
        quality = packet.link_quality()
        battery = packet.battery_percent()
        if quality is not None and quality < 25:
            alerts.append("SIGNAL LOST")
        if packet.gps_fix is GpsFix.NO_FIX:
            alerts.append("GPS LOST")
        if battery is not None and battery < 15:
            alerts.append("CRITICAL BATTERY")
        elif battery is not None and battery < 30:
            alerts.append("LOW BATTERY")
        if distance is not None and distance > 1000 and (battery is not None and battery < 35 or quality is not None and quality < 35):
            alerts.append("RETURN TO HOME RECOMMENDED")
        self.alert.setText("  •  ".join(alerts))

    def _set_gps_banner(self, fix: GpsFix) -> None:
        names = {
            GpsFix.NO_FIX: "GpsNoFix",
            GpsFix.FIX_2D: "Gps2D",
            GpsFix.FIX_3D: "Gps3D",
            GpsFix.DGPS: "GpsDgps",
            GpsFix.RTK: "GpsRtk",
        }
        self.gps_banner.setObjectName(names[fix])
        self.gps_banner.setText(fix.value)
        self.gps_banner.style().unpolish(self.gps_banner)
        self.gps_banner.style().polish(self.gps_banner)

    def _set_home_from_current(self) -> None:
        if self.last_packet and self.last_packet.has_gps_fix():
            self.home = (self.last_packet.latitude, self.last_packet.longitude)
            self._log("Home point manually updated")
        else:
            QMessageBox.information(self, "Home", "Home can be set only after a real GPS fix packet.")

    def _health_check(self) -> None:
        now = time.time()
        alerts = []
        if self.last_packet_time and now - self.last_packet_time > self.SIGNAL_TIMEOUT_S:
            alerts.append("SIGNAL LOST")
            self.led.set_connected(False)
            self.status.setText("Telemetry timeout")
        if self.last_gps_fix_time and now - self.last_gps_fix_time > self.GPS_TIMEOUT_S:
            alerts.append("GPS LOST")
        if alerts:
            self.alert.setText("  •  ".join(alerts))

    def _load_replay(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load mission JSON", str(Path(__file__).resolve().parent / "missions"), "JSON (*.json)")
        if path:
            self.replay_packets = load_json_mission(Path(path))
            self.replay_index = 0
            self._log(f"Replay loaded: {len(self.replay_packets)} packets")

    def _play_replay(self) -> None:
        if not self.replay_packets:
            self._load_replay()
        if self.replay_packets:
            self.replay_timer.start(max(20, int(1000 / self.replay_speed)))

    def _replay_tick(self) -> None:
        if self.replay_index >= len(self.replay_packets):
            self._stop_replay()
            return
        packet = self.replay_packets[self.replay_index]
        self.last_packet = packet
        if self.home is None and packet.has_gps_fix():
            self.home = (packet.latitude, packet.longitude)
        self._render_packet(packet, record_to_map=True)
        self.replay_index += 1

    def _set_replay_speed(self, speed: float) -> None:
        self.replay_speed = speed
        if self.replay_timer.isActive():
            self.replay_timer.start(max(20, int(1000 / self.replay_speed)))

    def _stop_replay(self) -> None:
        self.replay_timer.stop()
        self.replay_index = 0

    def _log(self, message: str) -> None:
        if hasattr(self, "log"):
            self.log.append(f"[{datetime.now():%H:%M:%S}] {message}")
        logging.info(message)


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)
    window = GroundStationWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
