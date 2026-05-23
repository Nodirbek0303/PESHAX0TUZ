# Vercel Deploy — SmartCross AI

## Muammo sababi

GitHub repoda **root** `requirements.txt` (torch, opencv, YOLO) bor.
Vercel buni ko'rib **Python backend** build qilishga urinadi — bu **ishlamaydi**:
- Vercel serverless — OpenCV/YOLO/torch uchun emas
- Build vaqtida xato yoki timeout
- WebSocket + kamera stream Vercelda ishlamaydi

## Yechim

### 1. Root `requirements.txt` ni O'CHIRING

Faqat quyidagi qolishi kerak:
```
backend/requirements.txt
backend/requirements-gpu.txt
backend/requirements-minimal.txt
```

GitHub:
```bash
git rm requirements.txt
git commit -m "fix: remove root requirements.txt for Vercel frontend deploy"
git push
```

### 2. Yangi fayllarni push qiling

- `vercel.json`
- `package.json` (root)
- `.vercelignore`

### 3. Vercel Dashboard sozlamalari

| Sozlama | Qiymat |
|---------|--------|
| Framework | **Other** |
| Root Directory | *(bo'sh)* |
| Build Command | `npm --prefix frontend run build` |
| Output Directory | `frontend/dist` |
| Install Command | `npm --prefix frontend ci` |

Yoki **Root Directory = `frontend`** qilib, Build = `npm run build`, Output = `dist`

### 4. Environment Variables

```
VITE_GOOGLE_MAPS_API_KEY=...
VITE_API_URL=https://SIZNING-BACKEND-SERVER/api/v1
VITE_WS_URL=wss://SIZNING-BACKEND-SERVER/api/v1
```

### 5. Backend alohida serverda

Backend **Docker/VPS** da ishlashi shart:

```bash
docker compose up --build -d
```

Yoki:
```bash
cd backend
pip install -r requirements-gpu.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Xavfsizlik

GitHub repoda `.env` fayl **bo'lmasligi kerak** (API kalitlar ochiq!):

```bash
git rm --cached .env
git commit -m "security: remove .env from repo"
```

`.env` faqat serverda qoladi.

## Arxitektura

```
┌─────────────────┐      HTTPS/WSS      ┌──────────────────┐
│  Vercel         │ ◄────────────────── │  VPS / Docker    │
│  React Dashboard│                     │  FastAPI + AI    │
└─────────────────┘                     └──────────────────┘
```
