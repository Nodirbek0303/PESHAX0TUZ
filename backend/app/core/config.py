from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SmartCross AI v1.0"
    app_version: str = "1.0.0"
    api_prefix: str = "/api/v1"

    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql+asyncpg://smartcross:smartcross@localhost:5432/smartcross"

    ws_update_interval_ms: int = 500
    snapshot_interval_sec: int = 1
    aggregation_interval_sec: int = 60
    cloud_sync_interval_sec: int = 300

    inference_mode: str = "gpu"
    inference_device: str = "auto"  # auto | cuda:0 | cpu
    yolo_model: str = "yolov8n.pt"
    yolo_confidence: float = 0.45
    yolo_iou: float = 0.5
    tracker_max_age: int = 30
    tracker_n_init: int = 3
    reference_frame_width: int = 720
    reference_frame_height: int = 640
    default_stream_url: str | None = None
    demo_video_path: str | None = None
    use_webcam: bool = True
    webcam_index: int = 0
    webcam_width: int = 1280
    webcam_height: int = 720
    camera_stream_urls: dict[str, str] = {}
    gpu_load_alert_threshold: float = 85.0
    crosswalk_density_limit: int = 15
    enable_vision_vehicle_detection: bool = True
    vehicle_proximity_alert_sec: float = 2.0
    vehicle_approach_buffer_px: int = 200
    sensor_stale_after_sec: int = 15
    traffic_light_poll_urls: dict[str, str] = {}
    traffic_light_poll_interval_sec: int = 3
    sensor_api_key: str | None = None

    google_api_key: str | None = None
    admin_password: str = "404-UZ_TEAM"
    admin_password_hash: str | None = None
    admin_token_ttl_hours: int = 8

    security_environment: str = "development"  # development | production
    security_secret_key: str = "change-me-in-production-use-64-char-random-secret-key!!"
    security_require_sensor_key: bool = False
    security_enable_docs: bool = True
    security_rate_limit_per_minute: int = 120
    security_login_rate_limit_per_minute: int = 10
    security_login_max_attempts: int = 5
    security_login_lockout_minutes: int = 15
    security_max_body_bytes: int = 1_048_576
    security_admin_ip_allowlist: list[str] = []

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "https://peshax0t.vercel.app",
    ]


settings = Settings()
