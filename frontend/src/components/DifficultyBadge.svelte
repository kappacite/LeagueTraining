<script>
  import { DIFFICULTY_LABELS } from "../lib/dd.js";
  let { difficulty } = $props();
  const level = $derived({ facile: 1, moyen: 2, difficile: 3 }[difficulty]);
</script>

<span class="badge {difficulty}" title="Difficulté : {DIFFICULTY_LABELS[difficulty]}">
  <span class="gems" aria-hidden="true">
    {#each [1, 2, 3] as i}<span class="gem" class:on={i <= level}></span>{/each}
  </span>
  {DIFFICULTY_LABELS[difficulty]}
</span>

<style>
  .badge {
    display: inline-flex; align-items: center; gap: 0.45rem;
    font: 700 0.72rem var(--font-body); letter-spacing: 0.12em; text-transform: uppercase;
    color: var(--lol-text-secondary);
  }
  .gems { display: inline-flex; gap: 3px; }
  .gem { width: 7px; height: 7px; transform: rotate(45deg); border: 1px solid var(--lol-gold-deep); background: transparent; }
  .facile .gem.on { background: var(--lol-blue); border-color: var(--lol-blue); box-shadow: 0 0 6px rgba(10, 200, 185, 0.6); }
  .moyen .gem.on { background: var(--lol-gold); border-color: var(--lol-gold); box-shadow: 0 0 6px rgba(200, 170, 110, 0.5); }
  .difficile .gem.on { background: var(--lol-danger); border-color: #e06a6a; box-shadow: 0 0 6px rgba(196, 63, 63, 0.6); }
  .facile { color: var(--lol-blue); }
  .moyen { color: var(--lol-gold); }
  .difficile { color: #d86a6a; }
</style>
