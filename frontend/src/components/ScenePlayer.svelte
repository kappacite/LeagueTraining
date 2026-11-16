<script>
  // Plays one timeline on the minimap. Remount (with {#key}) to play another clip.
  import { onDestroy, onMount } from "svelte";
  import { duration, stateAt } from "../lib/timeline.js";
  import Minimap from "./Minimap.svelte";

  let { base, clip, autoplay = true, onend } = $props();

  const total = duration(clip);
  let t = $state(0);
  let playing = $state(false);
  let ended = false;
  let raf;
  let last = null;

  function finish() {
    t = total;
    playing = false;
    cancelAnimationFrame(raf);
    if (!ended) {
      ended = true;
      onend?.();
    }
  }

  function tick(now) {
    if (last !== null) t = Math.min(total, t + (now - last) / 1000);
    last = now;
    if (t >= total) return finish();
    raf = requestAnimationFrame(tick);
  }

  function play() {
    if (t >= total) t = 0;
    playing = true;
    last = null;
    raf = requestAnimationFrame(tick);
  }

  function pause() {
    playing = false;
    cancelAnimationFrame(raf);
  }

  function replay() {
    pause();
    t = 0;
    play();
  }

  onMount(() => {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches || total === 0) finish();
    else if (autoplay) play();
  });
  onDestroy(() => cancelAnimationFrame(raf));

  const state = $derived(stateAt(base, clip, t));
  const scene = $derived({
    champions: Object.values(state.champions).filter((c) => c.x != null),
    wards: Object.values(state.wards),
    objectives: state.objectives,
    events: state.events,
  });
</script>

<div class="player">
  <div class="screen">
    {#if state.clock}<span class="clock num">{state.clock}</span>{/if}
    <Minimap {scene} />
  </div>
  <p class="caption" aria-live="polite">{state.caption}</p>
  <div class="controls">
    {#if playing}
      <button class="quiet" onclick={pause} aria-label="Pause">Pause</button>
    {:else}
      <button class="quiet" onclick={play} aria-label="Lecture">{t >= total ? "Revoir" : "Lecture"}</button>
    {/if}
    <button class="quiet" onclick={replay}>Depuis le début</button>
    {#if t < total}<button class="quiet" onclick={finish}>Passer</button>{/if}
    <span class="track"><span style:width="{total ? (t / total) * 100 : 100}%"></span></span>
  </div>
</div>

<style>
  .player { display: grid; gap: 0.6rem; }
  .screen { position: relative; }
  .clock {
    position: absolute; top: 10px; left: 50%; transform: translateX(-50%); z-index: 1;
    padding: 0.2rem 0.9rem; font-size: 1rem; color: var(--lol-gold-bright);
    background: rgba(1, 10, 19, 0.85); border: 1px solid var(--lol-gold-dark);
  }
  .caption {
    min-height: 3em; margin: 0.3rem 0 0; font-size: 1.05rem; color: var(--lol-gold-bright);
    border-left: 2px solid var(--lol-hextech); padding-left: 0.75rem;
  }
  .controls { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
  .controls button { padding: 0.55em 0.9em; font-size: 0.7rem; }
  .track { flex: 1; min-width: 4rem; height: 3px; background: var(--lol-black); border: 1px solid var(--lol-gold-deep); }
  .track span { display: block; height: 100%; background: var(--lol-hextech); box-shadow: 0 0 6px var(--lol-hextech); }
</style>
