<script>
  import { GRADE_LABELS } from "../lib/dd.js";
  import Avatar from "./Avatar.svelte";
  import ItemIcons from "./ItemIcons.svelte";

  let { result, chosen } = $props();
  const pickedBy = (id) => result.distribution.filter((d) => d.choice_id === id);
</script>

<section class="result" aria-live="polite">
  <header>
    <h2 class="grade-{result.grade}">{result.timed_out ? "Temps écoulé" : GRADE_LABELS[result.grade]}</h2>
    {#if result.scored}
      <p class="num points">+{result.points} pts</p>
    {:else}
      <p class="muted">Entraînement, sans points</p>
    {/if}
  </header>

  <p class="lesson">{result.lesson}</p>

  <ol class="choices">
    {#each result.choices as c}
      <li class:chosen={c.id === chosen}>
        <div class="head">
          <span class="tag grade-{c.grade}">{GRADE_LABELS[c.grade]}</span>
          <strong>{c.text}</strong>
          <ItemIcons items={c.items} size={24} />
          <span class="who">{#each pickedBy(c.id) as u}<Avatar user={u} size={24} />{/each}</span>
        </div>
        <p>{c.explanation}</p>
      </li>
    {/each}
  </ol>
</section>

<style>
  header { display: flex; align-items: baseline; gap: 1rem; }
  h2 { font-size: 2.6rem; margin: 0; }
  .points { font-size: 1.6rem; margin: 0; }
  .lesson { font-size: 1.15rem; border-left: 3px solid var(--excellent); padding-left: 0.9rem; margin: 1rem 0 1.5rem; }
  .choices { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.75rem; }
  li { padding: 0.9rem 1rem; background: var(--bank); border-radius: 6px; }
  li.chosen { box-shadow: inset 0 0 0 2px var(--foam); }
  .head { display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; margin-bottom: 0.35rem; }
  .tag { font: 700 0.95rem var(--display); min-width: 5.5rem; }
  .who { display: flex; gap: 2px; margin-left: auto; }
  li p { margin: 0; color: var(--mist); }
</style>
