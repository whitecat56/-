from __future__ import annotations
import sys
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor, QPixmap, QPainter, QFont
from PyQt6.QtWidgets import QApplication, QSplashScreen
from ui.main_window import MainWindow

def build_splash() -> QSplashScreen:
    pix = QPixmap(720, 320); pix.fill(QColor("#0D1117")); painter = QPainter(pix); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor("#00E5FF")); painter.setFont(QFont("Segoe UI", 26, QFont.Weight.Black)); painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "VAYLLEM UAV\nCOMMAND CENTER V2")
    painter.setPen(QColor("#00FF88")); painter.setFont(QFont("Consolas", 12)); painter.drawText(28, 292, "INITIALIZING MILITARY UAV GROUND CONTROL STATION..."); painter.end()
    return QSplashScreen(pix)

def main() -> int:
    app = QApplication(sys.argv)
    splash = build_splash(); splash.show(); app.processEvents()
    window = MainWindow()
    QTimer.singleShot(1200, lambda: (splash.finish(window), window.show()))
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
