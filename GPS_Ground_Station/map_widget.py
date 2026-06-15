"""Leaflet/Folium based live map widget."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
import folium

from serial_handler import TelemetryPacket


class MapWidget(QWebEngineView):
    """Interactive aircraft map with satellite tiles, marker and route polyline."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.route: list[TelemetryPacket] = []
        self.setMinimumSize(760, 520)
        self._html_path = Path(__file__).resolve().parent / "assets" / "live_map.html"
        self._create_initial_map()

    def _create_initial_map(self) -> None:
        """Build the self-contained Leaflet document used by the web view."""
        start = [55.751244, 37.618423]
        fmap = folium.Map(location=start, zoom_start=15, control_scale=True, tiles=None)
        folium.TileLayer("OpenStreetMap", name="Street", control=True).add_to(fmap)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri World Imagery", name="Satellite", overlay=False, control=True,
        ).add_to(fmap)
        folium.LayerControl().add_to(fmap)
        html = fmap.get_root().render()
        extra = """
<style>
html, body { background:#07111f; }
.leaflet-control-layers, .leaflet-control-zoom a { background: rgba(12,24,42,.88)!important; color:#fff!important; border-color: rgba(91,176,255,.35)!important; }
.drone-marker { width:34px; height:34px; border-radius:50%; background: radial-gradient(circle,#fff 0,#25d9ff 38%,#1266ff 65%,rgba(18,102,255,.20) 100%); box-shadow:0 0 28px #26dcff; border:2px solid #e8fbff; }
</style>
<script>
let droneMarker = null;
let routeLine = null;
let lastLatLng = null;
function ensureObjects(lat, lon) {
  const icon = L.divIcon({className:'', html:'<div class="drone-marker"></div>', iconSize:[34,34], iconAnchor:[17,17]});
  if (!droneMarker) droneMarker = L.marker([lat, lon], {icon: icon}).addTo(map).bindPopup('Drone');
  if (!routeLine) routeLine = L.polyline([], {color:'#28e7ff', weight:4, opacity:.9}).addTo(map);
}
function updateDrone(lat, lon, alt, points) {
  ensureObjects(lat, lon);
  const target = L.latLng(lat, lon);
  droneMarker.setLatLng(target);
  droneMarker.setPopupContent(`Drone<br>Lat: ${lat.toFixed(6)}<br>Lon: ${lon.toFixed(6)}<br>Alt: ${alt.toFixed(1)} m`);
  routeLine.setLatLngs(points);
  map.flyTo(target, Math.max(map.getZoom(), 16), {animate:true, duration:.75});
  lastLatLng = target;
}
</script>
"""
        html = html.replace("</head>", extra + "</head>")
        self._html_path.write_text(html, encoding="utf-8")
        self.setUrl(QUrl.fromLocalFile(str(self._html_path)))

    def update_position(self, packet: TelemetryPacket) -> None:
        """Append a point and update marker/polyline in JavaScript."""
        self.route.append(packet)
        points = [[p.latitude, p.longitude] for p in self.route]
        js = f"updateDrone({packet.latitude:.8f}, {packet.longitude:.8f}, {packet.altitude:.2f}, {json.dumps(points)});"
        self.page().runJavaScript(js)

    def clear_route(self) -> None:
        """Clear recorded route and reset the map document."""
        self.route.clear()
        self._create_initial_map()

    @staticmethod
    def export_csv(path: Path, packets: Iterable[TelemetryPacket]) -> None:
        """Export route as CSV for Excel, GIS tools or post-flight analysis."""
        rows = ["timestamp,latitude,longitude,altitude,speed,heading,battery_voltage,rssi"]
        for p in packets:
            rows.append(f"{p.timestamp:.3f},{p.latitude:.8f},{p.longitude:.8f},{p.altitude:.2f},{p.speed or ''},{p.heading or ''},{p.battery_voltage or ''},{p.rssi or ''}")
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    @staticmethod
    def export_gpx(path: Path, packets: Iterable[TelemetryPacket]) -> None:
        """Export route as GPX track."""
        trkpts = []
        for p in packets:
            trkpts.append(f'      <trkpt lat="{p.latitude:.8f}" lon="{p.longitude:.8f}"><ele>{p.altitude:.2f}</ele></trkpt>')
        xml = "\n".join([
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<gpx version="1.1" creator="GPS Ground Station" xmlns="http://www.topografix.com/GPX/1/1">',
            '  <trk><name>Drone route</name><trkseg>', *trkpts, '  </trkseg></trk>', '</gpx>'
        ])
        path.write_text(xml + "\n", encoding="utf-8")
