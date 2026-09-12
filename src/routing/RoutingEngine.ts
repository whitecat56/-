import type {GeoPlace,Route} from '../types'; import {bearing,haversine,interpolateGreatCircle} from '../utils/geo';
/** Offline routing boundary. Road providers can be registered once a local OSM graph is installed. */
export class RoutingEngine { build(start:GeoPlace,destination:GeoPlace):Route {const distanceKm=haversine(start,destination); if(distanceKm<0.01) throw new Error('Start and destination must be different points.'); return {kind:'geodesic',points:interpolateGreatCircle(start,destination),distanceKm,initialBearing:bearing(start,destination),finalBearing:bearing(destination,start),durationMinutes:Math.round(distanceKm/780*60)} } }
export const routingEngine=new RoutingEngine();
