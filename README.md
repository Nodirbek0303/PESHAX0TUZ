# SmartCross AI v1.0

O'zbekiston bo'ylab peshaxot (zebra) va yo'l ikkala tomonidagi piyodalarni real vaqtda kuzatuvchi AI tizimi.

## Modullar

| Modul | Tavsif | Holat |
|-------|--------|-------|
| 1 | Joylashuv va kamera boshqaruvi (viloyat → shahar → tuman → ko'cha → kamera) | ✅ |
| 2 | Real-vaqt aniqlash va klassifikatsiya (YOLOv8 + DeepSORT) | ✅ |
| 3 | Sanash va statistika | ✅ |
| 4 | Ogohlantirish tizimi (QIZIL / SARIQ / KO'K) | ✅ |
| 5 | Real-vaqt dashboard | ✅ |
| 6 | Texnik arxitektura (FastAPI + React) | ✅ |
| 7 | JSON chiqish formati | ✅ |

## Ma'lumotlar siyosati

**Tizim hech qanday taxminiy yoki tasodifiy raqamlar bermaydi.**

Faqat kameradan olinadigan haqiqiy ma'lumotlar:

- YOLOv8 orqali aniqlangan piyoda (`bbox`, `confidence`)
- DeepSORT trek ID va harakat yo'li
- Kadr piksellaridan hisoblangan tezlik va yo'nalish
- Kiyim rangi (kadr kesimidan)
- Peshaxot zonasi ichida yoki tashqarida (geometrik hisob)
- Kadr ichidagi odamlar soni va guruh holati

Taxminiy demo ma'lumotlar, tasodifiy ogohlantirishlar va namuna rasmlar **o'chirilgan**.

## Admin panel

Respublika darajasidagi boshqaruv paneli (rasmdagidek interfeys):

- URL: http://localhost:5173/admin/login
- **Parol:** `404-UZ_TEAM`

Admin panelda:
- Jami kameralar, odamlar, oqim, ogohlantirishlar
- Google Maps xarita (viloyatlar bo'yicha)
- Live kamera grid
- Jins/yo'nalish diagrammalari
- Ogohlantirishlar va so'nggi deteksiyalar jadvali
- **Kamera o'rnatish** (`/admin/cameras`) — viloyat → shahar → tuman → ko'cha → kamera

Backend API:
- `POST /api/v1/admin/login`
- `GET /api/v1/admin/dashboard` (Bearer token)

`.env`:
```env
ADMIN_PASSWORD=404-UZ_TEAM
```

## Google Maps API

Dashboard **Google Maps** xaritasidan foydalanadi. Backend **Geocoding API** orqali GPS manzilni o'qiydi.

### Sozlash

`frontend/.env`:
```env
VITE_GOOGLE_MAPS_API_KEY=your-google-api-key
```

`backend/.env`:
```env
GOOGLE_API_KEY=your-google-api-key
```

Google Cloud Console'da yoqing:
- **Maps JavaScript API** (dashboard xaritasi)
- **Geocoding API** (manzil aniqlash)

Cheklang: HTTP referrer (`http://localhost:5173/*`) va faqat kerakli API'lar.

### API

- `GET /api/v1/cameras/{camera_id}/google-address` — GPS → Google Maps manzil

## Tez ishga tushirish

### 1. Backend

```powershell
cd backend
pip install -r requirements-gpu.txt
python -m uvicorn app.main:app --reload --port 8000
```

API hujjatlari: http://localhost:8000/docs

### 2. Frontend dashboard

```powershell
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:5173

### 3. Docker (serverga joylash — tavsiya etiladi)

Boshlang'ich holat: **barcha ma'lumotlar 0** (kamera yo'q). Kameralar admin panel orqali qo'shiladi.

```powershell
# Tayyorgarlik (ma'lumotlarni nolga tushirish + .env nusxalash)
.\scripts\deploy-server.ps1

# backend\.env va .env ichida ADMIN_PASSWORD, GOOGLE_API_KEY ni sozlang
docker compose up --build -d
```

- Dashboard: http://SERVER-IP/ (port **80**)
- Backend API: http://SERVER-IP:8000/docs
- Admin: http://SERVER-IP/admin/login

Ma'lumotlar saqlanadi: `backend/app/data/` (Docker volume orqali).

Ma'lumotlarni qayta nolga tushirish:

```powershell
.\scripts\reset-data.ps1
# yoki admin panel: KAMERALAR -> "Barcha ma'lumotlarni 0 ga tushirish"
# yoki API: POST /api/v1/admin/system/reset
```

### 4. Ma'lumotlar bazasi (JSON)

| Fayl | Ma'lumot |
|------|----------|
| `backend/app/data/camera_registry.json` | Barcha kameralar |
| `backend/app/data/location_catalog.json` | Viloyat/shahar/tuman/ko'cha katalogi |

Server qayta ishga tushganda ham saqlanadi. Demo kameralar **o'chirilgan** — faqat admin o'rnatgan kameralar ishlaydi.

### 5. Vercel (faqat frontend dashboard)

**Muhim:** Vercel **backend (Python/YOLO/OpenCV) ni ishga tushira olmaydi**.
Vercel faqat React dashboard uchun. Backend alohida serverda (Docker/VPS) ishlashi kerak.

**Vercel xato sababi:** `requirements.txt` topilsa Python build boshlanadi (torch/opencv — muvaffaqiyatsiz).

**Tuzatish (loyihada qo'shilgan):**
- `vercel.json` — faqat `frontend/dist` build qiladi
- `.vercelignore` — `backend/` ignore qilinadi
- Root `package.json` — Node build

**Vercel sozlamalari:**

| Parametr | Qiymat |
|----------|--------|
| Framework Preset | **Other** |
| Root Directory | *(bo'sh — repo root)* |
| Build Command | `npm --prefix frontend run build` |
| Output Directory | `frontend/dist` |
| Install Command | `npm --prefix frontend ci` |

**Environment Variables** (Vercel Dashboard):

```env
VITE_GOOGLE_MAPS_API_KEY=your-key
VITE_API_URL=https://YOUR-BACKEND-SERVER/api/v1
VITE_WS_URL=wss://YOUR-BACKEND-SERVER/api/v1
```

Agar repo root da `requirements.txt` bo'lsa — **o'chiring** (faqat `backend/requirements.txt` qolsin).

**Arxitektura:**
```
[Vercel]  → React dashboard (statik)
[Docker/VPS] → FastAPI backend + AI + WebSocket
```

---

Dashboard o'ng panelida kaskadli filtrlar:

**Viloyat → Shahar → Tuman → Ko'cha → Kamera (raqam · nom)**

Masalan: `Toshkent viloyati · Toshkent shahri · Chilonzor tumani · Bunyodkor ko'chasi · Peshaxot monitoring №042`

## Asosiy API

| Endpoint | Tavsif |
|----------|--------|
| `GET /api/v1/health` | Tizim holati |
| `GET /api/v1/inference/status` | GPU/CPU inference holati |
| `GET /api/v1/regions` | Viloyatlar ro'yxati |
| `GET /api/v1/cities?region=` | Shaharlar |
| `GET /api/v1/districts?region=&city=` | Tumanlar |
| `GET /api/v1/streets?region=&city=&district=` | Ko'chalar |
| `GET /api/v1/camera-options?...` | Kamera ro'yxati (label + manzil) |
| `GET /api/v1/cameras` | To'liq kamera metadata |
| `GET /api/v1/analyze/{camera_id}` | Bitta kadr tahlili (7-modul JSON) |
| `GET /api/v1/schema/frame-response` | JSON sxema (OpenAPI) |
| `GET /api/v1/snapshot/{camera_id}` | Live JPEG kadr |
| `GET /api/v1/alerts` | So'nggi ogohlantirishlar |
| `WS /api/v1/live-feed/{camera_id}` | 500ms real-vaqt oqim |

## Namuna JSON javob

`GET /api/v1/analyze/{camera_id}` yoki WebSocket orqali:

```json
{
  "request_id": "uuid",
  "timestamp": "2026-05-23T12:00:00+00:00",
  "camera_id": "UZB-TASH-001-CAM-042",
  "frame_number": 128,
  "frame_width": 1280,
  "frame_height": 720,
  "snapshot_url": "/api/v1/snapshot/UZB-TASH-001-CAM-042",
  "detected_persons": [],
  "statistics": {
    "total_count": 0,
    "by_category": {},
    "by_gender": {},
    "by_direction": {},
    "by_side": {},
    "avg_crossing_time": 0,
    "density_map": [],
    "hourly_flow": [],
    "peak_hour": null,
    "violation_count": 0
  },
  "active_alerts": [],
  "zone_counts": {
    "left_side": 0,
    "crosswalk": 0,
    "right_side": 0
  }
}
```

Ogohlantirishlar `location` maydonida to'liq manzilni o'z ichiga oladi.

## GPU inference

`.env` faylida `INFERENCE_MODE=gpu` (default).

```powershell
cd backend
.\scripts\install_gpu.ps1
python -m uvicorn app.main:app --reload --port 8000
```

**Tavsiya:** Python 3.11 yoki 3.12. CUDA bo'lmasa CPU'da ishlaydi.

### RTSP kamera

```env
USE_WEBCAM=false
CAMERA_STREAM_URLS={"UZB-TASH-001-CAM-042":"rtsp://user:pass@192.168.1.10:554/stream1"}
```

### Veb-kamera (laptop)

```env
USE_WEBCAM=true
WEBCAM_INDEX=0
WEBCAM_WIDTH=1280
WEBCAM_HEIGHT=720
```

Tekshirish: `GET /api/v1/camera-source/{camera_id}` → `"source": "webcam"`

### Tashqi signallar (ixtiyoriy)

Svetofor yoki transport xavfi faqat API orqali aniq berilganda ishlaydi:

```http
GET /api/v1/analyze/{camera_id}?traffic_light_red=true&vehicle_proximity_sec=1.5
```

Tizim o'zi tasodifiy signallar yaratmaydi.

## Haqiqiy kamera va sensor integratsiyasi

### 1. Svetofor sensori (tashqi controller)

Svetofor kontrolleri (Arduino, PLC, svetofor API) quyidagi endpointga ma'lumot yuboradi:

```http
POST /api/v1/sensors/UZB-TASH-001-CAM-042/traffic-light
Content-Type: application/json

{"signal": "red", "source": "traffic_controller"}
```

`signal`: `red` | `green` | `yellow`

Holatni o'qish:

```http
GET /api/v1/sensors/UZB-TASH-001-CAM-042
```

### 2. Radar / lidar sensor (transport masofasi)

```http
POST /api/v1/sensors/UZB-TASH-001-CAM-042/vehicle-radar
Content-Type: application/json

{"proximity_sec": 1.4, "source": "mmwave_radar"}
```

`proximity_sec` — transport peshaxotga yetib kelish vaqti (soniya).

### 3. Kameradan transport deteksiyasi (avtomatik)

YOLOv8 bir xil kadrda **piyoda + transport** (car, bus, truck, motorcycle) aniqlaydi va peshaxotga yaqinlashayotgan transport uchun **xavf vaqtini** hisoblaydi.

Live oqimda `sensor_state` maydonida ko'rinadi:
- `vision_vehicle_proximity_sec` — kamera hisobi
- `radar_vehicle_proximity_sec` — radar sensor
- `vehicle_proximity_sec` — eng yaqin (min)

### 4. Svetofor poll (HTTP controller)

`.env` da:

```env
TRAFFIC_LIGHT_POLL_URLS={"UZB-TASH-001-CAM-042":"http://192.168.1.50/api/signal"}
TRAFFIC_LIGHT_POLL_INTERVAL_SEC=3
```

Controller `{"signal":"red"}` JSON qaytarishi kerak.

### 5. Sensor API kaliti (ixtiyoriy)

```env
SENSOR_API_KEY=your-secret-key
```

So'rovda header: `X-Sensor-Key: your-secret-key`

### PowerShell misoli

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/api/v1/sensors/UZB-TASH-001-CAM-042/traffic-light" `
  -ContentType "application/json" `
  -Body '{"signal":"red","source":"plc"}'
```

## Xavfsizlik (8 bosqichli davlat TZ)

Davlat darajasidagi tizim uchun **8 qavatli xavfsizlik** joriy qilingan.
To'liq hujjat: [SECURITY.md](SECURITY.md)

| Bosqich | Himoya |
|---------|--------|
| 1 | Tarmoq/transport — HTTPS, security headers |
| 2 | Autentifikatsiya — JWT + bcrypt parol |
| 3 | Avtorizatsiya — admin/sensor/public rollar |
| 4 | Brute-force/DDoS — rate limit, IP blok |
| 5 | Validatsiya — Pydantic, body limit |
| 6 | Audit jurnali — `security_audit.log` |
| 7 | Maxfiylik — sirlar `.env` da, parol hash |
| 8 | Intrusion Detection — shubhali IP monitoring |

Production parol hash:
```powershell
cd backend
pip install passlib bcrypt PyJWT
python -m app.scripts.hash_password "YangiKuchliParol!"
```

Admin xavfsizlik holati: `GET /api/v1/admin/security/status`

---

```powershell
cd backend
pip install pytest
pytest tests/ -q
```

## Arxitektura

```
Kamera (RTSP / veb-kamera) → OpenCV → YOLOv8 → DeepSORT → Atribut tahlili
  → Statistika → Ogohlantirish → FastAPI → React Dashboard
```

**Reja (keyingi versiya):** Redis cache, PostgreSQL arxiv, markaziy cloud sinxronizatsiya.

## Stack

- **Backend:** FastAPI, OpenCV, Ultralytics YOLOv8, DeepSORT, Pydantic v2
- **Frontend:** React 18, Vite, Leaflet, Recharts
- **Deploy:** Docker Compose (backend + frontend + Redis + Postgres)
