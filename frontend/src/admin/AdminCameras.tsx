import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import UzbekistanEmblem from "../components/UzbekistanEmblem";
import { adminDelete, adminFetch, adminPatch, adminPost, getAdminToken, publicGet } from "./api";
import type { AdminCameraListResponse, AdminCameraRecord, CameraInstallPayload } from "./cameraTypes";
import "./admin.css";

const REGION_SUGGESTIONS = [
  "Andijon viloyati",
  "Buxoro viloyati",
  "Farg'ona viloyati",
  "Jizzax viloyati",
  "Xorazm viloyati",
  "Namangan viloyati",
  "Navoiy viloyati",
  "Qashqadaryo viloyati",
  "Qoraqalpog'iston Respublikasi",
  "Samarqand viloyati",
  "Sirdaryo viloyati",
  "Surxondaryo viloyati",
  "Toshkent viloyati",
  "Toshkent shahri",
];

const STEPS = ["Viloyat", "Shahar", "Tuman", "Ko'cha", "Kamera", "O'rnatish"];

type InstallForm = {
  region: string;
  city: string;
  district: string;
  street: string;
  camera_name: string;
  camera_number: string;
  location_name: string;
  gps_lat: string;
  gps_lon: string;
  camera_type: string;
  resolution: string;
  fps: string;
  stream_url: string;
  activate: boolean;
};

const emptyForm: InstallForm = {
  region: "",
  city: "",
  district: "",
  street: "",
  camera_name: "",
  camera_number: "",
  location_name: "",
  gps_lat: "41.2995",
  gps_lon: "69.2401",
  camera_type: "FIXED",
  resolution: "FHD",
  fps: "25",
  stream_url: "",
  activate: true,
};

export default function AdminCameras() {
  const navigate = useNavigate();
  const [data, setData] = useState<AdminCameraListResponse | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<InstallForm>(emptyForm);
  const [cities, setCities] = useState<string[]>([]);
  const [districts, setDistricts] = useState<string[]>([]);
  const [streets, setStreets] = useState<string[]>([]);
  const [installing, setInstalling] = useState(false);

  function loadCameras() {
    setLoading(true);
    adminFetch<AdminCameraListResponse>("/admin/cameras")
      .then(setData)
      .catch((err: Error) => {
        if (err.message === "Sessiya tugadi") navigate("/admin/login");
        else setError(err.message);
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    if (!getAdminToken()) {
      navigate("/admin/login");
      return;
    }
    loadCameras();
  }, [navigate]);

  useEffect(() => {
    if (!form.region) {
      setCities([]);
      return;
    }
    publicGet<{ cities: string[] }>(`/cities?region=${encodeURIComponent(form.region)}`)
      .then((payload) => setCities(payload.cities))
      .catch(() => setCities([]));
  }, [form.region]);

  useEffect(() => {
    if (!form.region || !form.city) {
      setDistricts([]);
      return;
    }
    publicGet<{ districts: string[] }>(
      `/districts?region=${encodeURIComponent(form.region)}&city=${encodeURIComponent(form.city)}`,
    )
      .then((payload) => setDistricts(payload.districts))
      .catch(() => setDistricts([]));
  }, [form.region, form.city]);

  useEffect(() => {
    if (!form.region || !form.city || !form.district) {
      setStreets([]);
      return;
    }
    publicGet<{ streets: string[] }>(
      `/streets?region=${encodeURIComponent(form.region)}&city=${encodeURIComponent(form.city)}&district=${encodeURIComponent(form.district)}`,
    )
      .then((payload) => setStreets(payload.streets))
      .catch(() => setStreets([]));
  }, [form.region, form.city, form.district]);

  const reviewText = useMemo(
    () =>
      `${form.region} · ${form.city} · ${form.district} · ${form.street} · ${form.camera_name}${form.camera_number ? ` №${form.camera_number}` : ""}`,
    [form],
  );

  function updateField<K extends keyof InstallForm>(key: K, value: InstallForm[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function canNext() {
    if (step === 0) return form.region.trim().length > 1;
    if (step === 1) return form.city.trim().length > 1;
    if (step === 2) return form.district.trim().length > 1;
    if (step === 3) return form.street.trim().length > 1;
    if (step === 4) {
      return form.camera_name.trim().length > 1 && form.location_name.trim().length > 1;
    }
    return true;
  }

  async function saveLocationStep() {
    await adminPost("/locations", {
      region: form.region.trim(),
      city: form.city.trim(),
      district: form.district.trim(),
      street: form.street.trim(),
    });
  }

  async function onInstall(event: FormEvent) {
    event.preventDefault();
    setInstalling(true);
    setError("");
    setMessage("");
    const payload: CameraInstallPayload = {
      region: form.region.trim(),
      city: form.city.trim(),
      district: form.district.trim(),
      street: form.street.trim(),
      camera_name: form.camera_name.trim(),
      location_name: form.location_name.trim(),
      gps_lat: Number(form.gps_lat),
      gps_lon: Number(form.gps_lon),
      camera_type: form.camera_type,
      resolution: form.resolution,
      fps: Number(form.fps),
      activate: form.activate,
    };
    if (form.camera_number.trim()) payload.camera_number = form.camera_number.trim();
    if (form.stream_url.trim()) payload.stream_url = form.stream_url.trim();

    try {
      const result = await adminPost<{ camera: AdminCameraRecord }>("/cameras/install", payload);
      setMessage(`Kamera o'rnatildi: ${result.camera.camera_id}`);
      setForm(emptyForm);
      setStep(0);
      loadCameras();
    } catch (err) {
      setError(err instanceof Error ? err.message : "O'rnatish xato");
    } finally {
      setInstalling(false);
    }
  }

  async function toggleStatus(camera: AdminCameraRecord) {
    const next = camera.status === "ONLINE" ? "OFFLINE" : "ONLINE";
    await adminPatch(`/cameras/${camera.camera_id}/status`, { status: next });
    loadCameras();
  }

  async function removeCamera(cameraId: string) {
    if (!window.confirm("Kamerani bazadan o'chirishni tasdiqlaysizmi?")) return;
    await adminDelete(`/cameras/${cameraId}`);
    loadCameras();
  }

  return (
    <div className="admin-shell">
      <header className="admin-header">
        <div className="admin-brand">
          <UzbekistanEmblem className="uz-emblem-img" size={54} />
          <div>
            <h1>KAMERA O&apos;RNATISH VA BOSHQARUV</h1>
            <p>Cheklanmagan kameralar · Bosqichma-bosqich viloyat → shahar → tuman → ko&apos;cha → kamera</p>
          </div>
        </div>
        <div className="admin-header-meta">
          <Link className="admin-btn ghost" to="/admin">
            Dashboard
          </Link>
          <Link className="admin-btn ghost" to="/">
            Operator
          </Link>
        </div>
      </header>

      <div className="admin-camera-page">
        {error && <div className="admin-error">{error}</div>}
        {message && <div className="admin-success">{message}</div>}

        <section className="admin-panel admin-camera-summary">
          <div><span>Jami kameralar</span><strong>{data?.summary.total ?? 0}</strong></div>
          <div><span>Online</span><strong>{data?.summary.online ?? 0}</strong></div>
          <div><span>Offline</span><strong>{data?.summary.offline ?? 0}</strong></div>
          <div><span>Manzillar bazasi</span><strong>{data?.summary.locations ?? 0}</strong></div>
        </section>

        <div className="admin-camera-grid">
          <section className="admin-panel admin-install-panel">
            <h2>Kamera o&apos;rnatish (bosqichma-bosqich)</h2>
            <div className="admin-step-tabs">
              {STEPS.map((label, index) => (
                <button
                  key={label}
                  type="button"
                  className={index === step ? "active" : index < step ? "done" : ""}
                  onClick={() => setStep(index)}
                >
                  {index + 1}. {label}
                </button>
              ))}
            </div>

            <form
              onSubmit={onInstall}
              onKeyDown={(event) => {
                if (event.key === "Enter" && step < 5) event.preventDefault();
              }}
            >
              {step === 0 && (
                <div className="admin-form-grid">
                  <label>
                    Viloyat
                    <input
                      list="region-list"
                      value={form.region}
                      onChange={(e) => updateField("region", e.target.value)}
                      placeholder="Masalan: Toshkent viloyati"
                    />
                    <datalist id="region-list">
                      {REGION_SUGGESTIONS.map((region) => (
                        <option key={region} value={region} />
                      ))}
                    </datalist>
                  </label>
                </div>
              )}

              {step === 1 && (
                <div className="admin-form-grid">
                  <label>
                    Shahar
                    <input
                      list="city-list"
                      value={form.city}
                      onChange={(e) => updateField("city", e.target.value)}
                      placeholder="Masalan: Toshkent shahri"
                    />
                    <datalist id="city-list">
                      {cities.map((city) => (
                        <option key={city} value={city} />
                      ))}
                    </datalist>
                  </label>
                </div>
              )}

              {step === 2 && (
                <div className="admin-form-grid">
                  <label>
                    Tuman
                    <input
                      list="district-list"
                      value={form.district}
                      onChange={(e) => updateField("district", e.target.value)}
                      placeholder="Masalan: Chilonzor tumani"
                    />
                    <datalist id="district-list">
                      {districts.map((district) => (
                        <option key={district} value={district} />
                      ))}
                    </datalist>
                  </label>
                </div>
              )}

              {step === 3 && (
                <div className="admin-form-grid">
                  <label>
                    Ko&apos;cha / manzil
                    <input
                      list="street-list"
                      value={form.street}
                      onChange={(e) => updateField("street", e.target.value)}
                      placeholder="Masalan: Bunyodkor ko'chasi"
                    />
                    <datalist id="street-list">
                      {streets.map((street) => (
                        <option key={street} value={street} />
                      ))}
                    </datalist>
                  </label>
                </div>
              )}

              {step === 4 && (
                <div className="admin-form-grid two-col">
                  <label>
                    Kamera nomi
                    <input value={form.camera_name} onChange={(e) => updateField("camera_name", e.target.value)} />
                  </label>
                  <label>
                    Kamera raqami (ixtiyoriy)
                    <input value={form.camera_number} onChange={(e) => updateField("camera_number", e.target.value)} />
                  </label>
                  <label className="full">
                    Aniq manzil
                    <input value={form.location_name} onChange={(e) => updateField("location_name", e.target.value)} />
                  </label>
                  <label>
                    GPS kenglik (lat)
                    <input value={form.gps_lat} onChange={(e) => updateField("gps_lat", e.target.value)} />
                  </label>
                  <label>
                    GPS uzunlik (lon)
                    <input value={form.gps_lon} onChange={(e) => updateField("gps_lon", e.target.value)} />
                  </label>
                  <label>
                    Kamera turi
                    <select value={form.camera_type} onChange={(e) => updateField("camera_type", e.target.value)}>
                      <option value="FIXED">FIXED</option>
                      <option value="PTZ">PTZ</option>
                      <option value="PANORAMIC">PANORAMIC</option>
                    </select>
                  </label>
                  <label>
                    Aniqlik
                    <select value={form.resolution} onChange={(e) => updateField("resolution", e.target.value)}>
                      <option value="HD">HD</option>
                      <option value="FHD">FHD</option>
                      <option value="4K">4K</option>
                    </select>
                  </label>
                  <label>
                    FPS
                    <input value={form.fps} onChange={(e) => updateField("fps", e.target.value)} />
                  </label>
                  <label className="full">
                    RTSP / stream URL (ixtiyoriy)
                    <input value={form.stream_url} onChange={(e) => updateField("stream_url", e.target.value)} />
                  </label>
                  <label className="full checkbox-row">
                    <input
                      type="checkbox"
                      checked={form.activate}
                      onChange={(e) => updateField("activate", e.target.checked)}
                    />
                    O&apos;rnatilgach darhol ONLINE holatga o&apos;tish
                  </label>
                </div>
              )}

              {step === 5 && (
                <div className="admin-review-box">
                  <h3>Tasdiqlash</h3>
                  <p>{reviewText}</p>
                  <p>
                    GPS: {form.gps_lat}, {form.gps_lon} · {form.camera_type} · {form.resolution} · {form.fps} FPS
                  </p>
                  {form.stream_url && <p>Stream: {form.stream_url}</p>}
                  <p>Holat: {form.activate ? "ONLINE" : "OFFLINE"}</p>
                </div>
              )}

              <div className="admin-step-actions">
                {step > 0 && (
                  <button type="button" className="admin-btn ghost" onClick={() => setStep((value) => value - 1)}>
                    Orqaga
                  </button>
                )}
                {step < 5 && (
                  <button
                    type="button"
                    className="admin-btn"
                    disabled={!canNext()}
                    onClick={async () => {
                      if (step === 3) {
                        try {
                          await saveLocationStep();
                        } catch {
                          /* manzil allaqachon bo'lishi mumkin */
                        }
                      }
                      setStep((value) => value + 1);
                    }}
                  >
                    Keyingi
                  </button>
                )}
                {step === 5 && (
                  <button type="submit" className="admin-btn" disabled={installing}>
                    {installing ? "O'rnatilmoqda..." : "Kamerani o'rnatish va bazaga saqlash"}
                  </button>
                )}
              </div>
            </form>
          </section>

          <section className="admin-panel">
            <h2>Barcha kameralar ({data?.cameras.length ?? 0})</h2>
            {loading && <p className="muted">Yuklanmoqda...</p>}
            <div className="admin-camera-table-wrap">
              <table className="admin-table admin-camera-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Manzil</th>
                    <th>Holat</th>
                    <th>Amallar</th>
                  </tr>
                </thead>
                <tbody>
                  {(data?.cameras ?? []).map((camera) => (
                    <tr key={camera.camera_id}>
                      <td>
                        <strong>{camera.camera_id}</strong>
                        <small>№{camera.camera_number}</small>
                      </td>
                      <td>
                        {camera.region}
                        <br />
                        {camera.city}, {camera.district}
                        <br />
                        {camera.street}
                      </td>
                      <td>
                        <span className={`admin-status-pill ${camera.status.toLowerCase()}`}>{camera.status}</span>
                      </td>
                      <td className="admin-row-actions">
                        <button type="button" className="admin-btn ghost" onClick={() => toggleStatus(camera)}>
                          {camera.status === "ONLINE" ? "Offline" : "Online"}
                        </button>
                        <button type="button" className="admin-btn danger" onClick={() => removeCamera(camera.camera_id)}>
                          O&apos;chirish
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          <section className="admin-panel admin-danger-panel">
            <h2>Tizimni nolga tushirish</h2>
            <p className="muted">
              Barcha kameralar, manzillar, statistika va ogohlantirishlar o&apos;chiriladi. Serverga yangi joylashish uchun ishlating.
            </p>
            <button
              type="button"
              className="admin-btn danger"
              onClick={async () => {
                if (!window.confirm("Barcha ma'lumotlar 0 ga tushirilsinmi?")) return;
                try {
                  await adminPost("/system/reset", {});
                  setMessage("Barcha ma'lumotlar nolga tushirildi.");
                  setForm(emptyForm);
                  setStep(0);
                  loadCameras();
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Reset xato");
                }
              }}
            >
              Barcha ma&apos;lumotlarni 0 ga tushirish
            </button>
          </section>
        </div>
      </div>
    </div>
  );
}
