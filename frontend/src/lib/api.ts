const BASE = process.env.NEXT_PUBLIC_API_BASE_URL!;

let accessToken: string | null = null;
export const setAccessToken = (t: string | null) => {
  accessToken = t;
};
const getRefresh = () =>
  typeof window !== "undefined" ? localStorage.getItem("faraday_refresh") : null;
export const setRefresh = (t: string | null) => {
  if (typeof window === "undefined") return;
  if (t) localStorage.setItem("faraday_refresh", t);
  else localStorage.removeItem("faraday_refresh");
};

async function rotate(): Promise<boolean> {
  const refreshToken = getRefresh();
  if (!refreshToken) return false;
  const res = await fetch(`${BASE}/api/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refreshToken }),
  });
  if (!res.ok) {
    setAccessToken(null);
    setRefresh(null);
    return false;
  }
  const data = await res.json();
  setAccessToken(data.accessToken);
  setRefresh(data.refreshToken); // rotation returns a NEW refresh token
  return true;
}

export async function api(
  path: string,
  init: RequestInit = {},
  retry = true,
): Promise<Response> {
  const headers = new Headers(init.headers);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (res.status === 401 && retry && (await rotate())) {
    return api(path, init, false);
  }
  return res;
}

// Convenience JSON POST that throws the server's ProblemDetail message on failure.
export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail || detail?.message || "Request failed");
  }
  return res.json();
}
