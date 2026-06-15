"""QWebEngine Leaflet map with SVG aircraft, interpolation and tile cache."""
from __future__ import annotations

import json
from pathlib import Path
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWebEngineWidgets import QWebEngineView

from telemetry import TelemetryPacket


class LeafletMap(QWebEngineView):
    """Live aircraft map optimized for small JavaScript updates per packet."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(900, 590)
        self.route: list[list[float]] = []
        self.base_dir = Path(__file__).resolve().parents[1]
        self.path = self.base_dir / "resources" / "leaflet_live.html"
        self.cache_dir = self.base_dir / "resources" / "tile_cache"
        self.path.parent.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
        profile = self.page().profile()
        profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        profile.setCachePath(str(self.cache_dir))
        profile.setPersistentStoragePath(str(self.cache_dir))
        self._write_html()
        self.setUrl(QUrl.fromLocalFile(str(self.path)))

    def _write_html(self) -> None:
        """Create the Leaflet document used by QWebEngine."""
        html = r'''<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
html,body,#map{height:100%;margin:0;background:#06111e}.leaflet-control{background:rgba(10,22,35,.90)!important;color:#fff!important;box-shadow:0 0 18px rgba(60,240,177,.18)}
.aircraft-wrap{transition:transform .18s linear;filter:drop-shadow(0 0 10px #3cf0b1)}.aircraft-svg{width:100%;height:100%;display:block}.rth-arrow{color:#3cf0b1;font-size:32px;text-shadow:0 0 12px #3cf0b1}.home-dot{background:#fff;border:3px solid #3cf0b1;border-radius:50%;width:18px;height:18px;box-shadow:0 0 15px #3cf0b1}
</style></head><body><div id="map"></div><script>
const map=L.map('map',{preferCanvas:true,zoomControl:true}).setView([55.751244,37.618423],15);
const osm=L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:20,attribution:'OSM'}).addTo(map);
const sat=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:20,attribution:'Esri'});
L.control.layers({'OpenStreetMap':osm,'Esri Satellite':sat}).addTo(map);
let marker=null, route=L.polyline([],{color:'#3cf0b1',weight:3,opacity:.92}).addTo(map), home=null, homeLine=L.polyline([],{color:'#ffffff',dashArray:'8 8',weight:2}).addTo(map), rth=null, follow=true, current=null, target=null, animStart=0, animMs=850, lastHeading=0;
function aircraftSvg(){return `<svg class="aircraft-svg" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg"><path d="M32 3 L39 28 L61 39 L61 47 L37 40 L37 56 L46 61 L46 64 L32 60 L18 64 L18 61 L27 56 L27 40 L3 47 L3 39 L25 28 Z" fill="#f8ffff" stroke="#3cf0b1" stroke-width="2"/></svg>`}
function sizeForZoom(){return Math.max(30,Math.min(70,24+map.getZoom()*2.1))}
function icon(h){const s=sizeForZoom();return L.divIcon({className:'',html:`<div class="aircraft-wrap" style="width:${s}px;height:${s}px;transform:rotate(${h}deg)">${aircraftSvg()}</div>`,iconSize:[s,s],iconAnchor:[s/2,s/2]});}
function homeIcon(){return L.divIcon({className:'',html:'<div class="home-dot"></div>',iconSize:[24,24],iconAnchor:[12,12]})}
function arrowIcon(b){return L.divIcon({className:'',html:`<div class="rth-arrow" style="transform:rotate(${b}deg)">➤</div>`,iconSize:[36,36],iconAnchor:[18,18]})}
function setFollow(v){follow=v}
function setHome(lat,lon){if(!home){home=L.marker([lat,lon],{icon:homeIcon()}).addTo(map).bindPopup('HOME')}else home.setLatLng([lat,lon])}
function lerp(a,b,t){return a+(b-a)*t}
function tick(){if(current&&target){let t=Math.min(1,(performance.now()-animStart)/animMs);let lat=lerp(current[0],target[0],t), lon=lerp(current[1],target[1],t); marker.setLatLng([lat,lon]); if(follow) map.panTo([lat,lon],{animate:false}); if(t>=1) current=target;} requestAnimationFrame(tick)} requestAnimationFrame(tick);
function updateAircraft(p, pts, homePoint, bearingHome){lastHeading=p.heading; const ll=[p.latitude,p.longitude]; if(!marker){current=ll; marker=L.marker(ll,{icon:icon(p.heading)}).addTo(map)} target=ll; animStart=performance.now(); marker.setIcon(icon(p.heading)); marker.bindPopup(`Aircraft<br>${p.latitude.toFixed(6)}, ${p.longitude.toFixed(6)}<br>${p.altitude.toFixed(1)} m<br>${p.gps_fix}`); route.setLatLngs(pts); if(homePoint){setHome(homePoint[0],homePoint[1]); homeLine.setLatLngs([ll,homePoint]); if(!rth) rth=L.marker(ll,{icon:arrowIcon(bearingHome||0)}).addTo(map); rth.setLatLng(ll); rth.setIcon(arrowIcon(bearingHome||0));}}
map.on('zoomend',()=>{if(marker) marker.setIcon(icon(lastHeading))});
</script></body></html>'''
        self.path.write_text(html, encoding="utf-8")

    def update_packet(self, packet: TelemetryPacket, home: tuple[float, float] | None, bearing_home: float | None) -> None:
        """Send only the latest packet and bounded route to JavaScript."""
        self.route.append([packet.latitude, packet.longitude])
        if len(self.route) > 2000:
            self.route = self.route[-2000:]
        js = f"updateAircraft({json.dumps(packet.to_dict())},{json.dumps(self.route)},{json.dumps(home)},{json.dumps(bearing_home)})"
        self.page().runJavaScript(js)

    def set_follow(self, enabled: bool) -> None:
        self.page().runJavaScript(f"setFollow({str(enabled).lower()})")
