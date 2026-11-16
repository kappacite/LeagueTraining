<script>
  // End of a scene: your outcome vs the optimal one, replays, then every decision explained.
  import { GRADE_LABELS } from "../lib/dd.js";
  import { chain, initialState } from "../lib/timeline.js";
  import Avatar from "./Avatar.svelte";
  import Burst from "./Burst.svelte";
  import ScenePlayer from "./ScenePlayer.svelte";

  let { end, history } = $props();
  let replay = $state(null); // "mine" | "optimal" | null

  const LABELS = {
    drakes: ["drake", "drakes"], towers: ["tour", "tours"], gold: ["PO", "PO"], kills: ["kill", "kills"],
    barons: ["Baron", "Barons"], heralds: ["Héraut", "Hérauts"], grubs: ["larve", "larves"],
  };
  const fmt = new Intl.NumberFormat("fr-FR");
  const line = (k, v) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${fmt.format(Math.abs(v))} ${LABELS[k][Math.abs(v) > 1 ? 1 : 0]}`;
  const rows = (o) => Object.entries(o).filter(([k, v]) => v != null && LABELS[k]);
  const isOptimal = $derived(end.reached.id === end.optimal.id);
  const clips = $derived(replay ? chain(end.replay[replay]).clip : null);
</script>

<section class="end">
  <header class="rise">
    {#if isOptimal}<Burst />{/if}
    <h1>{isOptimal ? "Chemin optimal" : "Fin de la scène"}</h1>
    <p class="num total">+{end.total_points}<small> pts</small></p>
  </header>

  <div class="compare rise-2">
    <article class="panel outcome" class:best={isOptimal}>
      <h3>Ton chemin</h3>
      <p class="title">{end.reached.title}</p>
      <ul>{#each rows(end.reached.outcome) as [k, v]}<li class:up={v > 0} class:down={v < 0}>{line(k, v)}</li>{/each}</ul>
      {#if end.reached.note}<p class="muted note">{end.reached.note}</p>{/if}
      <button class="quiet" onclick={() => (replay = "mine")}>Revoir mon chemin</button>
    </article>
    {#if !isOptimal}
      <article class="panel outcome best">
        <h3>Le chemin optimal</h3>
        <p class="title">{end.optimal.title}</p>
        <ul>{#each rows(end.optimal.outcome) as [k, v]}<li class:up={v > 0} class:down={v < 0}>{line(k, v)}</li>{/each}</ul>
        {#if end.optimal.note}<p class="muted note">{end.optimal.note}</p>{/if}
        <button class="hextech" onclick={() => (replay = "optimal")}>Voir le chemin optimal</button>
      </article>
    {/if}
  </div>

  {#if clips}
    <div class="replay panel">
      <h3>{replay === "mine" ? "Ton chemin" : "Le chemin optimal"}</h3>
      {#key replay}<ScenePlayer base={initialState()} clip={clips} />{/key}
    </div>
  {/if}

  <p class="lesson">{end.lesson}</p>

  <div class="ornament"><span></span></div>

  <ol class="decisions">
    {#each history as h, i}
      <li>
        <h3>Décision {i + 1} : {h.step.question}</h3>
        <ol class="choices">
          {#each h.response.choices as c}
            <li class="panel" class:chosen={c.id === h.chosen}>
              <div class="head">
                <span class="tag grade-{c.grade}"><span class="gem"></span>{GRADE_LABELS[c.grade]}</span>
                <strong>{c.text}</strong>
                <span class="who">
                  {#each h.response.distribution.filter((d) => d.choice_id === c.id) as u}<Avatar user={u} size={24} />{/each}
                </span>
              </div>
              <p>{c.explanation}</p>
            </li>
          {/each}
        </ol>
      </li>
    {/each}
  </ol>
</section>

<style>
  header { position: relative; display: flex; align-items: baseline; gap: 1.5rem; flex-wrap: wrap; }
  .total { margin-left: auto; font-size: 2.2rem; color: var(--lol-gold-bright); }
  .total small { font-size: 0.9rem; color: var(--lol-text-secondary); }
  .compare { display: grid; grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr)); gap: 1.25rem; margin: 1rem 0 1.5rem; }
  .outcome { display: grid; gap: 0.6rem; align-content: start; }
  .outcome.best { border-image: var(--metal) 1; box-shadow: 0 12px 32px rgba(0, 0, 0, 0.55), 0 0 22px rgba(11, 196, 226, 0.12); }
  h3 { margin: 0; }
  .title { font: 700 1.3rem var(--font-display); color: var(--lol-gold-bright); text-transform: uppercase; letter-spacing: 0.04em; margin: 0; }
  ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.25rem; }
  li.up { color: var(--lol-success); }
  li.down { color: #e07a7a; }
  ul li { font: 600 1.05rem var(--font-body); }
  .note { margin: 0; font-size: 0.9rem; }
  .outcome button { justify-self: start; margin-top: 0.5rem; }
  .replay { margin-bottom: 1.5rem; max-width: 34rem; }
  .lesson {
    font: 600 1.15rem/1.5 var(--font-body); color: var(--lol-gold-bright);
    border-left: 2px solid var(--lol-gold); padding: 0.25rem 0 0.25rem 1rem;
    background: linear-gradient(90deg, rgba(200, 170, 110, 0.08), transparent 60%);
  }
  .decisions { list-style: none; padding: 0; margin: 0; display: grid; gap: 2rem; }
  .decisions > li > h3 { margin-bottom: 0.75rem; }
  .choices { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.6rem; }
  .choices li.panel { padding: 0.9rem 1.1rem; }
  .choices li.chosen { border-image: var(--metal) 1; box-shadow: 0 0 0 1px rgba(11, 196, 226, 0.35), 0 10px 28px rgba(0, 0, 0, 0.5); }
  .head { display: flex; align-items: center; gap: 0.7rem; flex-wrap: wrap; margin-bottom: 0.4rem; }
  .head strong { color: var(--lol-gold-bright); flex: 1; min-width: 12rem; }
  .tag { display: inline-flex; align-items: center; gap: 0.4rem; min-width: 6.5rem; font: 700 0.72rem var(--font-body); letter-spacing: 0.14em; text-transform: uppercase; }
  .gem { width: 7px; height: 7px; transform: rotate(45deg); background: currentColor; box-shadow: 0 0 6px currentColor; }
  .who { display: flex; gap: 3px; }
  .choices p { margin: 0; color: var(--lol-text-secondary); }
</style>
