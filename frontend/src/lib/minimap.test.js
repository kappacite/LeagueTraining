import { expect, test } from "vitest";
import { toSvg, remaining } from "./minimap.js";

test("maps 0-100 coordinates onto the svg", () => {
  expect(toSvg(50, 50, 400)).toEqual({ cx: 200, cy: 200 });
  expect(toSvg(0, 100, 400)).toEqual({ cx: 0, cy: 400 });
});

test("clamps out-of-range coordinates", () => {
  expect(toSvg(120, -5, 400)).toEqual({ cx: 400, cy: 0 });
});

test("remaining seconds come from the server start time, never negative", () => {
  const start = "2026-11-16T12:00:00+00:00";
  expect(remaining(start, 20, Date.parse("2026-11-16T12:00:05Z"))).toBe(15);
  expect(remaining(start, 20, Date.parse("2026-11-16T12:00:30Z"))).toBe(0);
});
