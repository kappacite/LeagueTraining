<script>
  import { onDestroy } from "svelte";
  import { remaining } from "../lib/minimap.js";

  let { startedAt, limit, onexpire } = $props();
  let left = $state(remaining(startedAt, limit));
  const timer = setInterval(() => {
    left = remaining(startedAt, limit);
    if (left === 0) {
      clearInterval(timer);
      onexpire?.();
    }
  }, 250);
  onDestroy(() => clearInterval(timer));
</script>

<div class="countdown" class:urgent={left <= 5} role="timer" aria-live="off" aria-label="{left} secondes restantes">
  <span class="num">{left}</span><span class="unit">s</span>
  <div class="track"><div class="fill" style:width="{(left / limit) * 100}%"></div></div>
</div>

<style>
  .countdown { display: flex; align-items: baseline; gap: 0.2rem; flex-wrap: wrap; }
  .num { font-size: 2.6rem; line-height: 1; }
  .unit { color: var(--mist); margin-right: 0.75rem; }
  .track { flex: 1; min-width: 6rem; height: 4px; background: var(--reed); border-radius: 2px; align-self: center; }
  .fill { height: 100%; background: var(--foam); border-radius: 2px; transition: width 0.25s linear; }
  .urgent .num, .urgent .fill { color: var(--erreur); background-color: var(--erreur); }
  .urgent .num { background: none; }
</style>
