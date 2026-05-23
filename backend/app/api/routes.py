import asyncio

from fastapi import APIRouter, Depends, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

from app.core.config import settings
from app.core.schemas import (
    CameraMetadata,
    CameraStatus,
    FrameResponse,
    LiveFeedMessage,
    TrafficLightUpdate,
    VehicleRadarUpdate,
)
from app.services.alerts import alert_service
from app.services.camera_manager import camera_manager
from app.services.frame_source import frame_source_manager
from app.services.google_geo import reverse_geocode
from app.services.pipeline import pipeline_service
from app.services.sensor_service import sensor_service

router = APIRouter()


def verify_sensor_api_key(x_sensor_key: str | None = Header(default=None)) -> None:
    if settings.security_require_sensor_key or settings.sensor_api_key:
        if not settings.sensor_api_key or x_sensor_key != settings.sensor_api_key:
            raise HTTPException(status_code=401, detail="Sensor API kaliti talab qilinadi")


@router.get("/health")
async def health() -> dict:
    inference = pipeline_service.inference_status()
    return {
        "status": "online",
        "system": "SmartCross AI v1.0",
        "mode": "24/7 real-vaqt",
        "inference_mode": settings.inference_mode,
        "inference_ready": inference.get("ready"),
        "inference_device": inference.get("device"),
    }


@router.get("/inference/status")
async def inference_status() -> dict:
    return pipeline_service.inference_status()


@router.get("/cameras", response_model=list[CameraMetadata])
async def list_cameras(
    region: str | None = None,
    city: str | None = None,
    district: str | None = None,
    street: str | None = None,
    camera_number: str | None = None,
    status: CameraStatus | None = None,
) -> list[CameraMetadata]:
    return camera_manager.list_cameras(
        region=region,
        city=city,
        district=district,
        street=street,
        camera_number=camera_number,
        status=status,
    )


@router.get("/cameras/{camera_id}", response_model=CameraMetadata)
async def get_camera(camera_id: str) -> CameraMetadata:
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Kamera topilmadi")
    return camera


@router.get("/cameras/{camera_id}/google-address")
async def camera_google_address(camera_id: str) -> dict:
    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Kamera topilmadi")
    address = await reverse_geocode(camera.gps_coords.lat, camera.gps_coords.lon)
    if not address:
        raise HTTPException(status_code=503, detail="Google Geocoding javob bermadi")
    return address


@router.get("/regions")
async def list_regions() -> dict:
    return {"regions": camera_manager.regions()}


@router.get("/cities")
async def list_cities(region: str | None = Query(default=None)) -> dict:
    return {"cities": camera_manager.cities(region=region)}


@router.get("/districts")
async def list_districts(
    region: str | None = Query(default=None),
    city: str | None = Query(default=None),
) -> dict:
    return {"districts": camera_manager.districts(region=region, city=city)}


@router.get("/streets")
async def list_streets(
    region: str | None = Query(default=None),
    city: str | None = Query(default=None),
    district: str | None = Query(default=None),
) -> dict:
    return {"streets": camera_manager.streets(region=region, city=city, district=district)}


@router.get("/camera-options")
async def list_camera_options(
    region: str | None = Query(default=None),
    city: str | None = Query(default=None),
    district: str | None = Query(default=None),
    street: str | None = Query(default=None),
) -> dict:
    return {"cameras": camera_manager.camera_options(region=region, city=city, district=district, street=street)}


@router.get("/analyze/{camera_id}", response_model=FrameResponse)
async def analyze_frame(
    camera_id: str,
    traffic_light_red: bool | None = Query(default=None),
    vehicle_proximity_sec: float | None = Query(default=None),
) -> FrameResponse:
    if not camera_manager.get_camera(camera_id):
        raise HTTPException(status_code=404, detail="Kamera topilmadi")
    return pipeline_service.process_camera(
        camera_id,
        traffic_light_red=traffic_light_red,
        vehicle_proximity_sec=vehicle_proximity_sec,
    )


@router.get("/sensors/{camera_id}")
async def get_sensor_state(camera_id: str) -> dict:
    if not camera_manager.get_camera(camera_id):
        raise HTTPException(status_code=404, detail="Kamera topilmadi")
    _, state = sensor_service.merge_vehicle_proximity(camera_id, None)
    state.traffic_light = sensor_service.get_traffic_light_reading(camera_id)
    state.traffic_light_red = sensor_service.traffic_light_is_red(camera_id)
    return {"sensor_state": state}


@router.post("/sensors/{camera_id}/traffic-light")
async def update_traffic_light(
    camera_id: str,
    payload: TrafficLightUpdate,
    _: None = Depends(verify_sensor_api_key),
) -> dict:
    if not camera_manager.get_camera(camera_id):
        raise HTTPException(status_code=404, detail="Kamera topilmadi")
    reading = sensor_service.set_traffic_light(camera_id, payload.signal, payload.source)
    return {"ok": True, "traffic_light": reading}


@router.post("/sensors/{camera_id}/vehicle-radar")
async def update_vehicle_radar(
    camera_id: str,
    payload: VehicleRadarUpdate,
    _: None = Depends(verify_sensor_api_key),
) -> dict:
    if not camera_manager.get_camera(camera_id):
        raise HTTPException(status_code=404, detail="Kamera topilmadi")
    reading = sensor_service.set_vehicle_radar(camera_id, payload.proximity_sec, payload.source)
    return {"ok": True, "vehicle_proximity": reading}


@router.get("/alerts")
async def list_alerts(limit: int = Query(default=20, ge=1, le=100)) -> dict:
    return {"alerts": alert_service.recent_all(limit=limit)}


@router.get("/alerts/{camera_id}")
async def camera_alerts(camera_id: str) -> dict:
    if not camera_manager.get_camera(camera_id):
        raise HTTPException(status_code=404, detail="Kamera topilmadi")
    return {"alerts": alert_service.get_active(camera_id)}


@router.get("/camera-source/{camera_id}")
async def camera_source(camera_id: str) -> dict:
    if not camera_manager.get_camera(camera_id):
        raise HTTPException(status_code=404, detail="Kamera topilmadi")
    pipeline_service.process_camera(camera_id)
    return frame_source_manager.get_source_info(camera_id)


@router.get("/snapshot/{camera_id}")
async def camera_snapshot(camera_id: str) -> Response:
    if not camera_manager.get_camera(camera_id):
        raise HTTPException(status_code=404, detail="Kamera topilmadi")
    image = frame_source_manager.get_snapshot_jpeg(camera_id)
    if not image:
        pipeline_service.process_camera(camera_id)
        image = frame_source_manager.get_snapshot_jpeg(camera_id)
    if not image:
        raise HTTPException(status_code=503, detail="Kamera kadri mavjud emas")
    return Response(content=image, media_type="image/jpeg")


@router.websocket("/live-feed/{camera_id}")
async def live_feed(websocket: WebSocket, camera_id: str) -> None:
    if not camera_manager.get_camera(camera_id):
        await websocket.close(code=4404)
        return

    await websocket.accept()
    queue = await pipeline_service.subscribe(camera_id)

    try:
        while True:
            frame: FrameResponse = await queue.get()
            message = LiveFeedMessage(data=frame)
            await websocket.send_json(message.model_dump(mode="json"))
    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        raise
    except Exception:
        pass
    finally:
        pipeline_service.unsubscribe(camera_id, queue)


@router.get("/schema/frame-response")
async def frame_response_schema() -> dict:
    """7-modul: JSON chiqish sxemasi (OpenAPI-compatible)."""
    return FrameResponse.model_json_schema()
