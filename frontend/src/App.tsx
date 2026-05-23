import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
import type { Alert, Camera, CameraOption, FrameResponse, InferenceStatus } from "./types";
import { alertLocationText, cameraFullAddress } from "./types";
import UzbekistanEmblem from "./components/UzbekistanEmblem";
import UzbekistanBanner from "./components/UzbekistanBanner";
import UzbekistanFlag from "./components/UzbekistanFlag";
import "./operator.css";

const API = import.meta.env.VITE_API_URL ?? "/api/v1";

function wsBaseUrl(): string {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL;
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}${API}`;
}

async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API}${path}`);
  if (!response.ok) {
    throw new Error(`API xato: ${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

function severityClass(severity: Alert["severity"]) {
  if (severity === "RED") return "alert-red";
  if (severity === "YELLOW") return "alert-yellow";
  return "alert-blue";
}

export default function App() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [regions, setRegions] = useState<string[]>([]);
  const [cities, setCities] = useState<string[]>([]);
  const [districts, setDistricts] = useState<string[]>([]);
  const [streets, setStreets] = useState<string[]>([]);
  const [cameraOptions, setCameraOptions] = useState<CameraOption[]>([]);
  const [selectedRegion, setSelectedRegion] = useState("");
  const [selectedCity, setSelectedCity] = useState("");
  const [selectedDistrict, setSelectedDistrict] = useState("");
  const [selectedStreet, setSelectedStreet] = useState("");
  const [selectedCamera, setSelectedCamera] = useState<string>("");
  const [liveFrame, setLiveFrame] = useState<FrameResponse | null>(null);
  const [recentAlerts, setRecentAlerts] = useState<Alert[]>([]);
  const [connected, setConnected] = useState(false);
  const [videoSource, setVideoSource] = useState<string>("");
  const [inference, setInference] = useState<InferenceStatus | null>(null);
  const [apiError, setApiError] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [googleAddress, setGoogleAddress] = useState<string>("");
  const [now, setNow] = useState(new Date());
  const reconnectDelay = useRef(1000);

  const selectCamera = useCallback((camera: Camera) => {
    setSelectedRegion(camera.region);
    setSelectedCity(camera.city);
    setSelectedDistrict(camera.district);
    setSelectedStreet(camera.street);
    setSelectedCamera(camera.camera_id);
  }, []);

  useEffect(() => {
    let active = true;
    setLoading(true);
    Promise.all([
      apiGet<Camera[]>("/cameras"),
      apiGet<{ regions: string[] }>("/regions"),
      apiGet<{ alerts: Alert[] }>("/alerts?limit=15"),
      apiGet<InferenceStatus>("/inference/status"),
    ])
      .then(([cameraList, regionData, alertData, inferenceData]) => {
        if (!active) return;
        setCameras(cameraList);
        setRegions(regionData.regions);
        setRecentAlerts(alertData.alerts);
        setInference(inferenceData);
        if (cameraList.length) selectCamera(cameraList[0]);
        setApiError("");
      })
      .catch((error: Error) => {
        if (active) setApiError(error.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [selectCamera]);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => {
      apiGet<InferenceStatus>("/inference/status")
        .then(setInference)
        .catch(() => undefined);
    }, 15000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!selectedRegion) {
      setCities([]);
      return;
    }
    apiGet<{ cities: string[] }>(`/cities?region=${encodeURIComponent(selectedRegion)}`)
      .then((data) => setCities(data.cities))
      .catch((error: Error) => setApiError(error.message));
  }, [selectedRegion]);

  useEffect(() => {
    if (!selectedRegion || !selectedCity) {
      setDistricts([]);
      return;
    }
    const params = new URLSearchParams({ region: selectedRegion, city: selectedCity });
    apiGet<{ districts: string[] }>(`/districts?${params}`)
      .then((data) => setDistricts(data.districts))
      .catch((error: Error) => setApiError(error.message));
  }, [selectedRegion, selectedCity]);

  useEffect(() => {
    if (!selectedRegion || !selectedCity || !selectedDistrict) {
      setStreets([]);
      return;
    }
    const params = new URLSearchParams({
      region: selectedRegion,
      city: selectedCity,
      district: selectedDistrict,
    });
    apiGet<{ streets: string[] }>(`/streets?${params}`)
      .then((data) => setStreets(data.streets))
      .catch((error: Error) => setApiError(error.message));
  }, [selectedRegion, selectedCity, selectedDistrict]);

  useEffect(() => {
    if (!selectedRegion || !selectedCity || !selectedDistrict || !selectedStreet) {
      setCameraOptions([]);
      return;
    }
    const params = new URLSearchParams({
      region: selectedRegion,
      city: selectedCity,
      district: selectedDistrict,
      street: selectedStreet,
    });
    apiGet<{ cameras: CameraOption[] }>(`/camera-options?${params}`)
      .then((data) => {
        setCameraOptions(data.cameras);
        setSelectedCamera((current) => {
          if (data.cameras.length === 0) return "";
          if (data.cameras.some((item) => item.camera_id === current)) return current;
          return data.cameras[0].camera_id;
        });
      })
      .catch((error: Error) => setApiError(error.message));
  }, [selectedRegion, selectedCity, selectedDistrict, selectedStreet]);

  useEffect(() => {
    if (!selectedCamera) return;
    apiGet<{ source?: string }>(`/camera-source/${selectedCamera}`)
      .then((data) => setVideoSource(data.source ?? ""))
      .catch(() => setVideoSource(""));
  }, [selectedCamera, liveFrame?.frame_number]);

  useEffect(() => {
    if (!selectedCamera) return;

    let ws: WebSocket | null = null;
    let reconnectTimer = 0;
    let closedByUser = false;

    const connect = () => {
      ws = new WebSocket(`${wsBaseUrl()}/live-feed/${selectedCamera}`);
      ws.onopen = () => {
        setConnected(true);
        reconnectDelay.current = 1000;
        setApiError("");
      };
      ws.onclose = () => {
        setConnected(false);
        if (!closedByUser) {
          reconnectTimer = window.setTimeout(connect, reconnectDelay.current);
          reconnectDelay.current = Math.min(reconnectDelay.current * 2, 10000);
        }
      };
      ws.onerror = () => setConnected(false);
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        const frame: FrameResponse = message.data;
        setLiveFrame(frame);
        if (frame.active_alerts.length) {
          setRecentAlerts((prev) => {
            const merged = [...frame.active_alerts, ...prev];
            const unique = new Map(merged.map((alert) => [alert.alert_id, alert]));
            return Array.from(unique.values()).slice(0, 20);
          });
        }
      };
    };

    connect();
    return () => {
      closedByUser = true;
      window.clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, [selectedCamera]);

  useEffect(() => {
    if (!selectedCamera) {
      setGoogleAddress("");
      return;
    }
    apiGet<{ formatted_address?: string }>(`/cameras/${selectedCamera}/google-address`)
      .then((data) => setGoogleAddress(data.formatted_address ?? ""))
      .catch(() => setGoogleAddress(""));
  }, [selectedCamera]);

  const activeCamera = useMemo(
    () => cameras.find((camera) => camera.camera_id === selectedCamera),
    [cameras, selectedCamera],
  );

  const stats = liveFrame?.statistics;
  const zoneCounts = liveFrame?.zone_counts;
  const totalPeople = stats?.total_count ?? 0;
  const frameWidth = liveFrame?.frame_width ?? 1280;
  const frameHeight = liveFrame?.frame_height ?? 720;
  const snapshotSrc = selectedCamera
    ? `${API}/snapshot/${selectedCamera}?t=${liveFrame?.frame_number ?? 0}`
    : "";

  const genderPie = useMemo(
    () =>
      Object.entries(stats?.by_gender ?? { aniqlanmadi: 0 }).map(([name, value]) => ({
        name,
        value,
      })),
    [stats],
  );

  const agePie = useMemo(
    () => [
      { name: "Yosh bola", value: 0 },
      { name: "O'smir", value: 0 },
      { name: "Katta", value: totalPeople },
      { name: "Qariya", value: 0 },
    ],
    [totalPeople],
  );

  const statusRows = useMemo(
    () => [
      { label: "Sog'lom", value: totalPeople, tone: "green" },
      { label: "Nogiron", value: 0, tone: "purple" },
      { label: "Boshqa", value: stats?.violation_count ?? 0, tone: "yellow" },
    ],
    [stats, totalPeople],
  );

  const analyticsLines = useMemo(
    () =>
      (stats?.hourly_flow ?? Array(24).fill(0)).map((count, hour) => ({
        hour: `${hour}`,
        jami: count,
        chap: Math.round((zoneCounts?.left_side ?? 0) * (count / Math.max(totalPeople, 1))),
        ong: Math.round((zoneCounts?.right_side ?? 0) * (count / Math.max(totalPeople, 1))),
      })),
    [stats, zoneCounts, totalPeople],
  );

  function percent(part: number) {
    if (!totalPeople) return "0%";
    return `${((part / totalPeople) * 100).toFixed(1)}%`;
  }

  function bboxTone(gender?: string) {
    if (gender === "ayol") return "pink";
    if (gender === "erkak") return "cyan";
    return "green";
  }

  const categoryCards = [
    { label: "Yosh bola", value: 0, icon: "👶", tone: "green" },
    { label: "O'smir", value: 0, icon: "🧒", tone: "blue" },
    { label: "Qariya", value: 0, icon: "🧓", tone: "yellow" },
    { label: "Nogiron", value: 0, icon: "♿", tone: "purple" },
    { label: "Ayol", value: stats?.by_gender?.ayol ?? 0, icon: "👩", tone: "pink" },
    { label: "Erkak", value: stats?.by_gender?.erkak ?? 0, icon: "👨", tone: "cyan" },
  ];

  const clockText = now.toLocaleTimeString("uz-UZ", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  return (
    <div className="sveta-dashboard">
      <div className="sveta-symbols-strip">
        <UzbekistanBanner className="uz-banner-img header-banner" height={72} />
      </div>

      <header className="sveta-top">
        <div className="sveta-brand">
          <UzbekistanEmblem className="uz-emblem-img" size={64} />
          <div>
            <h1>O&apos;ZBEKISTON RESPUBLIKASI</h1>
          </div>
        </div>
        <div className="sveta-categories">
          {categoryCards.map((item) => (
            <div key={item.label} className={`sveta-cat-card ${item.tone}`}>
              <div className="icon">{item.icon}</div>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </div>
          ))}
        </div>
        <div className="sveta-total-box">
          <div className="sveta-total-head">
            <UzbekistanFlag className="uz-flag-img" width={58} height={38} side="right" />
            <div>
              <span>JAMI ODAMLAR SONI</span>
              <strong>{stats?.total_count ?? 0}</strong>
            </div>
          </div>
          <span className="sveta-clock">REAL VAQT {clockText}</span>
          <a className="sveta-admin-link" href="/admin/login">
            Admin panel →
          </a>
        </div>
      </header>

      {apiError && <div className="sveta-error">{apiError}</div>}

      <div className="sveta-body">
        <aside className="sveta-panel">
          <h3>Tizim ishi</h3>
          <div className="sveta-menu">
            {[
              "Real vaqtda monitoring",
              "AI aniqlash texnologiyasi",
              "To'liq sanash",
              "Yo'nalish bo'yicha sanash",
              "Ma'lumotlarni saqlash",
              "Statistika va hisobot",
            ].map((item) => (
              <div key={item} className="sveta-menu-item">
                <span>◉</span> {item}
              </div>
            ))}
          </div>

          <h3>Yo&apos;nalish bo&apos;yicha sanash</h3>
          <div className="sveta-stat-row">
            <span>Chapdan o&apos;ngga</span>
            <strong>{stats?.by_direction?.["chapdan"] ?? 0}</strong>
          </div>
          <div className="sveta-stat-row">
            <span>O&apos;ngdan chapga</span>
            <strong>{stats?.by_direction?.["o'ngdan"] ?? 0}</strong>
          </div>

          <h3>Yo&apos;lning har ikki tomoni</h3>
          <div className="sveta-stat-row">
            <span>Tomon A (chap)</span>
            <strong>{zoneCounts?.left_side ?? 0}</strong>
          </div>
          <div className="sveta-stat-row">
            <span>Tomon B (o&apos;ng)</span>
            <strong>{zoneCounts?.right_side ?? 0}</strong>
          </div>
          <div className="sveta-stat-row">
            <span>Peshaxot</span>
            <strong>{zoneCounts?.crosswalk ?? 0}</strong>
          </div>

          <h3>Qo&apos;shimcha imkoniyatlar</h3>
          <div className="sveta-menu">
            {["Yozuvlarni saqlash", "Hisobot yuklab olish", "Ogohlantirish tizimi"].map((item) => (
              <div key={item} className="sveta-menu-item">
                <span>◉</span> {item}
              </div>
            ))}
          </div>

          <h3>Kamera tanlash</h3>
          <div className="sveta-filter-grid">
            <label>
              Viloyat
              <select value={selectedRegion} onChange={(e) => { setSelectedRegion(e.target.value); setSelectedCity(""); setSelectedDistrict(""); setSelectedStreet(""); setSelectedCamera(""); }}>
                <option value="">Tanlang</option>
                {regions.map((region) => <option key={region} value={region}>{region}</option>)}
              </select>
            </label>
            <label>
              Shahar
              <select value={selectedCity} disabled={!selectedRegion} onChange={(e) => { setSelectedCity(e.target.value); setSelectedDistrict(""); setSelectedStreet(""); setSelectedCamera(""); }}>
                <option value="">Tanlang</option>
                {cities.map((city) => <option key={city} value={city}>{city}</option>)}
              </select>
            </label>
            <label>
              Tuman
              <select value={selectedDistrict} disabled={!selectedCity} onChange={(e) => { setSelectedDistrict(e.target.value); setSelectedStreet(""); setSelectedCamera(""); }}>
                <option value="">Tanlang</option>
                {districts.map((district) => <option key={district} value={district}>{district}</option>)}
              </select>
            </label>
            <label>
              Ko&apos;cha
              <select value={selectedStreet} disabled={!selectedDistrict} onChange={(e) => { setSelectedStreet(e.target.value); setSelectedCamera(""); }}>
                <option value="">Tanlang</option>
                {streets.map((street) => <option key={street} value={street}>{street}</option>)}
              </select>
            </label>
            <label>
              Kamera
              <select value={selectedCamera} disabled={!selectedStreet} onChange={(e) => setSelectedCamera(e.target.value)}>
                <option value="">Tanlang</option>
                {cameraOptions.map((camera) => <option key={camera.camera_id} value={camera.camera_id}>{camera.label}</option>)}
              </select>
            </label>
          </div>
        </aside>

        <main className="sveta-center">
          {snapshotSrc ? (
            <img src={snapshotSrc} alt="Live kamera" />
          ) : (
            <div className="camera-empty">{loading ? "Tizim yuklanmoqda..." : "Kamera yuklanmoqda..."}</div>
          )}
          <div className="sveta-overlay">
            {(liveFrame?.detected_persons ?? []).map((person) => (
              <div
                key={person.person_id}
                className={`sveta-bbox ${person.in_crosswalk ? "crosswalk" : ""} ${bboxTone(person.gender)}`}
                style={{
                  left: `${(person.bbox[0] / frameWidth) * 100}%`,
                  top: `${(person.bbox[1] / frameHeight) * 100}%`,
                  width: `${((person.bbox[2] - person.bbox[0]) / frameWidth) * 100}%`,
                  height: `${((person.bbox[3] - person.bbox[1]) / frameHeight) * 100}%`,
                }}
              >
                <span className="sveta-bbox-label">
                  {person.person_id} · {person.category} · {person.speed_ms} m/s
                </span>
              </div>
            ))}
          </div>
          <div className="sveta-center-hud">
            <span>{googleAddress || cameraFullAddress(activeCamera)}</span>
            <span>{connected ? "● LIVE" : "○ Ulanmoqda"} · {videoSource || "kamera"} · Kadr {liveFrame?.frame_number ?? 0}</span>
          </div>
        </main>

        <aside className="sveta-panel">
          <h3>Real vaqtda analitika</h3>
          <ResponsiveContainer width="100%" height={130}>
            <LineChart data={analyticsLines}>
              <CartesianGrid stroke="#1e3a5f" strokeDasharray="3 3" />
              <XAxis dataKey="hour" tick={{ fill: "#94a3b8", fontSize: 9 }} interval={4} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 9 }} width={24} />
              <Tooltip />
              <Line type="monotone" dataKey="jami" stroke="#22d3ee" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="chap" stroke="#4ade80" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="ong" stroke="#f472b6" strokeWidth={1.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>

          <h3>Yosh bo&apos;yicha taqsimot</h3>
          <ResponsiveContainer width="100%" height={110}>
            <PieChart>
              <Pie data={agePie} dataKey="value" nameKey="name" innerRadius={28} outerRadius={48}>
                {agePie.map((_, index) => (
                  <Cell key={index} fill={["#4ade80", "#38bdf8", "#facc15", "#c084fc"][index % 4]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="sveta-pie-legend">
            {agePie.map((item) => (
              <div key={item.name}><span>{item.name}</span><strong>{item.value}</strong></div>
            ))}
          </div>

          <h3>Jins bo&apos;yicha taqsimot</h3>
          <ResponsiveContainer width="100%" height={110}>
            <PieChart>
              <Pie data={genderPie} dataKey="value" nameKey="name" innerRadius={28} outerRadius={48}>
                {genderPie.map((_, index) => (
                  <Cell key={index} fill={["#f472b6", "#38bdf8", "#94a3b8"][index % 3]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="sveta-pie-legend">
            {genderPie.map((item) => (
              <div key={item.name}>
                <span>{item.name}</span>
                <strong>{item.value} · {percent(item.value)}</strong>
              </div>
            ))}
          </div>
          <div className="sveta-progress-list">
            {genderPie.map((item, index) => (
              <div key={item.name} className="sveta-progress-row">
                <span>{item.name}</span>
                <div className="sveta-progress-track">
                  <div
                    className={`sveta-progress-fill tone-${index}`}
                    style={{ width: totalPeople ? `${(item.value / totalPeople) * 100}%` : "0%" }}
                  />
                </div>
              </div>
            ))}
          </div>

          <h3>Holat bo&apos;yicha taqsimot</h3>
          <div className="sveta-status-list">
            {statusRows.map((row) => (
              <div key={row.label} className={`sveta-status-row ${row.tone}`}>
                <span>{row.label}</span>
                <strong>{row.value} · {percent(row.value)}</strong>
              </div>
            ))}
          </div>

          <h3>Ogohlantirishlar</h3>
          <div className="alerts-list">
            {recentAlerts.slice(0, 4).map((alert) => (
              <div key={alert.alert_id} className={`alert-item ${severityClass(alert.severity)}`}>
                <div className="alert-head"><strong>{alert.alert_type}</strong><span>{alert.severity}</span></div>
                <p>{alert.description}</p>
                {alertLocationText(alert.location) && <p className="alert-location">{alertLocationText(alert.location)}</p>}
              </div>
            ))}
          </div>
        </aside>
      </div>

      <footer className="sveta-footer">
        <div className="sveta-footer-icons">
          <span>✓ Aniq sanash</span>
          <span>✓ Yuz tanish (ixtiyoriy)</span>
          <span>✓ Ma&apos;lumot xavfsizligi</span>
          <span>✓ Cloud saqlash</span>
          <span>✓ Ko&apos;p kamera</span>
          <span>✓ Qurilma mosligi</span>
        </div>
        <div className="sveta-footer-slogan">HAR BIR ODAM MUHIM – HAR BIR SON ANIQ</div>
      </footer>
    </div>
  );
}
