from __future__ import annotations
from PyQt6.QtWidgets import QComboBox, QDialog, QFormLayout, QDialogButtonBox
from core.serial_manager import SerialManager

class SettingsDialog(QDialog):
    def __init__(self, port: str, baud: int, theme: str, refresh: int, map_type: str, parent=None) -> None:
        super().__init__(parent); self.setWindowTitle("Settings")
        layout = QFormLayout(self)
        self.port = QComboBox(); self.port.addItems(SerialManager.available_ports()); self.port.setCurrentText(port)
        self.baud = QComboBox(); self.baud.addItems([str(b) for b in SerialManager.baudrates()]); self.baud.setCurrentText(str(baud))
        self.theme = QComboBox(); self.theme.addItems(["Cyber HUD", "Glass Dark"]); self.theme.setCurrentText(theme)
        self.refresh = QComboBox(); self.refresh.addItems(["5", "10", "20", "30"]); self.refresh.setCurrentText(str(refresh))
        self.map_type = QComboBox(); self.map_type.addItems(["OpenStreetMap", "Satellite", "Terrain"]); self.map_type.setCurrentText(map_type)
        for label, widget in (("COM Port",self.port),("Baudrate",self.baud),("Theme",self.theme),("Refresh Rate",self.refresh),("Map Type",self.map_type)): layout.addRow(label, widget)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); layout.addWidget(buttons)
