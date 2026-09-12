export type PlaceType='country'|'city'|'region'|'airport'|'landmark'|'coordinate';
export interface GeoPlace {id:string;name:string;names?:string[];type:PlaceType;country?:string;countryCode?:string;region?:string;latitude:number;longitude:number;population?:number;importance?:number}
export interface Route { points:GeoPlace[]; distanceKm:number; initialBearing:number; finalBearing:number; kind:'geodesic'|'road'; durationMinutes:number }
export type SelectionMode='start'|'destination'|null;
export interface Settings {autoRotate:boolean;atmosphere:boolean;stars:boolean;routeAnimation:boolean;units:'metric'|'imperial';showHud:boolean;showFps:boolean;sound:boolean}
