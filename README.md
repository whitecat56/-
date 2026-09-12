# GLOBAL NAV

**GLOBAL NAV — LOCAL 3D NAVIGATION SYSTEM** is an offline-first WebGL navigation workstation. It renders Earth locally with Three.js, supports local multilingual place search, browser GPS, click-to-select coordinates, and a mathematically correct great-circle route fallback.

## Run on Windows / local development

```bash
npm install
npm run dev
npm run build
npm test
npm run preview
```

No runtime API keys, CDNs, map tiles, geocoders, route services, web fonts, or remote textures are used. After Vite has served the app once, the included service worker caches the application shell for offline use. Development servers are normally not PWA-offline-equivalent; use `npm run build` and `npm run preview` to validate the production bundle.

## Workflow

1. Use **LOCATE ME** to request browser geolocation, or **SELECT ON GLOBE** and click Earth to set START.
2. Search a city, country, airport, region, or decimal coordinates. `Tashkent`, `Ташкент`, `Toshkent`, `Tashknet`, and `41.3111, 69.2797` are supported locally.
3. Search selection sets DESTINATION and performs a smooth camera flight.
4. Choose **BUILD ROUTE**. The UI explicitly labels the bundled route as **GEODESIC**; it is never represented as driving directions.

GPS values are never sent from this application. Browser permission denial and unavailable GPS are presented in the UI.

## Architecture

- `src/globe/GlobeScene.tsx`: Three.js scene, procedural day/night-like terrain shading, atmospheric shell, star field, raycasting, markers, globe route and controls.
- `src/geocoding/LocalGeocoder.ts`: local normalisation, aliases, coordinate parser, ranking, prefix/exact/fuzzy lookup.
- `src/routing/RoutingEngine.ts`: offline geodesic engine (Haversine, bearings, spherical interpolation).
- `src/stores/navigationStore.ts`: typed Zustand navigation state and local recent search history.
- `public/data/manifest.json`: local dataset inventory.

## Local data and road routing

The seed local dataset contains Uzbekistan priority locations (including Tashkent, Samarkand, and Bukhara), major world cities, countries, a region, and airport examples. It is intentionally a compact starter dataset, not a claim to contain all world cities. Expand it by adding `GeoPlace` records to `src/data/places.ts` or by replacing the geocoder data source with a prebuilt offline index.

`public/data/roads/` is reserved for a locally installed OSM graph. It is **not installed** in this source distribution; the UI reports this accurately. To add genuine driving routing, implement a `RoadRoutingProvider` that reads a locally generated OSM graph (for example a regional GraphHopper/OSRM export) and only return `kind: 'road'` after it has produced a road-edge path. The current fallback remains fully functional without it and never makes a network request.

## Data manifest

`public/data/{cities,countries,airports,maps,roads,textures}` is the local-data layout. The manifest gives installed/absent status. Procedural shaders eliminate mandatory image texture downloads and avoid large binary assets.

## Troubleshooting

- **WebGL unavailable**: enable browser hardware acceleration or update GPU drivers.
- **GPS denied**: enable location permission for the localhost / installed PWA origin; use click selection instead.
- **No local result**: use coordinates or click the globe. The app never falls back to an online geocoder.
- **Road network not installed**: expected for the starter distribution; great-circle navigation remains available.

## Production deployment

Serve the generated `dist/` folder from any static local server. Keep the build and `public/data` together. The service worker caches same-origin assets only.
