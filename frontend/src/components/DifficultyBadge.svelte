<script>
  import { DIFFICULTY_LABELS } from "../lib/dd.js";
  let { difficulty } = $props();
</script>

<span class="diff {difficulty}">{DIFFICULTY_LABELS[difficulty]}</span>

<style>
  .diff { font: 700 10px var(--font-body); letter-spacing: 0.085em; text-transform: uppercase; }
  .facile { color: #4cc8c7; }
  .moyen { color: #cfb47a; }
  .difficile { color: #d37a74; }
</style>
