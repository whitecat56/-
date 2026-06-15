"""Application theme and UI constants."""

APP_STYLE = """
* { font-family: 'Segoe UI', 'Inter', Arial, sans-serif; color: #EAF2FF; }
QMainWindow, QWidget#Root { background: #07111F; }
QFrame#GlassPanel {
    background: rgba(17, 31, 52, 210);
    border: 1px solid rgba(120, 190, 255, 70);
    border-radius: 22px;
}
QLabel#Title { font-size: 22px; font-weight: 800; letter-spacing: 1px; color: #FFFFFF; }
QLabel#Subtitle { color: #8EA7C6; font-size: 12px; }
QLabel#MetricName { color: #8EA7C6; font-size: 12px; text-transform: uppercase; }
QLabel#MetricValue { color: #FFFFFF; font-size: 25px; font-weight: 800; }
QLabel#Warning {
    background: rgba(255, 56, 86, 210);
    color: white;
    border-radius: 14px;
    padding: 12px 18px;
    font-size: 16px;
    font-weight: 800;
}
QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #1C7DFF, stop:1 #18D6E8);
    border: 0;
    border-radius: 14px;
    padding: 11px 16px;
    color: white;
    font-weight: 800;
}
QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #44A0FF, stop:1 #46F2FF); }
QPushButton:pressed { background: #1164CC; }
QPushButton:disabled { background: rgba(90, 105, 125, 140); color: #B2C2D6; }
QPushButton#Danger { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #FF315C, stop:1 #FF8A3D); }
QPushButton#Ghost { background: rgba(255,255,255,25); border: 1px solid rgba(255,255,255,45); }
QComboBox {
    background: rgba(255,255,255,22);
    border: 1px solid rgba(130, 190, 255, 70);
    border-radius: 12px;
    padding: 9px 12px;
    color: white;
}
QComboBox QAbstractItemView { background: #101C30; selection-background-color: #1C7DFF; color: white; }
QTextEdit {
    background: rgba(1, 8, 18, 170);
    border: 1px solid rgba(120, 190, 255, 50);
    border-radius: 14px;
    padding: 10px;
    color: #CDE8FF;
}
QProgressBar {
    background: rgba(255,255,255,20);
    border: 1px solid rgba(255,255,255,40);
    border-radius: 8px;
    text-align: center;
    height: 14px;
}
QProgressBar::chunk { border-radius: 8px; background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #28FFBF, stop:1 #28A8FF); }
"""
