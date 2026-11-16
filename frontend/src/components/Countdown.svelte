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
  <span class="num value">{left}</span>
  <div class="track"><div class="fill" style:width="{(left / limit) * 100}%"></div></div>
</div>

<style>
  .countdown { display: flex; align-items: center; gap: 1rem; margin: 0.5rem 0 1rem; }
  .value {
    display: grid; place-items: center; width: 3.4rem; height: 3.4rem; flex: none;
    font-size: 1.6rem; color: var(--lol-gold-bright);
    border: 2px solid transparent; border-image: var(--metal) 1;
    background: radial-gradient(circle, #13203a, var(--lol-black));
    box-shadow: 0 0 14px rgba(200, 170, 110, 0.2);
  }
  .track { flex: 1; height: 6px; background: var(--lol-black); border: 1px solid var(--lol-gold-deep); }
  .fill {
    height: 100%; transition: width 0.25s linear;
    background: linear-gradient(90deg, var(--lol-gold-dark), var(--lol-gold-hover));
    box-shadow: 0 0 10px rgba(200, 170, 110, 0.6);
  }
  .urgent .value { color: #e07a7a; border-image: linear-gradient(180deg, #e07a7a, var(--lol-danger), #5e1a1a) 1; box-shadow: 0 0 16px rgba(196, 63, 63, 0.45); }
  .urgent .fill { background: linear-gradient(90deg, #5e1a1a, var(--lol-danger)); box-shadow: 0 0 10px rgba(196, 63, 63, 0.7); }
</style>
