from __future__ import annotations

import logging
import sys
from threading import Lock

import cv2
import numpy as np

from app.core.config import settings
from app.services.camera_manager import camera_manager

logger = logging.getLogger(__name__)


class FrameSourceManager:
    """Faqat haqiqiy kamera manbalari: veb-kamera, RTSP yoki video fayl."""

    def __init__(self) -> None:
        self._captures: dict[str, cv2.VideoCapture] = {}
        self._source_types: dict[str, str] = {}
        self._latest_frames: dict[str, np.ndarray] = {}
        self._lock = Lock()

    def _open_webcam(self) -> cv2.VideoCapture | None:
        backends = [cv2.CAP_DSHOW, cv2.CAP_ANY] if sys.platform == "win32" else [cv2.CAP_ANY]
        for backend in backends:
            capture = cv2.VideoCapture(settings.webcam_index, backend)
            if not capture.isOpened():
                capture.release()
                continue
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, settings.webcam_width)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.webcam_height)
            ok, frame = capture.read()
            if ok and frame is not None:
                logger.info(
                    "Veb-kamera ochildi: index=%s backend=%s size=%sx%s",
                    settings.webcam_index,
                    backend,
                    frame.shape[1],
                    frame.shape[0],
                )
                return capture
            capture.release()
        logger.warning("Veb-kamera ochilmadi: index=%s", settings.webcam_index)
        return None

    def _open_capture(self, camera_id: str) -> tuple[cv2.VideoCapture | None, str]:
        stream_url = camera_manager.get_stream_url(camera_id) or settings.camera_stream_urls.get(camera_id) or settings.default_stream_url

        if settings.use_webcam:
            capture = self._open_webcam()
            if capture is not None:
                return capture, "webcam"

        if stream_url:
            capture = cv2.VideoCapture(stream_url)
            if capture.isOpened():
                logger.info("RTSP manba ochildi: %s", stream_url)
                return capture, "rtsp"
            capture.release()

        if settings.demo_video_path:
            capture = cv2.VideoCapture(settings.demo_video_path)
            if capture.isOpened():
                logger.info("Video fayl ochildi: %s", settings.demo_video_path)
                return capture, "video_file"
            capture.release()

        logger.warning("Kamera manbasi topilmadi: %s", camera_id)
        return None, "none"

    def get_source_info(self, camera_id: str) -> dict:
        source = self._source_types.get(camera_id, "unknown")
        frame = self._latest_frames.get(camera_id)
        return {
            "camera_id": camera_id,
            "source": source,
            "use_webcam": settings.use_webcam,
            "webcam_index": settings.webcam_index,
            "width": frame.shape[1] if frame is not None else None,
            "height": frame.shape[0] if frame is not None else None,
        }

    def get_frame(self, camera_id: str) -> tuple[np.ndarray | None, dict]:
        meta = {"source": "none", "width": 0, "height": 0}

        with self._lock:
            capture = self._captures.get(camera_id)
            source_type = self._source_types.get(camera_id, "none")

            if capture is None or not capture.isOpened():
                capture, source_type = self._open_capture(camera_id)
                if capture is None:
                    return None, meta
                self._captures[camera_id] = capture
                self._source_types[camera_id] = source_type

            ok, frame = capture.read()
            if not ok or frame is None:
                if source_type in {"webcam", "rtsp"}:
                    capture.release()
                    self._captures.pop(camera_id, None)
                    capture, source_type = self._open_capture(camera_id)
                    if capture is not None:
                        self._captures[camera_id] = capture
                        self._source_types[camera_id] = source_type
                        ok, frame = capture.read()
                elif source_type == "video_file":
                    capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ok, frame = capture.read()

            if not ok or frame is None:
                return None, meta

            meta["source"] = self._source_types.get(camera_id, source_type)
            meta["width"] = frame.shape[1]
            meta["height"] = frame.shape[0]
            self._latest_frames[camera_id] = frame.copy()
            return frame, meta

    def get_latest_frame(self, camera_id: str) -> np.ndarray | None:
        frame = self._latest_frames.get(camera_id)
        if frame is not None:
            return frame
        frame, _meta = self.get_frame(camera_id)
        return frame

    def get_snapshot_jpeg(self, camera_id: str) -> bytes | None:
        frame = self.get_latest_frame(camera_id)
        if frame is None:
            return None
        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            return None
        return encoded.tobytes()

    def release(self, camera_id: str | None = None) -> None:
        with self._lock:
            if camera_id:
                capture = self._captures.pop(camera_id, None)
                self._source_types.pop(camera_id, None)
                if capture is not None:
                    capture.release()
                return
            for capture in self._captures.values():
                capture.release()
            self._captures.clear()
            self._source_types.clear()


frame_source_manager = FrameSourceManager()
