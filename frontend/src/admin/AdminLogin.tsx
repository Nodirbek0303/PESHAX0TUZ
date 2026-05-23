import { ChangeEvent, FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import UzbekistanEmblem from "../components/UzbekistanEmblem";
import UzbekistanBanner from "../components/UzbekistanBanner";
import { adminLogin, setAdminToken } from "./api";
import "./admin.css";

export default function AdminLogin() {
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await adminLogin(password);
      setAdminToken(data.token);
      navigate("/admin");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Kutilmagan xato yuz berdi.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="admin-login-page">
      <div className="admin-login-card">
        <UzbekistanBanner className="uz-banner-img login-banner" height={110} />
        <UzbekistanEmblem className="uz-emblem-img login-emblem" size={88} />
        <h1>BUTUN RESPUBLIKA – INTELLEKTUAL NAZORAT TIZIMI</h1>
        <p className="admin-login-sub">Admin panel — faqat vakolatli xodimlar uchun</p>
        <form onSubmit={onSubmit}>
          <label>
            Parol
            <input
              type="password"
              value={password}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
              placeholder="Admin parolini kiriting"
              autoFocus
            />
          </label>
          {error && <p className="admin-login-error">{error}</p>}
          <button type="submit" disabled={loading || !password}>
            {loading ? "Tekshirilmoqda..." : "Kirish"}
          </button>
        </form>
        <a className="admin-login-back" href="/">
          ← Operator dashboard
        </a>
      </div>
    </div>
  );
}
