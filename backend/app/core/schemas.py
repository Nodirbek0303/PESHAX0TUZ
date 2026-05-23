from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class CameraType(str, Enum):
    PTZ = "PTZ"
    FIXED = "FIXED"
    PANORAMIC = "PANORAMIC"


class Resolution(str, Enum):
    HD = "HD"
    FHD = "FHD"
    K4 = "4K"


class CameraStatus(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"


class PersonCategory(str, Enum):
    PIYODA = "piyoda"
    YOSH_BOLA = "yosh_bola"
    OSMIR = "o'smir"
    YOSH_KATTA = "yosh_katta"
    ORTA_YOSH = "o'rta_yosh"
    KEKSA = "keksa"
    NOGIRONLAR = "nogironlar"


class Gender(str, Enum):
    AYOL = "ayol"
    ERKAK = "erkak"
    ANIQLANMADI = "aniqlanmadi"


class AgeRange(str, Enum):
    ANIQLANMADI = "aniqlanmadi"
    R0_12 = "0-12"
    R13_17 = "13-17"
    R18_25 = "18-25"
    R26_35 = "26-35"
    R36_50 = "36-50"
    R51_60 = "51-60"
    R60_PLUS = "60+"


class Direction(str, Enum):
    N = "N"
    NE = "NE"
    E = "E"
    SE = "SE"
    S = "S"
    SW = "SW"
    W = "W"
    NW = "NW"


class SpeedClass(str, Enum):
    SEKIN = "sekin"
    NORMAL = "normal"
    TEZ = "tez"


class GroupStatus(str, Enum):
    YOLGIZ = "yolg'iz"
    JUFT = "juft"
    GURUH_3_5 = "guruh_3-5"
    OLOMON_6_PLUS = "olomon_6+"


class HandOccupancy(str, Enum):
    BOSH = "bo'sh"
    TELEFON = "telefon"
    SUMKA = "sumka"
    BOLA_QOLINDA = "bola_qo'lida"
    TAYOQ_ARAVA = "tayoq/arava"


class CrosswalkPresence(str, Enum):
    HA = "ha"
    YOQ = "yo'q"
    QISMAN = "qisman"


class AlertSeverity(str, Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    BLUE = "BLUE"


class AlertType(str, Enum):
    QIZIL_CHIROQ_BUZISH = "QIZIL_CHIROQ_BUZISH"
    TRANSPORT_TOQNASHUV = "TRANSPORT_TO'QNASHUV"
    BOLA_YOLGIZ = "BOLA_YOLGIZ"
    NOGIRON_XAVF = "NOGIRON_XAVF"
    KEKSA_SEKIN = "KEKSA_SEKIN"
    GURUH_TOSIQCHI = "GURUH_TO'SIQCHI"
    ATROFGA_QARAMADI = "ATROFGA_QARAMADI"
    TELEFON_CHALGITISH = "TELEFON_CHALG'ITISH"
    GAVJUMLIK_OSHDI = "GAVJUMLIK_OSHDI"
    KAMERA_OFFLINE = "KAMERA_OFFLINE"
    TIZIM_YUKLANISH = "TIZIM_YUKLANISH"


class GpsCoords(BaseModel):
    lat: float
    lon: float


class CrosswalkZone(BaseModel):
    polygon: list[list[float]]


class CameraMetadata(BaseModel):
    camera_id: str
    region: str
    city: str
    district: str
    street: str
    camera_name: str
    camera_number: str
    location_name: str
    gps_coords: GpsCoords
    camera_type: CameraType
    resolution: Resolution
    fps: int
    status: CameraStatus
    crosswalk_zones: list[CrosswalkZone] = Field(default_factory=list)
    stream_url: str | None = None
    installed_at: datetime | None = None

    @property
    def full_address(self) -> str:
        return (
            f"{self.region} · {self.city} · {self.district} · {self.street} · "
            f"{self.camera_name} №{self.camera_number}"
        )


class CameraInstallRequest(BaseModel):
    region: str = Field(min_length=2)
    city: str = Field(min_length=2)
    district: str = Field(min_length=2)
    street: str = Field(min_length=2)
    camera_name: str = Field(min_length=2)
    camera_number: str | None = None
    location_name: str = Field(min_length=2)
    gps_lat: float
    gps_lon: float
    camera_type: CameraType = CameraType.FIXED
    resolution: Resolution = Resolution.FHD
    fps: int = Field(default=25, ge=1, le=60)
    stream_url: str | None = None
    activate: bool = True


class CameraUpdateRequest(BaseModel):
    region: str | None = None
    city: str | None = None
    district: str | None = None
    street: str | None = None
    camera_name: str | None = None
    camera_number: str | None = None
    location_name: str | None = None
    gps_lat: float | None = None
    gps_lon: float | None = None
    camera_type: CameraType | None = None
    resolution: Resolution | None = None
    fps: int | None = Field(default=None, ge=1, le=60)
    stream_url: str | None = None
    status: CameraStatus | None = None


class LocationEntryRequest(BaseModel):
    region: str = Field(min_length=2)
    city: str = Field(min_length=2)
    district: str = Field(min_length=2)
    street: str = Field(min_length=2)


class TrackPoint(BaseModel):
    x: float
    y: float
    t: float


class DetectedPerson(BaseModel):
    person_id: str
    category: PersonCategory
    gender: Gender
    age_range: AgeRange
    clothing_color: str
    direction: Direction
    speed_ms: float
    speed_class: SpeedClass
    group_status: GroupStatus
    qol_band: HandOccupancy
    yol_qaraydi: bool
    peshaxot_ichida: CrosswalkPresence
    in_crosswalk: bool
    bbox: list[float]
    confidence: float
    track_path: list[TrackPoint] = Field(default_factory=list)
    birinchi_korish: datetime | None = None
    oxirgi_korish: datetime | None = None
    otish_vaqti: float | None = None


class ZoneCounts(BaseModel):
    left_side: int = 0
    crosswalk: int = 0
    right_side: int = 0


class DetectedVehicle(BaseModel):
    vehicle_id: str
    vehicle_type: str
    bbox: list[float]
    confidence: float
    speed_ms: float = 0.0
    approaching_crosswalk: bool = False


class TrafficLightReading(BaseModel):
    signal: str
    source: str
    updated_at: datetime | None = None
    is_stale: bool = False


class VehicleProximityReading(BaseModel):
    proximity_sec: float | None = None
    source: str
    updated_at: datetime | None = None
    is_stale: bool = False


class CameraSensorState(BaseModel):
    traffic_light_red: bool = False
    traffic_light: TrafficLightReading | None = None
    vehicle_proximity_sec: float | None = None
    vehicle_proximity: VehicleProximityReading | None = None
    vision_vehicle_proximity_sec: float | None = None
    radar_vehicle_proximity_sec: float | None = None
    detected_vehicles: int = 0


class Statistics(BaseModel):
    total_count: int = 0
    by_category: dict[str, int] = Field(default_factory=dict)
    by_gender: dict[str, int] = Field(default_factory=dict)
    by_direction: dict[str, int] = Field(default_factory=dict)
    by_side: dict[str, int] = Field(default_factory=dict)
    avg_crossing_time: float = 0.0
    density_map: list[list[float]] = Field(default_factory=list)
    hourly_flow: list[int] = Field(default_factory=list)
    peak_hour: int | None = None
    violation_count: int = 0


class Alert(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    camera_id: str
    location: dict[str, Any]
    alert_type: AlertType
    severity: AlertSeverity
    person_id: str | None = None
    category: str | None = None
    description: str
    recommended_action: str
    snapshot_url: str | None = None


class TrafficLightUpdate(BaseModel):
    signal: str = Field(description="red | green | yellow")
    source: str = "traffic_controller"


class VehicleRadarUpdate(BaseModel):
    proximity_sec: float = Field(ge=0, description="Transport peshaxotga yetib kelish vaqti (soniya)")
    source: str = "radar_sensor"


class FrameResponse(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    camera_id: str
    frame_number: int
    frame_width: int = 1280
    frame_height: int = 720
    snapshot_url: str | None = None
    detected_persons: list[DetectedPerson]
    detected_vehicles: list[DetectedVehicle] = Field(default_factory=list)
    sensor_state: CameraSensorState | None = None
    statistics: Statistics
    active_alerts: list[Alert]
    zone_counts: ZoneCounts


class LiveFeedMessage(BaseModel):
    type: str = "frame_update"
    data: FrameResponse
