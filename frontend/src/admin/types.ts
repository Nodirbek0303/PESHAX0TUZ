export interface AdminSummary {
  total_cameras: number;
  online_cameras: number;
  offline_cameras: number;
  people_now: number;
  crosswalk_now: number;
  today_flow: number;
  active_alerts: number;
  danger_alerts: number;
  violations: number;
}

export interface AdminCameraCard {
  camera_id: string;
  camera_name: string;
  camera_number: string;
  region: string;
  city: string;
  district: string;
  street: string;
  status: string;
  gps_coords: { lat: number; lon: number };
  people_count: number;
  crosswalk_count: number;
  vehicles: number;
  snapshot_url?: string;
  alerts_count: number;
}

export interface AdminDashboardData {
  generated_at: string;
  summary: AdminSummary;
  demographics: {
    by_category: Record<string, number>;
    by_gender: Record<string, number>;
    by_direction: Record<string, number>;
    by_side: Record<string, number>;
  };
  hourly_flow: number[];
  regions: Array<{ region: string; cameras: number; online: number; people: number }>;
  cameras: AdminCameraCard[];
  alerts: Array<Record<string, unknown>>;
  recent_detections: Array<Record<string, unknown>>;
}
