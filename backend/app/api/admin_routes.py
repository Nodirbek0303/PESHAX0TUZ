from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.schemas import CameraInstallRequest, CameraStatus, CameraUpdateRequest, LocationEntryRequest
from app.middleware.security_middleware import get_client_ip
from app.services.admin_service import admin_service
from app.services.audit_service import audit_service
from app.services.camera_manager import camera_manager
from app.services.security_service import get_security_report
from app.services.system_service import reset_all_runtime_data

router = APIRouter(prefix="/admin", tags=["Admin"])


class AdminLoginRequest(BaseModel):
    password: str = Field(min_length=4, max_length=128)


class CameraStatusRequest(BaseModel):
    status: CameraStatus


def require_admin(authorization: str | None = Header(default=None)) -> str:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not admin_service.verify_token(token):
        raise HTTPException(status_code=401, detail="Admin autentifikatsiya talab qilinadi")
    return token or ""


@router.post("/login")
async def admin_login(payload: AdminLoginRequest, request: Request) -> dict:
    ip = get_client_ip(request)
    result = admin_service.login(payload.password, ip=ip)
    if not result:
        raise HTTPException(status_code=401, detail="Kirish rad etildi")
    token, expires_hours = result
    return {"token": token, "role": "super_admin", "expires_hours": expires_hours}


@router.post("/logout")
async def admin_logout(request: Request, token: str = Depends(require_admin)) -> dict:
    admin_service.logout(token, ip=get_client_ip(request))
    return {"ok": True}


@router.get("/dashboard")
async def admin_dashboard(_token: str = Depends(require_admin)) -> dict:
    return admin_service.build_dashboard()


@router.get("/verify")
async def admin_verify(_token: str = Depends(require_admin)) -> dict:
    return {"ok": True, "role": "super_admin"}


@router.get("/security/status")
async def admin_security_status(_token: str = Depends(require_admin)) -> dict:
    return get_security_report()


@router.get("/security/audit")
async def admin_security_audit(_token: str = Depends(require_admin)) -> dict:
    return {"events": audit_service.recent(limit=100)}


@router.get("/cameras")
async def admin_list_cameras(_token: str = Depends(require_admin)) -> dict:
    cameras = camera_manager.list_cameras()
    return {
        "summary": camera_manager.admin_summary(),
        "cameras": [camera.model_dump(mode="json") for camera in cameras],
    }


@router.post("/cameras/install")
async def admin_install_camera(
    payload: CameraInstallRequest,
    request: Request,
    _token: str = Depends(require_admin),
) -> dict:
    try:
        camera = camera_manager.install_camera(payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    audit_service.log(
        "CAMERA_INSTALL",
        ip=get_client_ip(request),
        actor="admin",
        detail=camera.camera_id,
        metadata={"address": camera.full_address},
    )
    return {"ok": True, "camera": camera.model_dump(mode="json")}


@router.put("/cameras/{camera_id}")
async def admin_update_camera(
    camera_id: str,
    payload: CameraUpdateRequest,
    request: Request,
    _token: str = Depends(require_admin),
) -> dict:
    camera = camera_manager.update_camera(camera_id, payload)
    if not camera:
        raise HTTPException(status_code=404, detail="Kamera topilmadi")
    audit_service.log("CAMERA_UPDATE", ip=get_client_ip(request), actor="admin", detail=camera_id)
    return {"ok": True, "camera": camera.model_dump(mode="json")}


@router.patch("/cameras/{camera_id}/status")
async def admin_update_camera_status(
    camera_id: str,
    payload: CameraStatusRequest,
    request: Request,
    _token: str = Depends(require_admin),
) -> dict:
    camera = camera_manager.update_status(camera_id, payload.status)
    if not camera:
        raise HTTPException(status_code=404, detail="Kamera topilmadi")
    audit_service.log(
        "CAMERA_STATUS",
        ip=get_client_ip(request),
        actor="admin",
        detail=f"{camera_id}:{payload.status.value}",
    )
    return {"ok": True, "camera": camera.model_dump(mode="json")}


@router.delete("/cameras/{camera_id}")
async def admin_delete_camera(
    camera_id: str,
    request: Request,
    _token: str = Depends(require_admin),
) -> dict:
    if not camera_manager.delete_camera(camera_id):
        raise HTTPException(status_code=404, detail="Kamera topilmadi")
    audit_service.log("CAMERA_DELETE", ip=get_client_ip(request), actor="admin", detail=camera_id)
    return {"ok": True}


@router.get("/locations")
async def admin_locations(_token: str = Depends(require_admin)) -> dict:
    return {
        "regions": camera_manager.regions(),
        "summary": {"locations": len(camera_manager.list_cameras())},
    }


@router.post("/locations")
async def admin_add_location(payload: LocationEntryRequest, _token: str = Depends(require_admin)) -> dict:
    entry = camera_manager.add_location(payload.region, payload.city, payload.district, payload.street)
    return {"ok": True, "entry": entry}


@router.post("/system/reset")
async def admin_reset_system(request: Request, _token: str = Depends(require_admin)) -> dict:
    audit_service.log("SYSTEM_RESET_REQUEST", ip=get_client_ip(request), actor="admin")
    result = reset_all_runtime_data()
    audit_service.log("SYSTEM_RESET_OK", ip=get_client_ip(request), actor="admin")
    return result
