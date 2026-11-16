const clamp = (v) => Math.min(100, Math.max(0, v));

// Puzzle coordinates: x 0-100 left to right, y 0-100 top to bottom (blue base bottom-left).
export function toSvg(x, y, size) {
  return { cx: (clamp(x) / 100) * size, cy: (clamp(y) / 100) * size };
}

// ponytail: uses the browser clock; the server decides the timeout anyway, a skewed clock only skews the display.
export function remaining(startedAt, limitSeconds, now = Date.now()) {
  const elapsed = (now - Date.parse(startedAt)) / 1000;
  return Math.max(0, Math.ceil(limitSeconds - elapsed));
}
