import { describe, expect, test } from "vitest";
import { parse, href } from "./router.js";

describe("parse", () => {
  test.each([
    ["", { page: "home", params: {}, query: {} }],
    ["#/", { page: "home", params: {}, query: {} }],
    ["#/puzzles", { page: "list", params: {}, query: {} }],
    ["#/puzzles?role=mid&difficulty=facile", { page: "list", params: {}, query: { role: "mid", difficulty: "facile" } }],
    ["#/puzzle/mid-drake-01", { page: "puzzle", params: { id: "mid-drake-01" }, query: {} }],
    ["#/leaderboard", { page: "leaderboard", params: {}, query: {} }],
    ["#/user/3", { page: "profile", params: { id: "3" }, query: {} }],
    ["#/login?error=not-allowed", { page: "login", params: {}, query: { error: "not-allowed" } }],
    ["#/nowhere/at/all", { page: "home", params: {}, query: {} }],
  ])("%s", (hash, expected) => {
    expect(parse(hash)).toEqual(expected);
  });

  test("decodes ids", () => {
    expect(parse("#/puzzle/a%20b").params.id).toBe("a b");
  });
});

test("href builds hash links with query", () => {
  expect(href("list", {}, { role: "mid" })).toBe("#/puzzles?role=mid");
  expect(href("puzzle", { id: "x" })).toBe("#/puzzle/x");
});
