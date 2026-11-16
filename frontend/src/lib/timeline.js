// Scene timelines: keyframes describe only what changes; positions are interpolated linearly,
// everything else (flags, clock, caption, wards, objectives) changes by steps.

const EVENT_LIFETIME = 1.5;
const PAUSE = 0.6;

export function initialState() {
  return { clock: "", caption: "", champions: {}, wards: {}, objectives: [], events: [] };
}

export function applyKeyframe(state, kf) {
  const champions = { ...state.champions };
  for (const c of kf.champions ?? []) champions[c.champion] = { ...champions[c.champion], ...c };
  const wards = { ...state.wards };
  for (const w of kf.wards ?? []) {
    if (w.removed) delete wards[w.id];
    else wards[w.id] = { ...wards[w.id], ...w };
  }
  return {
    clock: kf.clock ?? state.clock,
    caption: kf.caption ?? state.caption,
    champions,
    wards,
    objectives: kf.objectives ?? state.objectives,
    events: [],
  };
}

export const duration = (clip) => (clip.length ? clip[clip.length - 1].t : 0);

export function endState(base, clip) {
  return clip.reduce(applyKeyframe, base);
}

export function stateAt(base, clip, t) {
  const past = clip.filter((kf) => kf.t <= t);
  const state = past.reduce(applyKeyframe, base);
  state.events = past.flatMap((kf) => (t - kf.t < EVENT_LIFETIME ? kf.events ?? [] : []));

  // Glide each champion toward its next keyframed position.
  for (const [name, champ] of Object.entries(state.champions)) {
    const hasPos = (kf) => kf.champions?.some((c) => c.champion === name && c.x != null);
    const next = clip.find((kf) => kf.t > t && hasPos(kf));
    if (!next) continue;
    const prev = [...past].reverse().find(hasPos);
    const t0 = prev ? prev.t : 0;
    const target = next.champions.find((c) => c.champion === name);
    const k = (t - t0) / (next.t - t0);
    state.champions[name] = {
      ...champ,
      x: champ.x + ((target.x ?? champ.x) - champ.x) * k,
      y: champ.y + ((target.y ?? champ.y) - champ.y) * k,
    };
  }
  return state;
}

export function chain(clips) {
  const joined = [];
  const cuts = [];
  let offset = 0;
  for (const clip of clips) {
    cuts.push(offset);
    for (const kf of clip) joined.push({ ...kf, t: kf.t + offset });
    offset += duration(clip) + PAUSE;
  }
  return { clip: joined, cuts };
}
