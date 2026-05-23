from __future__ import annotations

import re
from datetime import datetime, timezone
from threading import Lock

from app.core.schemas import (
    CameraInstallRequest,
    CameraMetadata,
    CameraStatus,
    CameraUpdateRequest,
    CrosswalkZone,
    GpsCoords,
)
from app.services.camera_store import (
    LOCATION_CATALOG_PATH,
    REGISTRY_PATH,
    load_cameras,
    load_location_catalog,
    save_cameras,
    save_location_catalog,
)

REGION_CODES: dict[str, str] = {
    "Toshkent viloyati": "TASH",
    "Andijon viloyati": "AND",
    "Buxoro viloyati": "BUK",
    "Farg'ona viloyati": "FER",
    "Jizzax viloyati": "JIZ",
    "Xorazm viloyati": "XOR",
    "Namangan viloyati": "NAM",
    "Navoiy viloyati": "NAV",
    "Qashqadaryo viloyati": "QAS",
    "Qoraqalpog'iston Respublikasi": "QRP",
    "Samarqand viloyati": "SAM",
    "Sirdaryo viloyati": "SIR",
    "Surxondaryo viloyati": "SUR",
    "Toshkent shahri": "TSH",
}


class CameraManager:
    """1-MODUL: Joylashuv va kamera boshqaruvi (cheklanmagan, JSON bazada saqlanadi)."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._cameras: dict[str, CameraMetadata] = {}
        self._location_catalog: list[dict[str, str]] = []
        self._bootstrap()

    def _bootstrap(self) -> None:
        stored = load_cameras()
        self._cameras = {camera.camera_id: camera for camera in stored}
        self._location_catalog = load_location_catalog()
        if self._cameras:
            self._sync_catalog_from_cameras()
        if not REGISTRY_PATH.exists():
            self._persist()
        if not LOCATION_CATALOG_PATH.exists():
            save_location_catalog(self._location_catalog)

    def _persist(self) -> None:
        save_cameras(list(self._cameras.values()))

    def _sync_catalog_from_cameras(self) -> None:
        for camera in self._cameras.values():
            self._remember_location(camera.region, camera.city, camera.district, camera.street, persist=False)
        save_location_catalog(self._location_catalog)

    def _remember_location(
        self,
        region: str,
        city: str,
        district: str,
        street: str,
        *,
        persist: bool = True,
    ) -> None:
        entry = {
            "region": region.strip(),
            "city": city.strip(),
            "district": district.strip(),
            "street": street.strip(),
        }
        if entry not in self._location_catalog:
            self._location_catalog.append(entry)
            if persist:
                save_location_catalog(self._location_catalog)

    def _region_code(self, region: str) -> str:
        if region in REGION_CODES:
            return REGION_CODES[region]
        cleaned = re.sub(r"[^A-Za-z0-9 ]", "", region.upper())
        parts = cleaned.split()
        code = "".join(part[:2] for part in parts[:3]) or "UZ"
        return code[:6]

    def _next_camera_number(self, region: str, city: str, district: str, street: str) -> str:
        cameras = self.list_cameras(region=region, city=city, district=district, street=street)
        numbers = [int(camera.camera_number) for camera in cameras if camera.camera_number.isdigit()]
        return f"{max(numbers, default=0) + 1:03d}"

    def _generate_camera_id(self, region: str, camera_number: str) -> str:
        code = self._region_code(region)
        prefix = f"UZB-{code}-"
        seq_numbers = []
        for camera_id in self._cameras:
            if camera_id.startswith(prefix):
                parts = camera_id.split("-")
                if len(parts) >= 3 and parts[2].isdigit():
                    seq_numbers.append(int(parts[2]))
        seq = max(seq_numbers, default=0) + 1
        return f"UZB-{code}-{seq:03d}-CAM-{camera_number}"

    def list_cameras(
        self,
        region: str | None = None,
        city: str | None = None,
        district: str | None = None,
        street: str | None = None,
        camera_number: str | None = None,
        status: CameraStatus | None = None,
    ) -> list[CameraMetadata]:
        cameras = list(self._cameras.values())
        if region:
            cameras = [camera for camera in cameras if camera.region.lower() == region.lower()]
        if city:
            cameras = [camera for camera in cameras if camera.city.lower() == city.lower()]
        if district:
            cameras = [camera for camera in cameras if camera.district.lower() == district.lower()]
        if street:
            cameras = [camera for camera in cameras if camera.street.lower() == street.lower()]
        if camera_number:
            cameras = [camera for camera in cameras if camera.camera_number == camera_number]
        if status:
            cameras = [camera for camera in cameras if camera.status == status]
        return cameras

    def get_camera(self, camera_id: str) -> CameraMetadata | None:
        return self._cameras.get(camera_id)

    def get_stream_url(self, camera_id: str) -> str | None:
        camera = self.get_camera(camera_id)
        if camera and camera.stream_url:
            return camera.stream_url
        return None

    def register_camera(self, camera: CameraMetadata) -> CameraMetadata:
        with self._lock:
            self._cameras[camera.camera_id] = camera
            self._remember_location(camera.region, camera.city, camera.district, camera.street, persist=False)
            self._persist()
            save_location_catalog(self._location_catalog)
        return camera

    def install_camera(self, payload: CameraInstallRequest) -> CameraMetadata:
        camera_number = payload.camera_number or self._next_camera_number(
            payload.region, payload.city, payload.district, payload.street
        )
        camera_id = self._generate_camera_id(payload.region, camera_number)

        if camera_id in self._cameras:
            raise ValueError("Bu kamera ID allaqachon mavjud")

        camera = CameraMetadata(
            camera_id=camera_id,
            region=payload.region.strip(),
            city=payload.city.strip(),
            district=payload.district.strip(),
            street=payload.street.strip(),
            camera_name=payload.camera_name.strip(),
            camera_number=camera_number,
            location_name=payload.location_name.strip(),
            gps_coords=GpsCoords(lat=payload.gps_lat, lon=payload.gps_lon),
            camera_type=payload.camera_type,
            resolution=payload.resolution,
            fps=payload.fps,
            status=CameraStatus.ONLINE if payload.activate else CameraStatus.OFFLINE,
            stream_url=payload.stream_url.strip() if payload.stream_url else None,
            installed_at=datetime.now(timezone.utc),
        )
        return self.register_camera(camera)

    def update_camera(self, camera_id: str, payload: CameraUpdateRequest) -> CameraMetadata | None:
        camera = self._cameras.get(camera_id)
        if not camera:
            return None

        updates = payload.model_dump(exclude_unset=True)
        gps_lat = updates.pop("gps_lat", None)
        gps_lon = updates.pop("gps_lon", None)
        if gps_lat is not None or gps_lon is not None:
            updates["gps_coords"] = GpsCoords(
                lat=gps_lat if gps_lat is not None else camera.gps_coords.lat,
                lon=gps_lon if gps_lon is not None else camera.gps_coords.lon,
            )

        updated = camera.model_copy(update=updates)
        with self._lock:
            self._cameras[camera_id] = updated
            self._remember_location(updated.region, updated.city, updated.district, updated.street, persist=False)
            self._persist()
            save_location_catalog(self._location_catalog)
        return updated

    def delete_camera(self, camera_id: str) -> bool:
        with self._lock:
            if camera_id not in self._cameras:
                return False
            del self._cameras[camera_id]
            self._persist()
        return True

    def add_location(self, region: str, city: str, district: str, street: str) -> dict[str, str]:
        self._remember_location(region, city, district, street)
        return {"region": region.strip(), "city": city.strip(), "district": district.strip(), "street": street.strip()}

    def update_status(self, camera_id: str, status: CameraStatus) -> CameraMetadata | None:
        return self.update_camera(camera_id, CameraUpdateRequest(status=status))

    def _filtered(
        self,
        region: str | None = None,
        city: str | None = None,
        district: str | None = None,
    ) -> list[CameraMetadata]:
        return self.list_cameras(region=region, city=city, district=district)

    def _catalog_values(
        self,
        *,
        region: str | None = None,
        city: str | None = None,
        district: str | None = None,
        key: str,
    ) -> set[str]:
        values = set()
        for entry in self._location_catalog:
            if region and entry["region"].lower() != region.lower():
                continue
            if city and entry["city"].lower() != city.lower():
                continue
            if district and entry["district"].lower() != district.lower():
                continue
            values.add(entry[key])
        return values

    def regions(self) -> list[str]:
        values = {camera.region for camera in self._cameras.values()} | self._catalog_values(key="region")
        return sorted(values)

    def cities(self, region: str | None = None) -> list[str]:
        values = {camera.city for camera in self._filtered(region=region)} | self._catalog_values(
            region=region, key="city"
        )
        return sorted(values)

    def districts(self, region: str | None = None, city: str | None = None) -> list[str]:
        values = {camera.district for camera in self._filtered(region=region, city=city)} | self._catalog_values(
            region=region, city=city, key="district"
        )
        return sorted(values)

    def streets(
        self,
        region: str | None = None,
        city: str | None = None,
        district: str | None = None,
    ) -> list[str]:
        values = {camera.street for camera in self._filtered(region=region, city=city, district=district)} | self._catalog_values(
            region=region, city=city, district=district, key="street"
        )
        return sorted(values)

    def camera_options(
        self,
        region: str | None = None,
        city: str | None = None,
        district: str | None = None,
        street: str | None = None,
    ) -> list[dict]:
        cameras = self.list_cameras(region=region, city=city, district=district, street=street)
        return [
            {
                "camera_id": camera.camera_id,
                "camera_name": camera.camera_name,
                "camera_number": camera.camera_number,
                "label": f"№{camera.camera_number} — {camera.camera_name}",
                "full_address": camera.full_address,
                "status": camera.status.value,
            }
            for camera in cameras
        ]

    def location_payload(self, camera_id: str) -> dict | None:
        camera = self.get_camera(camera_id)
        if not camera:
            return None
        return {
            "region": camera.region,
            "city": camera.city,
            "district": camera.district,
            "street": camera.street,
            "camera_name": camera.camera_name,
            "camera_number": camera.camera_number,
            "location_name": camera.location_name,
            "full_address": camera.full_address,
            "gps_coords": camera.gps_coords.model_dump(),
        }

    def reset_all(self) -> dict:
        with self._lock:
            self._cameras = {}
            self._location_catalog = []
            save_cameras([])
            save_location_catalog([])
        return self.admin_summary()

    def admin_summary(self) -> dict:
        cameras = list(self._cameras.values())
        return {
            "total": len(cameras),
            "online": sum(1 for camera in cameras if camera.status == CameraStatus.ONLINE),
            "offline": sum(1 for camera in cameras if camera.status == CameraStatus.OFFLINE),
            "maintenance": sum(1 for camera in cameras if camera.status == CameraStatus.MAINTENANCE),
            "locations": len(self._location_catalog),
        }


camera_manager = CameraManager()
