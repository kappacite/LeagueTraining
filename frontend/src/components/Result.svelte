<script>
  import { GRADE_LABELS } from "../lib/dd.js";
  import Avatar from "./Avatar.svelte";
  import Burst from "./Burst.svelte";
  import ItemIcons from "./ItemIcons.svelte";

  let { result, chosen } = $props();
  const pickedBy = (id) => result.distribution.filter((d) => d.choice_id === id);
</script>

<section class="result {result.grade}" aria-live="polite">
  <header class="verdict">
    {#if result.grade === "excellent"}<Burst />{/if}
    <span class="seal" aria-hidden="true"></span>
    <h2>{result.timed_out ? "Temps écoulé" : GRADE_LABELS[result.grade]}</h2>
    {#if result.scored}
      <p class="num points">+{result.points}<small> pts</small></p>
    {:else}
      <p class="muted">Entraînement, sans points</p>
    {/if}
  </header>

  <p class="lesson">{result.lesson}</p>

  <ol class="choices">
    {#each result.choices as c}
      <li class="panel" class:chosen={c.id === chosen}>
        <div class="head">
          <span class="tag grade-{c.grade}"><span class="gem"></span>{GRADE_LABELS[c.grade]}</span>
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
  .verdict { position: relative; display: flex; align-items: center; gap: 1rem; padding: 0.5rem 0 1rem; }
  .seal { width: 18px; height: 18px; transform: rotate(45deg); flex: none; }
  h2 { font-size: 2.4rem; margin: 0; letter-spacing: 0.08em; }
  .points { font-size: 1.8rem; margin: 0 0 0 auto; color: var(--lol-gold-bright); }
  .points small { font-size: 0.9rem; color: var(--lol-text-secondary); }

  .excellent h2 { background: linear-gradient(180deg, var(--lol-gold-bright), var(--lol-gold)); -webkit-background-clip: text; background-clip: text; color: transparent; text-shadow: none; }
  .excellent .seal { background: var(--lol-gold); box-shadow: 0 0 14px var(--lol-gold), 0 0 28px rgba(11, 196, 226, 0.6); }
  .correct h2 { color: var(--lol-blue); }
  .correct .seal { background: var(--lol-blue); box-shadow: 0 0 12px var(--lol-blue); }
  .erreur h2 { color: var(--lol-danger); }
  .erreur .seal { background: #5e1a1a; border: 1px solid var(--lol-danger); }
  /* Failure: a contained dark-red fall, no flash. */
  .erreur .verdict { animation: sink 500ms var(--ease) both; }
  @keyframes sink { from { opacity: 0; transform: translateY(-6px); filter: brightness(1.6); } to { opacity: 1; transform: none; filter: none; } }
  .excellent .verdict, .correct .verdict { animation: rise 450ms var(--ease) both; }

  .lesson {
    font: 600 1.1rem/1.5 var(--font-body); color: var(--lol-gold-bright);
    border-left: 2px solid var(--lol-gold); padding: 0.25rem 0 0.25rem 1rem; margin: 0 0 1.5rem;
    background: linear-gradient(90deg, rgba(200, 170, 110, 0.08), transparent 60%);
  }
  .choices { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.7rem; }
  li.panel { padding: 0.9rem 1.1rem; }
  li.chosen { border-image: var(--metal) 1; box-shadow: 0 0 0 1px rgba(11, 196, 226, 0.35), 0 10px 28px rgba(0, 0, 0, 0.5); }
  .head { display: flex; align-items: center; gap: 0.7rem; flex-wrap: wrap; margin-bottom: 0.4rem; }
  .head strong { color: var(--lol-gold-bright); flex: 1; min-width: 12rem; }
  .tag { display: inline-flex; align-items: center; gap: 0.4rem; min-width: 6.5rem; font: 700 0.72rem var(--font-body); letter-spacing: 0.14em; text-transform: uppercase; }
  .gem { width: 7px; height: 7px; transform: rotate(45deg); background: currentColor; box-shadow: 0 0 6px currentColor; }
  .who { display: flex; gap: 3px; margin-left: auto; }
  li p { margin: 0; color: var(--lol-text-secondary); }
</style>
