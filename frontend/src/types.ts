export interface GpsCoords {
  lat: number;
  lon: number;
}

export interface Camera {
  camera_id: string;
  region: string;
  city: string;
  district: string;
  street: string;
  camera_name: string;
  camera_number: string;
  location_name: string;
  gps_coords: GpsCoords;
  camera_type: string;
  resolution: string;
  fps: number;
  status: "ONLINE" | "OFFLINE" | "MAINTENANCE";
}

export interface CameraOption {
  camera_id: string;
  camera_name: string;
  camera_number: string;
  label: string;
  full_address: string;
  status: string;
}

export interface AlertLocation {
  region?: string;
  city?: string;
  district?: string;
  street?: string;
  camera_name?: string;
  camera_number?: string;
  full_address?: string;
  location_name?: string;
}

export interface DetectedVehicle {
  vehicle_id: string;
  vehicle_type: string;
  bbox: number[];
  confidence: number;
  speed_ms: number;
  approaching_crosswalk: boolean;
}

export interface TrafficLightReading {
  signal: string;
  source: string;
  updated_at?: string;
  is_stale: boolean;
}

export interface VehicleProximityReading {
  proximity_sec?: number | null;
  source: string;
  updated_at?: string;
  is_stale: boolean;
}

export interface CameraSensorState {
  traffic_light_red: boolean;
  traffic_light?: TrafficLightReading | null;
  vehicle_proximity_sec?: number | null;
  vehicle_proximity?: VehicleProximityReading | null;
  vision_vehicle_proximity_sec?: number | null;
  radar_vehicle_proximity_sec?: number | null;
  detected_vehicles: number;
}

export interface DetectedPerson {
  person_id: string;
  category: string;
  gender: string;
  age_range: string;
  clothing_color: string;
  direction: string;
  speed_ms: number;
  group_status: string;
  in_crosswalk: boolean;
  bbox: number[];
  confidence: number;
}

export interface Statistics {
  total_count: number;
  by_category: Record<string, number>;
  by_gender: Record<string, number>;
  by_direction: Record<string, number>;
  by_side: Record<string, number>;
  avg_crossing_time: number;
  density_map: number[][];
  hourly_flow: number[];
  peak_hour: number | null;
  violation_count: number;
}

export interface Alert {
  alert_id: string;
  timestamp: string;
  camera_id: string;
  location?: AlertLocation;
  alert_type: string;
  severity: "RED" | "YELLOW" | "BLUE";
  description: string;
  recommended_action: string;
  category?: string;
}

export interface FrameResponse {
  request_id: string;
  timestamp: string;
  camera_id: string;
  frame_number: number;
  frame_width: number;
  frame_height: number;
  snapshot_url?: string;
  detected_persons: DetectedPerson[];
  detected_vehicles?: DetectedVehicle[];
  sensor_state?: CameraSensorState | null;
  statistics: Statistics;
  active_alerts: Alert[];
  zone_counts: {
    left_side: number;
    crosswalk: number;
    right_side: number;
  };
}

export interface InferenceStatus {
  mode: string;
  ready: boolean;
  device?: string;
  device_name?: string;
  model_name?: string;
  tracker?: string;
  gpu_available?: boolean;
  fallback_active?: boolean;
  message?: string;
}

export function cameraFullAddress(camera: Camera | undefined): string {
  if (!camera) return "Kamera tanlanmagan";
  return `${camera.region} · ${camera.city} · ${camera.district} · ${camera.street} · ${camera.camera_name} №${camera.camera_number}`;
}

export function alertLocationText(location: AlertLocation | undefined): string {
  if (!location) return "";
  if (location.full_address) return location.full_address;
  return [location.region, location.city, location.district, location.street]
    .filter(Boolean)
    .join(" · ");
}

export function densityColor(value: number): string {
  if (value <= 0) return "#1e293b";
  const alpha = 0.25 + value * 0.75;
  return `rgba(56, 189, 248, ${alpha.toFixed(2)})`;
}
