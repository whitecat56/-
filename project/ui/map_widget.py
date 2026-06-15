from __future__ import annotations
import math, tempfile
from pathlib import Path
import folium
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl

class MapWidget(QWebEngineView):
    """Folium/Leaflet tactical map with runtime layers, track, arrow and animated marker."""
    def __init__(self) -> None:
        super().__init__(); self.track: list[tuple[float,float]]=[]; self.map_type="OpenStreetMap"; self.auto_center=True; self.heading=0.0; self.altitude=0.0; self._last=(38.85667,65.81726); self.render()
    def set_map_type(self, name: str) -> None: self.map_type=name; self.render()
    def set_auto_center(self, enabled: bool) -> None: self.auto_center=enabled; self.render()
    def add_point(self, lat: float, lon: float, alt: float, heading: float = 0.0) -> None:
        self._last=(lat,lon); self.altitude=alt; self.heading=heading; self.track.append((lat,lon)); self.render()
    def clear_track(self) -> None: self.track.clear(); self.render()
    def route_km(self) -> float:
        return sum(self._haversine(a,b) for a,b in zip(self.track,self.track[1:]))
    def render(self) -> None:
        base = {"OpenStreetMap":"OpenStreetMap", "Terrain":"CartoDB positron", "Satellite":"OpenStreetMap"}.get(self.map_type,"OpenStreetMap")
        m=folium.Map(location=self._last, zoom_start=16 if self.auto_center else 13, tiles=base, control_scale=True)
        folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(m); folium.TileLayer("CartoDB positron", name="Terrain").add_to(m)
        folium.TileLayer(tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri World Imagery", name="Satellite").add_to(m)
        if self.track: folium.PolyLine(self.track,color="#00E5FF",weight=4,opacity=.85,tooltip="Flight track").add_to(m)
        icon_html=f"""<div class='drone-marker'><div class='pulse'></div><div class='arrow' style='transform:rotate({self.heading}deg)'>▲</div></div>"""
        folium.Marker(self._last, tooltip="UAV", icon=folium.DivIcon(html=icon_html, icon_size=(48,48), icon_anchor=(24,24))).add_to(m)
        folium.LayerControl(collapsed=False).add_to(m)
        css="""<style>.drone-marker{position:relative;width:48px;height:48px;color:#00ff88;text-align:center;font-size:30px;text-shadow:0 0 12px #00e5ff}.pulse{position:absolute;left:8px;top:8px;width:32px;height:32px;border:2px solid #00e5ff;border-radius:50%;animation:pulse 1.4s infinite}.arrow{position:absolute;left:8px;top:4px;width:32px;height:32px;transition:transform .45s ease-out}@keyframes pulse{0%{transform:scale(.45);opacity:1}100%{transform:scale(1.8);opacity:0}}</style>"""
        hud='<div style="position:fixed;top:20px;left:20px;z-index:9999;color:#00e5ff;background:rgba(13,17,23,.68);padding:14px;border:1px solid #00e5ff;border-radius:16px;box-shadow:0 0 22px #00e5ff;font:700 14px monospace">HUD OVERLAY<br>LAT %.6f<br>LON %.6f<br>ALT %.1f m<br>HDG %.0f°<br>DIST %.3f km</div>' % (self._last[0], self._last[1], self.altitude, self.heading, self.route_km())
        html=m.get_root().render()+css+hud
        path=Path(tempfile.gettempdir())/"vayllem_uav_map_v2.html"; path.write_text(html,encoding="utf-8"); self.setUrl(QUrl.fromLocalFile(str(path)))
    @staticmethod
    def _haversine(a: tuple[float,float], b: tuple[float,float]) -> float:
        r=6371.0088; p1=math.radians(a[0]); p2=math.radians(b[0]); dp=math.radians(b[0]-a[0]); dl=math.radians(b[1]-a[1]); h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2; return 2*r*math.atan2(math.sqrt(h),math.sqrt(1-h))
