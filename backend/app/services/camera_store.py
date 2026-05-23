from __future__ import annotations

import json
from pathlib import Path

from app.core.schemas import CameraMetadata

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
REGISTRY_PATH = DATA_DIR / "camera_registry.json"
LOCATION_CATALOG_PATH = DATA_DIR / "location_catalog.json"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_cameras() -> list[CameraMetadata]:
    _ensure_data_dir()
    if not REGISTRY_PATH.exists():
        return []
    raw = _read_json(REGISTRY_PATH)
    return [CameraMetadata.model_validate(item) for item in raw.get("cameras", [])]


def save_cameras(cameras: list[CameraMetadata]) -> None:
    _ensure_data_dir()
    payload = {"cameras": [camera.model_dump(mode="json") for camera in cameras]}
    REGISTRY_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_location_catalog() -> list[dict[str, str]]:
    _ensure_data_dir()
    if not LOCATION_CATALOG_PATH.exists():
        return []
    raw = _read_json(LOCATION_CATALOG_PATH)
    return list(raw.get("entries", []))


def save_location_catalog(entries: list[dict[str, str]]) -> None:
    _ensure_data_dir()
    LOCATION_CATALOG_PATH.write_text(
        json.dumps({"entries": entries}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
