export interface AdminCameraRecord {
  camera_id: string;
  region: string;
  city: string;
  district: string;
  street: string;
  camera_name: string;
  camera_number: string;
  location_name: string;
  gps_coords: { lat: number; lon: number };
  camera_type: string;
  resolution: string;
  fps: number;
  status: string;
  stream_url?: string | null;
  installed_at?: string | null;
  full_address?: string;
}

export interface AdminCameraListResponse {
  summary: {
    total: number;
    online: number;
    offline: number;
    maintenance: number;
    locations: number;
  };
  cameras: AdminCameraRecord[];
}

export interface CameraInstallPayload {
  region: string;
  city: string;
  district: string;
  street: string;
  camera_name: string;
  camera_number?: string;
  location_name: string;
  gps_lat: number;
  gps_lon: number;
  camera_type: string;
  resolution: string;
  fps: number;
  stream_url?: string;
  activate: boolean;
}
