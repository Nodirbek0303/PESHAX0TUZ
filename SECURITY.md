# SmartCross AI — 8 Bosqichli Davlat Xavfsizlik Tizimi (TZ)

> **Maqsad:** O'zbekiston Respublikasi darajasidagi intellektual nazorat tizimi uchun
> kiberhujumlarga qarshi ko'p qavatli (defense-in-depth) himoya.

---

## 1-BOSQICH: Tarmoq va transport himoyasi

| Talab | Amalga oshirish |
|-------|-----------------|
| HTTPS/TLS 1.2+ | Nginx/reverse-proxy orqali SSL sertifikat |
| Xavfsiz HTTP sarlavhalar | `SecurityHeadersMiddleware` |
| Firewall | Faqat 80/443 ochiq; 8000 faqat ichki tarmoq |
| WebSocket himoyasi | TLS orqali `wss://` |

**Sarlavhalar:** `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`, `Referrer-Policy`, `Permissions-Policy`

---

## 2-BOSQICH: Autentifikatsiya (kimligini tasdiqlash)

| Talab | Amalga oshirish |
|-------|-----------------|
| Admin parol | Bcrypt hash (`ADMIN_PASSWORD_HASH`) |
| JWT token | Imzolangan, muddatli (`SECURITY_SECRET_KEY`) |
| Token TTL | Default 8 soat, sozlanadi |
| Chiqish | Token bekor qilish (revoke) |

**Ishlab chiqilgan:** `app/core/security.py`, `AdminService.login()`

---

## 3-BOSQICH: Avtorizatsiya (ruxsat nazorati)

| Rol | Ruxsat |
|-----|--------|
| `public` | Faqat o'qish (kamera, snapshot, WS) |
| `admin` | Bearer JWT — kamera CRUD, reset, dashboard |
| `sensor` | `X-Sensor-Key` — faqat sensor POST |

Production rejimida sensor kaliti **majburiy** (`SECURITY_REQUIRE_SENSOR_KEY=true`).

---

## 4-BOSQICH: Brute-force va DDoS himoyasi

| Parametr | Default |
|----------|---------|
| Login urinishlari | 5 marta |
| Bloklash vaqti | 15 daqiqa |
| Umumiy rate limit | 120 so'rov/daqiqa/IP |
| Admin login limit | 10 so'rov/daqiqa/IP |

**Ishlab chiqilgan:** `app/services/intrusion_service.py`

---

## 5-BOSQICH: Kirish validatsiyasi va sanitizatsiya

| Talab | Amalga oshirish |
|-------|-----------------|
| Pydantic v2 sxemalar | Barcha POST/PUT body |
| Max body hajmi | 1 MB limit |
| ID/injection | Regex va uzunlik cheklovi |
| CORS | Faqat ruxsat etilgan domenlar |

---

## 6-BOSQICH: Audit jurnali (hisobdorlik)

Barcha muhim hodisalar yoziladi: `backend/app/data/security_audit.log`

| Hodisa | Misol |
|--------|-------|
| ADMIN_LOGIN_OK | Muvaffaqiyatli kirish |
| ADMIN_LOGIN_FAIL | Noto'g'ri parol |
| ADMIN_LOGOUT | Chiqish |
| CAMERA_INSTALL | Kamera o'rnatildi |
| CAMERA_DELETE | Kamera o'chirildi |
| SYSTEM_RESET | Ma'lumotlar nolga tushirildi |
| IP_BLOCKED | IP vaqtincha bloklandi |
| INTRUSION_ALERT | Shubhali faollik |

Admin: `GET /api/v1/admin/security/audit`

---

## 7-BOSQICH: Ma'lumotlar maxfiyligi va sirlar

| Ma'lumot | Himoya |
|----------|--------|
| Admin parol | `.env` da hash, gitga kirmaydi |
| JWT kalit | `SECURITY_SECRET_KEY` — min 32 belgi |
| Google API | Faqat server `.env` |
| Kamera RTSP | Bazada, tashqariga chiqmaydi |
| Frontend token | `sessionStorage` (tab yopilganda o'chadi) |

**Production checklist:**
```env
SECURITY_ENVIRONMENT=production
SECURITY_SECRET_KEY=<64+ random hex>
ADMIN_PASSWORD_HASH=<bcrypt hash>
SECURITY_REQUIRE_SENSOR_KEY=true
SENSOR_API_KEY=<strong random>
SECURITY_ENABLE_DOCS=false
```

Parol hash yaratish:
```powershell
cd backend
python -m app.scripts.hash_password "YangiKuchliParol!"
```

---

## 8-BOSQICH: Intrusion Detection va monitoring

| Funksiya | Tavsif |
|----------|--------|
| IP bloklash | Ko'p muvaffaqiyatsiz login |
| Shubhali so'rov | 429 rate limit |
| Xavfsizlik holati | `GET /admin/security/status` |
| Request ID | Har bir so'rovda `X-Request-ID` |
| Prod docs | `/docs` yopiq |

---

## Server joylash — xavfsizlik checklist

- [ ] `SECURITY_ENVIRONMENT=production`
- [ ] Kuchli `SECURITY_SECRET_KEY` (64+ belgi)
- [ ] `ADMIN_PASSWORD_HASH` (oddiy parol emas)
- [ ] `SENSOR_API_KEY` o'rnatilgan
- [ ] HTTPS sertifikat (Let's Encrypt)
- [ ] Firewall: faqat 443 ochiq
- [ ] `CORS_ORIGINS` faqat ruxsat etilgan domen
- [ ] `security_audit.log` muntazam backup
- [ ] Admin panel faqat VPN/ichki tarmoq (ixtiyoriy `SECURITY_ADMIN_IP_ALLOWLIST`)

---

## Xavfsizlik kontaktlari

- **Texnik xavfsizlik:** tizim administratori
- **Audit log joyi:** `backend/app/data/security_audit.log`
- **API holati:** `GET /api/v1/admin/security/status` (admin token bilan)
