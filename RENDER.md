# Render.com — Backend deploy

## Xato sababi (status 127)

Render **Node.js** sifatida deploy qilgan (`yarn build` ishladi), lekin **start command yo'q** — shuning uchun `Exited with status 127`.

SmartCross **backend Python (FastAPI)** — Node emas!

---

## To'g'ri yechim

### Variant A — Blueprint (tavsiya)

1. Render Dashboard → **mavjud noto'g'ri servisni o'chiring**
2. **New → Blueprint**
3. Repo: `Nodirbek0303/PESHAX0TUZ`
4. `render.yaml` avtomatik o'qiladi
5. **ADMIN_PASSWORD** = `404-UZ_TEAM` kiriting
6. Deploy

### Variant B — Qo'lda Web Service

| Sozlama | Qiymat |
|---------|--------|
| **Language** | **Python 3** (Node emas!) |
| **Root Directory** | `backend` |
| **Build Command** | `pip install -r requirements-minimal.txt` |
| **Start Command** | `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Health Check** | `/api/v1/health` |

**Environment Variables:**

```
USE_WEBCAM=false
SECURITY_ENVIRONMENT=production
SECURITY_ENABLE_DOCS=false
ADMIN_PASSWORD=404-UZ_TEAM
CORS_ORIGINS=["https://peshax0tuz.vercel.app","https://peshax0t.vercel.app"]
```

---

## Deploy tugagach

Backend URL masalan: `https://peshax0t-api.onrender.com`

**Vercel** `vercel.json` yangilang:

```json
"destination": "https://peshax0t-api.onrender.com/api/:path*"
```

Keyin: `npx vercel deploy --prod --yes`

Endi tunnel va kompyuter kerak bo'lmaydi!
