from __future__ import annotations
from datetime import datetime
from random import randint
from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QTimer
from PyQt6.QtWidgets import QFileDialog, QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QStatusBar, QVBoxLayout, QWidget, QGraphicsOpacityEffect
from core.logger import TelemetryLogger
from core.replay import ReplayPlayer, SessionRecorder
from core.serial_manager import SerialManager
from core.statistics import FlightStatistics
from core.telemetry_parser import TelemetryPoint
from .dashboard import FlightAnalyticsDashboard
from .graphs_widget import GraphsWidget
from .instruments import ArtificialHorizon, CompassWidget, AircraftAltimeter, VerticalSpeedIndicator, RadarWidget, DigitalUTCClock, SignalQualityMonitor, RSSIVisualization, CameraPanel, add_neon
from .map_widget import MapWidget
from .settings_dialog import SettingsDialog
from .telemetry_panel import TelemetryPanel

STYLE = """
QWidget{background:#0D1117;color:#CFFAFF;font-family:'Segoe UI',Arial;} QFrame#GlassPanel,QFrame#InstrumentPanel{background:rgba(21,26,36,214);border:1px solid rgba(0,229,255,105);border-radius:20px;} QFrame#StatTile{background:rgba(30,41,59,205);border:1px solid rgba(0,255,136,80);border-radius:16px;} QFrame#CameraPanel{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #111827,stop:1 #020617);border:1px dashed #00E5FF;border-radius:18px;} QLabel#PanelTitle{font-size:18px;font-weight:900;color:#00E5FF;letter-spacing:2px;} QLabel#UtcClock{font-size:22px;font-weight:900;color:#00FF88;border:1px solid #00E5FF;border-radius:14px;padding:8px;background:#151A24;} QLabel#StatValue{font-size:22px;font-weight:900;color:#00FF88;} QFrame#TelemetryCard{background:rgba(30,41,59,190);border-radius:18px;border:1px solid rgba(0,255,136,70);} QLabel#CardTitle{color:#8BE9FF;font-size:12px;} QLabel#CardValue{font-size:31px;font-weight:900;color:#00FF88;} QPushButton{background:#151A24;border:1px solid #00E5FF;border-radius:14px;padding:10px;color:#CFFAFF;font-weight:800;} QPushButton:hover{background:#1E293B;color:#00FF88;box-shadow:0 0 20px #00E5FF;} QLabel#GpsFix{color:#00FF88;font-weight:900;} QLabel#NoFix{color:#ff4d6d;font-weight:900;} QProgressBar{border:1px solid #00E5FF;border-radius:8px;background:#0D1117;text-align:center;} QProgressBar::chunk{background:#00FF88;border-radius:7px;}
"""

class MainWindow(QMainWindow):
    """V2 Professional military UAV Ground Control Station."""
    def __init__(self) -> None:
        super().__init__(); self.setWindowTitle("VAYLLEM UAV COMMAND CENTER V2 PROFESSIONAL"); self.resize(1600,900); self.setMinimumSize(1400,800); self.setStyleSheet(STYLE)
        self.port="COM5"; self.baud=9600; self.theme="Cyber HUD"; self.refresh=10; self.map_type="OpenStreetMap"; self.worker=None; self.packets=0; self.last_packet="--"; self.logger=TelemetryLogger(); self.stats=FlightStatistics(expected_hz=1.0); self.recorder=SessionRecorder(); self.replay=ReplayPlayer(self)
        self._build(); self.replay.point.connect(self.on_point); self.replay.finished.connect(lambda: self.link.setText("🟢 Replay finished")); self._status_timer=QTimer(self); self._status_timer.timeout.connect(self._refresh_status); self._status_timer.start(500)
    def _build(self) -> None:
        root=QWidget(); self.setCentralWidget(root); grid=QGridLayout(root); grid.setContentsMargins(14,14,14,14); grid.setSpacing(12)
        toolbar=QFrame(objectName="GlassPanel"); bar=QHBoxLayout(toolbar); self.buttons={name:QPushButton(name) for name in ["Connect","Disconnect","Clear Track","Center Map","Export Log","Settings","Record","Replay"]}
        title=QLabel("VAYLLEM UAV COMMAND CENTER · V2 PROFESSIONAL"); title.setObjectName("PanelTitle"); self.clock=DigitalUTCClock(); self.follow=QCheckBox("AUTO CENTER"); self.follow.setChecked(True); bar.addWidget(title); bar.addStretch(); bar.addWidget(self.clock); bar.addWidget(self.follow); [bar.addWidget(b) for b in self.buttons.values()]
        self.telemetry=TelemetryPanel(); self.map=MapWidget(); self.graphs=GraphsWidget(); self.analytics=FlightAnalyticsDashboard(); self.camera=CameraPanel()
        self.right=QFrame(objectName="GlassPanel"); r=QVBoxLayout(self.right); self.link=QLabel("🔴 Disconnected"); self.info=QLabel(); self.signal=SignalQualityMonitor(); self.rssi=RSSIVisualization(); r.addWidget(QLabel("LINK STATUS", objectName="PanelTitle")); r.addWidget(self.link); r.addWidget(self.info); r.addWidget(self.signal); r.addWidget(self.rssi); r.addWidget(self.camera,1)
        self.instruments=QFrame(objectName="GlassPanel"); inst=QGridLayout(self.instruments); self.horizon=ArtificialHorizon(); self.compass=CompassWidget(); self.altimeter=AircraftAltimeter(); self.vsi=VerticalSpeedIndicator(); self.radar=RadarWidget()
        for widget in (self.horizon,self.compass,self.altimeter,self.vsi,self.radar,self.clock): add_neon(widget)
        inst.addWidget(QLabel("TACTICAL INSTRUMENTS", objectName="PanelTitle"),0,0,1,5); [inst.addWidget(w,1,i) for i,w in enumerate((self.horizon,self.compass,self.altimeter,self.vsi,self.radar))]
        grid.addWidget(toolbar,0,0,1,3); grid.addWidget(self.telemetry,1,0); grid.addWidget(self.map,1,1); grid.addWidget(self.right,1,2); grid.addWidget(self.instruments,2,0,1,3); grid.addWidget(self.graphs,3,0,1,2); grid.addWidget(self.analytics,3,2); grid.setColumnStretch(1,1); grid.setRowStretch(1,1)
        self.setStatusBar(QStatusBar()); self._refresh_status(); self._wire_actions(); self._fade_in(root)
    def _wire_actions(self) -> None:
        self.buttons["Connect"].clicked.connect(self.connect_serial); self.buttons["Disconnect"].clicked.connect(self.disconnect_serial); self.buttons["Clear Track"].clicked.connect(self.clear_track); self.buttons["Center Map"].clicked.connect(self.map.render); self.buttons["Export Log"].clicked.connect(self.export_log); self.buttons["Settings"].clicked.connect(self.open_settings); self.buttons["Record"].clicked.connect(self.toggle_recording); self.buttons["Replay"].clicked.connect(self.load_replay); self.follow.toggled.connect(self.map.set_auto_center)
    def _fade_in(self, widget: QWidget) -> None:
        effect=QGraphicsOpacityEffect(widget); widget.setGraphicsEffect(effect); anim=QPropertyAnimation(effect,b"opacity",self); anim.setDuration(700); anim.setStartValue(0.0); anim.setEndValue(1.0); anim.setEasingCurve(QEasingCurve.Type.OutCubic); anim.start(); self._intro_anim=anim
    def connect_serial(self) -> None:
        self.disconnect_serial(); self.worker=SerialManager(self.port,self.baud,self); self.worker.telemetry_received.connect(self.on_point); self.worker.error.connect(lambda e: QMessageBox.warning(self,"Serial error",e)); self.worker.connected_changed.connect(lambda ok: self.link.setText("🟢 Connected" if ok else "🔴 Disconnected")); self.worker.start()
    def disconnect_serial(self) -> None:
        if self.worker: self.worker.stop(); self.worker=None
    def on_point(self, p: TelemetryPoint) -> None:
        self.packets+=1; self.last_packet=datetime.now().strftime("%H:%M:%S"); snap=self.stats.add_point(p); heading=self.stats.heading_deg
        self.telemetry.update_values(p.latitude,p.longitude,p.altitude); self.map.add_point(p.latitude,p.longitude,p.altitude,heading); self.graphs.add_point(p.latitude,p.longitude,p.altitude); self.logger.add(p); self.recorder.record(p,{"heading":heading,"packets":self.packets}); self.analytics.update_snapshot(snap)
        self.horizon.set_attitude(snap.vertical_speed_mps*1.5, heading/8); self.compass.set_heading(heading); self.altimeter.set_altitude(p.altitude); self.vsi.set_vspeed(snap.vertical_speed_mps); self.radar.set_distance(snap.distance_km); self.signal.set_quality(snap.signal_quality,snap.packet_loss_percent); self.rssi.set_rssi(randint(-108,-62)); self._refresh_status()
    def clear_track(self) -> None:
        self.map.clear_track(); self.graphs.clear(); self.logger.clear(); self.stats.reset(); self.packets=0; self.telemetry.reset(); self.analytics.update_snapshot(self.stats.snapshot()); self._refresh_status()
    def export_log(self) -> None:
        path,_=QFileDialog.getSaveFileName(self,"Export telemetry","telemetry.csv","CSV (*.csv);;JSON (*.json)")
        if not path: return
        self.logger.export_json(path) if path.endswith(".json") else self.logger.export_csv(path)
    def open_settings(self) -> None:
        dlg=SettingsDialog(self.port,self.baud,self.theme,self.refresh,self.map_type,self)
        if dlg.exec(): self.port=dlg.port.currentText(); self.baud=int(dlg.baud.currentText()); self.theme=dlg.theme.currentText(); self.refresh=int(dlg.refresh.currentText()); self.map_type=dlg.map_type.currentText(); self.map.set_map_type(self.map_type); self._refresh_status()
    def toggle_recording(self) -> None:
        if self.recorder.active:
            path=self.recorder.stop(); self.buttons["Record"].setText("Record"); QMessageBox.information(self,"Session Recorder",f"Saved: {path}")
        else:
            path=self.recorder.start(); self.buttons["Record"].setText("Stop Rec"); self.link.setText(f"🟢 Recording {path.name}")
    def load_replay(self) -> None:
        path,_=QFileDialog.getOpenFileName(self,"Open replay session","sessions","JSONL (*.jsonl)")
        if not path: return
        count=self.replay.load(path); self.link.setText(f"🟢 Replaying {count} packets"); self.replay.play()
    def _refresh_status(self) -> None:
        snap=self.stats.snapshot(); self.info.setText(f"COM Port: {self.port}\nBaudrate: {self.baud}\nPackets Received: {self.packets}\nSignal Status: {'ACTIVE' if self.packets else 'WAITING'}\nPacket Loss: {snap.packet_loss_percent:.1f}%\nLast Packet Time: {self.last_packet}\nRoute: {snap.distance_km:.3f} km")
        self.statusBar().showMessage(f"GPS {'ACTIVE' if self.packets else 'WAITING'} | LINK {'ACTIVE' if self.worker else 'IDLE'} | {self.port} | {self.baud} | PACKETS {self.packets} | LOSS {snap.packet_loss_percent:.1f}% | DIST {snap.distance_km:.3f} km")
