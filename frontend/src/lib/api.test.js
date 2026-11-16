import { afterEach, expect, test, vi } from "vitest";
import { get } from "svelte/store";
import { api, ApiError } from "./api.js";
import { user } from "./stores.js";

afterEach(() => vi.unstubAllGlobals());

function stubFetch(status, body) {
  const fetch = vi.fn(async () => new Response(body === undefined ? null : JSON.stringify(body), { status }));
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

test("returns JSON on success", async () => {
  stubFetch(200, { id: 1, name: "Faker" });
  expect(await api.me()).toEqual({ id: 1, name: "Faker" });
});

test("401 logs the user out and rejects", async () => {
  user.set({ id: 1 });
  stubFetch(401, { detail: "not logged in" });
  await expect(api.me()).rejects.toMatchObject({ status: 401 });
  expect(get(user)).toBeNull();
});

test("other errors reject with ApiError carrying status and detail", async () => {
  stubFetch(409, { detail: "no open attempt" });
  const err = await api.answer("p", "a").catch((e) => e);
  expect(err).toBeInstanceOf(ApiError);
  expect([err.status, err.message]).toEqual([409, "no open attempt"]);
});

test("POST sends JSON body with same-origin credentials", async () => {
  const fetch = stubFetch(200, {});
  await api.start("mid drake", "chrono");
  const [url, opts] = fetch.mock.calls[0];
  expect(url).toBe("/api/puzzles/mid%20drake/start");
  expect(opts).toMatchObject({ method: "POST", credentials: "same-origin" });
  expect(JSON.parse(opts.body)).toEqual({ mode: "chrono" });
});

test("204 resolves to null", async () => {
  stubFetch(204);
  expect(await api.logout()).toBeNull();
});

test("puzzles() drops empty filters from the query", async () => {
  const fetch = stubFetch(200, []);
  await api.puzzles({ role: "mid", difficulty: "" });
  expect(fetch.mock.calls[0][0]).toBe("/api/puzzles?role=mid");
});
