import { readable } from "svelte/store";

// page name -> path pattern. ":id" captures one segment.
const ROUTES = {
  home: "",
  list: "puzzles",
  puzzle: "puzzle/:id",
  leaderboard: "leaderboard",
  profile: "user/:id",
  login: "login",
};

export function parse(hash) {
  const [path, qs = ""] = hash.replace(/^#\/?/, "").split("?");
  const query = Object.fromEntries(new URLSearchParams(qs));
  const parts = path.split("/").filter(Boolean);
  for (const [page, pattern] of Object.entries(ROUTES)) {
    const pat = pattern.split("/").filter(Boolean);
    if (pat.length !== parts.length) continue;
    const params = {};
    if (pat.every((p, i) => (p.startsWith(":") ? (params[p.slice(1)] = decodeURIComponent(parts[i])) : p === parts[i]))) {
      return { page, params, query };
    }
  }
  return { page: "home", params: {}, query: {} };
}

export function href(page, params = {}, query = {}) {
  const path = ROUTES[page].replace(/:(\w+)/g, (_, k) => encodeURIComponent(params[k]));
  const qs = new URLSearchParams(Object.entries(query).filter(([, v]) => v)).toString();
  return `#/${path}${qs ? `?${qs}` : ""}`;
}

export const route = readable(parse(globalThis.location?.hash ?? ""), (set) => {
  const update = () => set(parse(location.hash));
  addEventListener("hashchange", update);
  return () => removeEventListener("hashchange", update);
});
