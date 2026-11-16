// The only module that talks to the server: errors and logouts are handled here, once.
import { user } from "./stores.js";

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

export async function request(method, path, body) {
  const res = await fetch(path, {
    method,
    credentials: "same-origin",
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (res.status === 401) user.set(null);
  if (!res.ok) throw new ApiError(res.status, data?.detail ?? res.statusText);
  return data;
}

const enc = encodeURIComponent;

export const api = {
  me: () => request("GET", "/api/me"),
  logout: () => request("POST", "/api/auth/logout"),
  meta: () => request("GET", "/api/meta"),
  puzzles: (filters = {}) => {
    const qs = new URLSearchParams(Object.entries(filters).filter(([, v]) => v)).toString();
    return request("GET", `/api/puzzles${qs ? `?${qs}` : ""}`);
  },
  start: (id, mode) => request("POST", `/api/puzzles/${enc(id)}/start`, { mode }),
  answer: (id, choice) => request("POST", `/api/puzzles/${enc(id)}/answer`, { choice }),
  daily: () => request("GET", "/api/daily"),
  leaderboard: () => request("GET", "/api/leaderboard"),
  profile: (id) => request("GET", `/api/users/${enc(id)}`),
};
