import { describe, expect, test } from "vitest";
import { applyKeyframe, chain, duration, endState, initialState, stateAt } from "./timeline.js";

const clip = [
  {
    t: 0, clock: "13:10", caption: "Début",
    champions: [{ champion: "Ahri", team: "ally", x: 10, y: 50, me: true }, { champion: "Zed", team: "enemy", x: 80, y: 20 }],
    wards: [{ id: "w1", team: "ally", x: 60, y: 60 }],
    objectives: [{ type: "dragon", spawn_in: 50 }],
  },
  { t: 2, caption: "Zed disparaît", champions: [{ champion: "Zed", hidden: true }], events: [{ type: "ping", x: 70, y: 30 }] },
  { t: 4, clock: "13:14", champions: [{ champion: "Ahri", x: 30, y: 50 }], wards: [{ id: "w1", removed: true }] },
];

describe("stateAt", () => {
  test("interpolates positions between keyframes", () => {
    const s = stateAt(initialState(), clip, 2);
    expect(s.champions.Ahri).toMatchObject({ x: 20, y: 50 });
  });

  test("a champion absent from a keyframe keeps its position", () => {
    expect(stateAt(initialState(), clip, 3).champions.Zed).toMatchObject({ x: 80, y: 20, hidden: true });
  });

  test("flags, clock and caption change by steps", () => {
    const s = stateAt(initialState(), clip, 1.9);
    expect(s.champions.Zed.hidden).toBeUndefined();
    expect([s.clock, s.caption]).toEqual(["13:10", "Début"]);
    expect(stateAt(initialState(), clip, 4).clock).toBe("13:14");
  });

  test("removed wards disappear", () => {
    expect(Object.keys(stateAt(initialState(), clip, 3.9).wards)).toEqual(["w1"]);
    expect(stateAt(initialState(), clip, 4).wards).toEqual({});
  });

  test("events show for 1.5 s after their keyframe", () => {
    expect(stateAt(initialState(), clip, 2.5).events).toHaveLength(1);
    expect(stateAt(initialState(), clip, 3.6).events).toHaveLength(0);
  });

  test("continues from a base state (next clip)", () => {
    const base = endState(initialState(), clip);
    const next = [{ t: 0 }, { t: 2, champions: [{ champion: "Ahri", x: 50 }] }];
    expect(stateAt(base, next, 1).champions.Ahri.x).toBe(40);
  });
});

test("applyKeyframe does not mutate its input", () => {
  const s = initialState();
  applyKeyframe(s, clip[0]);
  expect(s.champions).toEqual({});
});

test("duration is the last keyframe time", () => {
  expect(duration(clip)).toBe(4);
});

test("chain joins clips with a 0.6 s pause", () => {
  const a = [{ t: 0 }, { t: 4 }];
  const { clip: joined, cuts } = chain([a, a]);
  expect(duration(joined)).toBeCloseTo(8.6);
  expect(cuts).toEqual([0, 4.6]);
});
