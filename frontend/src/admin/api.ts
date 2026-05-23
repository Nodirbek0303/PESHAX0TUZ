const API = import.meta.env.VITE_API_URL ?? "/api/v1";

const TOKEN_KEY = "smartcross_admin_token";



function authHeaders(): HeadersInit {

  return {

    Authorization: `Bearer ${getAdminToken() ?? ""}`,

    "Content-Type": "application/json",

  };

}



async function parseAdminResponse<T>(response: Response): Promise<T> {

  if (response.status === 401) {

    clearAdminToken();

    throw new Error("Sessiya tugadi");

  }

  if (!response.ok) {

    const body = await response.json().catch(() => ({}));

    const detail = typeof body.detail === "string" ? body.detail : `API xato: ${response.status}`;

    throw new Error(detail);

  }

  return response.json() as Promise<T>;

}



export function getAdminToken(): string | null {

  return sessionStorage.getItem(TOKEN_KEY);

}



export function setAdminToken(token: string): void {

  sessionStorage.setItem(TOKEN_KEY, token);

}



export function clearAdminToken(): void {

  sessionStorage.removeItem(TOKEN_KEY);

}



export class AdminApiError extends Error {
  readonly code: "network" | "unauthorized" | "server";

  constructor(message: string, code: "network" | "unauthorized" | "server") {
    super(message);
    this.name = "AdminApiError";
    this.code = code;
  }
}

export async function adminLogin(password: string): Promise<{ token: string }> {
  let response: Response;
  try {
    response = await fetch(`${API}/admin/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });
  } catch {
    throw new AdminApiError(
      "Backend serverga ulanib bo'lmadi. API server ishlamayapti yoki VITE_API_URL noto'g'ri.",
      "network",
    );
  }

  if (response.status === 401) {
    throw new AdminApiError("Parol noto'g'ri. Qayta urinib ko'ring.", "unauthorized");
  }

  if (response.status === 404) {
    throw new AdminApiError(
      "Backend topilmadi (404). Vercel faqat frontend — backend alohida deploy qiling.",
      "network",
    );
  }

  if (response.status === 501 || response.status === 502 || response.status === 503) {
    throw new AdminApiError(
      "Backend vaqtincha ishlamayapti. Server yoki tunnel o'chgan bo'lishi mumkin.",
      "network",
    );
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : `Server xato: ${response.status}`;
    throw new AdminApiError(detail, "server");
  }

  return response.json();
}



export async function adminFetch<T>(path: string): Promise<T> {

  const response = await fetch(`${API}${path}`, {

    headers: { Authorization: `Bearer ${getAdminToken() ?? ""}` },

  });

  return parseAdminResponse<T>(response);

}



export async function adminPost<T>(path: string, body: unknown): Promise<T> {

  const response = await fetch(`${API}${path}`, {

    method: "POST",

    headers: authHeaders(),

    body: JSON.stringify(body),

  });

  return parseAdminResponse<T>(response);

}



export async function adminPut<T>(path: string, body: unknown): Promise<T> {

  const response = await fetch(`${API}${path}`, {

    method: "PUT",

    headers: authHeaders(),

    body: JSON.stringify(body),

  });

  return parseAdminResponse<T>(response);

}



export async function adminPatch<T>(path: string, body: unknown): Promise<T> {

  const response = await fetch(`${API}${path}`, {

    method: "PATCH",

    headers: authHeaders(),

    body: JSON.stringify(body),

  });

  return parseAdminResponse<T>(response);

}



export async function adminDelete<T>(path: string): Promise<T> {

  const response = await fetch(`${API}${path}`, {

    method: "DELETE",

    headers: authHeaders(),

  });

  return parseAdminResponse<T>(response);

}



export async function publicGet<T>(path: string): Promise<T> {

  const response = await fetch(`${API}${path}`);

  if (!response.ok) {

    throw new Error(`API xato: ${response.status}`);

  }

  return response.json() as Promise<T>;

}


