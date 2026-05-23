import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin_routes import router as admin_router
from app.api.routes import router
from app.core.config import settings
from app.middleware.security_middleware import SecurityMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.pipeline import pipeline_service
    from app.services.sensor_service import sensor_service

    status = pipeline_service.inference_status()
    print(
        f"[SmartCross] inference={status['mode']} ready={status['ready']} "
        f"device={status.get('device')} message={status.get('message')} "
        f"security={settings.security_environment}"
    )

    poll_task = None
    if settings.traffic_light_poll_urls:

        async def poll_loop() -> None:
            while True:
                await sensor_service.poll_all_traffic_lights()
                await asyncio.sleep(settings.traffic_light_poll_interval_sec)

        poll_task = asyncio.create_task(poll_loop())

    yield

    if poll_task is not None:
        poll_task.cancel()
    shutdown = getattr(pipeline_service.inference, "shutdown", None)
    if callable(shutdown):
        shutdown()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="O'zbekiston bo'ylab peshaxot monitoring — SmartCross AI v1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.security_enable_docs else None,
    redoc_url="/redoc" if settings.security_enable_docs else None,
    openapi_url="/openapi.json" if settings.security_enable_docs else None,
)

app.add_middleware(SecurityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Sensor-Key", "X-Request-ID"],
)

app.include_router(router, prefix=settings.api_prefix)
app.include_router(admin_router, prefix=settings.api_prefix)


@app.get("/")
async def root() -> dict:
    return {
        "system": settings.app_name,
        "version": settings.app_version,
        "security_environment": settings.security_environment,
        "security_layers": 8,
        "api_docs": "/docs" if settings.security_enable_docs else "disabled",
        "inference_status": f"{settings.api_prefix}/inference/status",
    }
