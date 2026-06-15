"""Application stylesheet for an aviation dark glass cockpit look."""

APP_STYLE = """
QMainWindow,#Root{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #05101d,stop:.55 #0a1624,stop:1 #111820);color:#eef7ff;font-family:'Segoe UI';}
QFrame#GlassPanel,QWidget#GlassPanel{background:rgba(17,31,47,205);border:1px solid rgba(160,190,220,58);border-radius:18px;}
QLabel#Title{font-size:20px;font-weight:850;letter-spacing:2px;color:#f8fbff;} QLabel#Subtitle,QLabel#MetricName{color:#9fb6cc;font-size:11px;font-weight:750;letter-spacing:1px;} QLabel#MetricValue{font-size:21px;font-weight:850;color:#ffffff;}
QLabel#AlertBanner{background:rgba(150,20,35,210);border:1px solid #ff7d8d;border-radius:14px;color:#ffffff;font-size:22px;font-weight:900;letter-spacing:2px;padding:12px;}
QLabel#GpsNoFix,QLabel#Gps2D,QLabel#Gps3D,QLabel#GpsDgps,QLabel#GpsRtk{border-radius:12px;padding:10px;font-size:18px;font-weight:900;letter-spacing:2px;color:#07111f;} QLabel#GpsNoFix{background:#ff6b7a;} QLabel#Gps2D{background:#ffd166;} QLabel#Gps3D{background:#3cf0b1;} QLabel#GpsDgps{background:#72ddf7;} QLabel#GpsRtk{background:#ffffff;}
QPushButton{background:#102c45;border:1px solid #315f7c;border-radius:10px;padding:9px;color:#eef7ff;font-weight:800;} QPushButton:hover{border-color:#3cf0b1;color:#3cf0b1;} QPushButton#Danger{border-color:#8b3442;color:#ff9cac;}
QComboBox,QCheckBox{background:#0a1725;color:#eef7ff;border:1px solid #315f7c;border-radius:8px;padding:7px;} QProgressBar{border:1px solid #315f7c;border-radius:7px;background:#071522;text-align:center;color:white;font-weight:800;} QProgressBar::chunk{background:#3cf0b1;border-radius:7px;} QTextEdit{background:#071522;color:#dff;border:1px solid #26435e;border-radius:12px;}
"""
