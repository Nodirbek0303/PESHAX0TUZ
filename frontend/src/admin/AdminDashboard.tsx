import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import CameraMap from "../components/CameraMap";
import UzbekistanEmblem from "../components/UzbekistanEmblem";
import UzbekistanBanner from "../components/UzbekistanBanner";
import UzbekistanFlag from "../components/UzbekistanFlag";
import type { Camera } from "../types";
import { adminFetch, clearAdminToken, getAdminToken } from "./api";
import type { AdminCameraCard, AdminDashboardData } from "./types";
import "./admin.css";

const PIE_COLORS = ["#22d3ee", "#a78bfa", "#f472b6", "#34d399", "#fbbf24", "#fb7185"];

function formatClock(date: Date) {
  return date.toLocaleTimeString("uz-UZ", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function formatDate(date: Date) {
  return date.toLocaleDateString("uz-UZ", { weekday: "long", day: "2-digit", month: "2-digit", year: "numeric" });
}

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [now, setNow] = useState(new Date());
  const [data, setData] = useState<AdminDashboardData | null>(null);
  const [error, setError] = useState("");
  const [refreshTick, setRefreshTick] = useState(0);
  const [selectedCameraId, setSelectedCameraId] = useState("");

  useEffect(() => {
    if (!getAdminToken()) {
      navigate("/admin/login");
      return;
    }
    adminFetch<AdminDashboardData>("/admin/dashboard")
      .then((payload) => {
        setData(payload);
        setSelectedCameraId((current) => current || payload.cameras[0]?.camera_id || "");
      })
      .catch((err: Error) => {
        if (err.message === "Sessiya tugadi") navigate("/admin/login");
        else setError(err.message);
      });
  }, [navigate, refreshTick]);

  useEffect(() => {
    const clock = window.setInterval(() => setNow(new Date()), 1000);
    const refresh = window.setInterval(() => setRefreshTick((value) => value + 1), 10000);
    return () => {
      window.clearInterval(clock);
      window.clearInterval(refresh);
    };
  }, []);

  const mapCameras: Camera[] = useMemo(() => {
    if (!data) return [];
    return data.cameras.map((camera) => ({
      camera_id: camera.camera_id,
      region: camera.region,
      city: camera.city,
      district: camera.district,
      street: camera.street,
      camera_name: camera.camera_name,
      camera_number: camera.camera_number,
      location_name: camera.street,
      gps_coords: camera.gps_coords,
      camera_type: "FIXED",
      resolution: "FHD",
      fps: 25,
      status: camera.status as Camera["status"],
    }));
  }, [data]);

  const selectedCamera: AdminCameraCard | undefined = useMemo(
    () => data?.cameras.find((camera) => camera.camera_id === selectedCameraId) ?? data?.cameras[0],
    [data, selectedCameraId],
  );

  const demographicPie = useMemo(() => {
    if (!data) return [];
    const gender = data.demographics.by_gender;
    return [
      { name: "Ayol", value: gender.ayol ?? 0 },
      { name: "Erkak", value: gender.erkak ?? 0 },
      { name: "Aniqlanmadi", value: gender.aniqlanmadi ?? 0 },
      { name: "Piyoda", value: data.demographics.by_category.piyoda ?? 0 },
    ].filter((item) => item.value > 0);
  }, [data]);

  const hourlyData = useMemo(() => {
    if (!data) return [];
    return data.hourly_flow.map((count, hour) => ({ hour: `${hour}:00`, count }));
  }, [data]);

  const directionRows = useMemo(() => {
    if (!data) return [];
    const dir = data.demographics.by_direction;
    return [
      { label: "Chapdan o'ngga", value: dir.chapdan ?? 0 },
      { label: "O'ngdan chapga", value: dir["o'ngdan"] ?? 0 },
      { label: "Peshaxot", value: data.demographics.by_side.crosswalk ?? 0 },
      { label: "Chap yo'lak", value: data.demographics.by_side.left_sidewalk ?? 0 },
      { label: "O'ng yo'lak", value: data.demographics.by_side.right_sidewalk ?? 0 },
    ];
  }, [data]);

  function logout() {
    clearAdminToken();
    navigate("/admin/login");
  }

  if (!data && !error) {
    return <div className="admin-loading">Admin panel yuklanmoqda...</div>;
  }

  const summary = data?.summary;
  const onlinePct = summary?.total_cameras
    ? ((summary.online_cameras / summary.total_cameras) * 100).toFixed(1)
    : "0";

  return (
    <div className="admin-shell">
      <header className="admin-header">
        <div className="admin-brand">
          <UzbekistanEmblem className="uz-emblem-img" size={64} />
          <div>
            <h1>BUTUN RESPUBLIKA – INTELLEKTUAL NAZORAT TIZIMI</h1>
            <p>Cheklanmagan kameralar · Barcha ma&apos;lumotlar bitta bazada · Har bir odam to&apos;liq hisobotda</p>
          </div>
        </div>
        <div className="admin-search">
          <input placeholder="Qidirish... (kamera, manzil, ID)" />
        </div>
        <div className="admin-header-meta">
          <UzbekistanFlag className="uz-flag-img" width={68} height={44} side="right" />
          <div>
            <strong>{formatClock(now)}</strong>
            <span>{formatDate(now)}</span>
          </div>
          <button type="button" className="admin-btn ghost" onClick={() => navigate("/")}>
            Operator
          </button>
          <button type="button" className="admin-btn danger" onClick={logout}>
            Chiqish
          </button>
        </div>
      </header>

      <div className="admin-symbols-strip">
        <UzbekistanBanner className="uz-banner-img header-banner" height={78} />
      </div>

      <nav className="admin-nav-tabs">
        {[
          { label: "BOSH SAHIFA", to: "/admin" },
          { label: "XARITA", to: "/admin" },
          { label: "KAMERALAR", to: "/admin/cameras" },
          { label: "ODAMLAR", to: "/admin" },
          { label: "HISOBOTLAR", to: "/admin" },
          { label: "STATISTIKA", to: "/admin" },
          { label: "OGOHLANTIRISHLAR", to: "/admin" },
          { label: "TIZIM SOZLAMALARI", to: "/admin" },
        ].map((tab, index) => (
          <Link key={tab.label} className={tab.to === "/admin/cameras" ? "" : index === 0 ? "active" : ""} to={tab.to}>
            {tab.label}
          </Link>
        ))}
      </nav>

      {error && <div className="admin-error admin-error-top">{error}</div>}

      <div className="admin-command-grid">
        <aside className="admin-command-left">
          <section className="admin-panel admin-big-stats">
            <h2>Jami ma&apos;lumot</h2>
            <div className="admin-mega-stat">
              <span>Jami kameralar</span>
              <strong>{summary?.total_cameras ?? 0}</strong>
              <small>Online: {summary?.online_cameras ?? 0}</small>
            </div>
            <div className="admin-mega-stat">
              <span>Hozir odamlar</span>
              <strong>{summary?.people_now ?? 0}</strong>
              <small>Peshaxot: {summary?.crosswalk_now ?? 0}</small>
            </div>
            <div className="admin-mega-stat accent">
              <span>Bugungi oqim</span>
              <strong>{summary?.today_flow ?? 0}</strong>
              <small>Real vaqt yig&apos;indisi</small>
            </div>
          </section>

          <section className="admin-panel">
            <h2>Real vaqtda odamlar oqimi</h2>
            <ResponsiveContainer width="100%" height={150}>
              <LineChart data={hourlyData}>
                <CartesianGrid stroke="#1e3a5f" strokeDasharray="3 3" />
                <XAxis dataKey="hour" tick={{ fill: "#94a3b8", fontSize: 9 }} interval={5} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 9 }} width={28} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#00ff88" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </section>

          <section className="admin-panel">
            <h2>Odamlar bo&apos;yicha taqsimot</h2>
            <ResponsiveContainer width="100%" height={140}>
              <PieChart>
                <Pie data={demographicPie.length ? demographicPie : [{ name: "Ma'lumot yo'q", value: 1 }]} dataKey="value" nameKey="name" innerRadius={38} outerRadius={58}>
                  {(demographicPie.length ? demographicPie : [{ name: "Ma'lumot yo'q", value: 1 }]).map((_, index) => (
                    <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="admin-legend-list">
              {(demographicPie.length ? demographicPie : [{ name: "Ma'lumot yo'q", value: 0 }]).map((item) => (
                <div key={item.name}>
                  <span>{item.name}</span>
                  <strong>{item.value}</strong>
                </div>
              ))}
            </div>
          </section>

          <section className="admin-panel">
            <h2>Yo&apos;nalishlar bo&apos;yicha oqim</h2>
            <div className="admin-flow-list">
              {directionRows.map((row) => (
                <div key={row.label}>
                  <span>{row.label}</span>
                  <strong>{row.value}</strong>
                </div>
              ))}
            </div>
          </section>

          <section className="admin-panel">
            <h2>Ogohlantirishlar</h2>
            <div className="admin-alert-feed">
              {(data?.alerts ?? []).length === 0 && <p className="muted">Faol ogohlantirish yo&apos;q</p>}
              {(data?.alerts ?? []).slice(0, 6).map((alert, index) => (
                <div key={String(alert.alert_id ?? index)} className={`admin-alert-item ${String(alert.severity ?? "").toLowerCase()}`}>
                  <strong>{String(alert.alert_type ?? "ALERT")}</strong>
                  <span>{String(alert.description ?? "")}</span>
                  <small>{String(alert.camera_id ?? "")}</small>
                </div>
              ))}
            </div>
          </section>
        </aside>

        <main className="admin-command-center">
          <section className="admin-panel admin-map-panel">
            <h2>Respublika bo&apos;yicha xarita</h2>
            <CameraMap
              cameras={mapCameras}
              selectedCameraId={selectedCameraId}
              onSelect={(camera) => setSelectedCameraId(camera.camera_id)}
            />
            <div className="admin-region-list">
              {(data?.regions ?? []).map((region) => (
                <div key={region.region}>
                  <span>{region.region}</span>
                  <strong>{region.cameras} kamera · {region.people} odam</strong>
                </div>
              ))}
            </div>
          </section>

          <section className="admin-system-metrics">
            <div><span>Online kameralar</span><strong>{summary?.online_cameras ?? 0}</strong><small>{onlinePct}%</small></div>
            <div><span>Offline kameralar</span><strong>{summary?.offline_cameras ?? 0}</strong></div>
            <div><span>Deteksiya modeli</span><strong>YOLOv8</strong></div>
            <div><span>Faol hududlar</span><strong>{data?.regions.length ?? 0}</strong></div>
            <div><span>Tizim ishlash vaqti</span><strong>99.99%</strong></div>
          </section>

          <section className="admin-panel">
            <h2>So&apos;nggi faoliyat</h2>
            <table className="admin-table admin-activity-table">
              <thead>
                <tr>
                  <th>Vaqt</th>
                  <th>Hudud</th>
                  <th>Kamera</th>
                  <th>Turi</th>
                  <th>Tavsif</th>
                  <th>Natija</th>
                </tr>
              </thead>
              <tbody>
                {(data?.recent_detections ?? []).slice(0, 8).map((row, index) => (
                  <tr key={`${row.person_id}-${index}`}>
                    <td>{String(row.timestamp ?? "").slice(11, 19)}</td>
                    <td>{String(row.city ?? row.region ?? "")}</td>
                    <td>№{String(row.camera_number ?? "")}</td>
                    <td>Piyoda aniqlash</td>
                    <td>ID {String(row.person_id ?? "")} · {String(row.category ?? "")}</td>
                    <td className="ok">Aniqlandi</td>
                  </tr>
                ))}
                {(data?.alerts ?? []).slice(0, 4).map((alert, index) => {
                  const location = alert.location as { city?: string; region?: string } | undefined;
                  return (
                  <tr key={`alert-${index}`}>
                    <td>{String(alert.timestamp ?? "").slice(11, 19)}</td>
                    <td>{String(location?.city ?? location?.region ?? "")}</td>
                    <td>{String(alert.camera_id ?? "")}</td>
                    <td>{String(alert.alert_type ?? "Ogohlantirish")}</td>
                    <td>{String(alert.description ?? "")}</td>
                    <td className={String(alert.severity ?? "").toLowerCase() === "red" ? "bad" : "warn"}>
                      {String(alert.severity ?? "INFO")}
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </section>
        </main>

        <aside className="admin-command-right">
          <section className="admin-panel admin-camera-focus">
            <h2>Har bir kamera bo&apos;yicha ma&apos;lumot</h2>
            {selectedCamera ? (
              <>
                <div className="admin-focus-preview">
                  {selectedCamera.snapshot_url ? (
                    <img src={`${selectedCamera.snapshot_url}?t=${refreshTick}`} alt={selectedCamera.camera_name} />
                  ) : (
                    <div className="admin-live-empty">Kadr yo&apos;q</div>
                  )}
                  <span className="admin-live-badge">LIVE</span>
                </div>
                <div className="admin-focus-meta">
                  <div><span>Kamera ID</span><strong>{selectedCamera.camera_id}</strong></div>
                  <div><span>Manzil</span><strong>{selectedCamera.city}, {selectedCamera.street}</strong></div>
                  <div><span>Raqam</span><strong>№{selectedCamera.camera_number}</strong></div>
                  <div><span>Holat</span><strong className="ok">{selectedCamera.status}</strong></div>
                  <div><span>Bugun</span><strong>{selectedCamera.people_count} odam</strong></div>
                </div>
                <div className="admin-focus-actions">
                  <button type="button" className="admin-btn">Live ko&apos;rish</button>
                  <button type="button" className="admin-btn ghost">Hisobot</button>
                </div>
              </>
            ) : (
              <p className="muted">Kamera tanlanmagan</p>
            )}
          </section>

          <section className="admin-panel">
            <h2>Kamera faoliyat statistikasi</h2>
            <div className="admin-quick-stats">
              <div><span>Aniqlangan odamlar</span><strong>{selectedCamera?.people_count ?? 0}</strong></div>
              <div><span>Peshaxotda</span><strong>{selectedCamera?.crosswalk_count ?? 0}</strong></div>
              <div><span>Transport</span><strong>{selectedCamera?.vehicles ?? 0}</strong></div>
              <div><span>Ogohlantirishlar</span><strong>{selectedCamera?.alerts_count ?? 0}</strong></div>
            </div>
          </section>

          <section className="admin-panel">
            <h2>So&apos;nggi aniqlangan odamlar</h2>
            <div className="admin-face-row">
              {(data?.recent_detections ?? []).slice(0, 7).map((row, index) => (
                <div key={`face-${index}`} className="admin-face-chip" title={String(row.person_id ?? "")}>
                  <span>{String(row.person_id ?? "?").slice(-2)}</span>
                  <small>{String(row.timestamp ?? "").slice(11, 16)}</small>
                </div>
              ))}
            </div>
          </section>

          <section className="admin-panel">
            <h2>Tezkor statistika</h2>
            <div className="admin-quick-stats">
              <div><span>Jami odamlar</span><strong>{summary?.people_now ?? 0}</strong></div>
              <div><span>Peshaxot oqimi</span><strong>{summary?.crosswalk_now ?? 0}</strong></div>
              <div><span>Faol ogohlantirish</span><strong>{summary?.active_alerts ?? 0}</strong></div>
              <div><span>Qizil ogohlantirish</span><strong>{summary?.danger_alerts ?? 0}</strong></div>
              <div><span>Qoidabuzarlik</span><strong>{summary?.violations ?? 0}</strong></div>
            </div>
          </section>
        </aside>
      </div>

      <footer className="admin-footer">
        <div className="admin-footer-modules">
          <span>Intellektual tahlil</span>
          <span>Yuz tanish</span>
          <span>Harakat tahlili</span>
          <span>Oqim tahlili</span>
          <span>Xavfsizlik nazorati</span>
          <span>Ma&apos;lumot xavfsizligi</span>
          <span>24/7 texnik yordam</span>
        </div>
        <span>SmartCross AI v3.2.1 · Har bir odam muhim — har bir son aniq</span>
      </footer>
    </div>
  );
}
