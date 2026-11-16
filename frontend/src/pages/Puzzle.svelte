<script>
  import { api } from "../lib/api.js";
  import { DIFFICULTY_LABELS, ROLE_LABELS, TYPE_LABELS } from "../lib/dd.js";
  import { href } from "../lib/router.js";
  import { views } from "../components/puzzles/index.js";
  import ChoiceList from "../components/ChoiceList.svelte";
  import Countdown from "../components/Countdown.svelte";
  import Result from "../components/Result.svelte";

  let { params } = $props();
  let session = $state(null); // StartResult from the server
  let result = $state(null);
  let chosen = $state(null);
  let busy = $state(false);
  let error = $state("");

  async function begin(mode) {
    error = "";
    try {
      session = await api.start(params.id, mode);
    } catch (e) {
      error = e.status === 404 ? "Ce puzzle n'existe pas (ou plus)." : e.message;
    }
  }

  async function choose(id) {
    if (busy || result) return;
    busy = true;
    chosen = id;
    try {
      result = await api.answer(params.id, id);
    } catch (e) {
      error = e.message;
    } finally {
      busy = false;
    }
  }

  function replay() {
    session = result = chosen = null;
  }

  const p = $derived(session?.puzzle);
  const View = $derived(p && views[p.type]);
</script>

{#if !session}
  <section class="intro">
    <h1>Prêt ?</h1>
    <p class="muted">En mode chrono, tu as un temps limité pour répondre. Au-delà, la réponse compte comme une erreur.</p>
    <div class="modes">
      <button onclick={() => begin("normal")}>Jouer</button>
      <button class="quiet" onclick={() => begin("chrono")}>Jouer en chrono</button>
    </div>
    {#if error}<p class="grade-erreur" role="alert">{error} <a href={href("list")}>Voir les puzzles</a></p>{/if}
  </section>
{:else}
  <article class="puzzle">
    <div class="brief">
      <p class="meta muted">{ROLE_LABELS[p.role]}, {DIFFICULTY_LABELS[p.difficulty].toLowerCase()}, {TYPE_LABELS[p.type].toLowerCase()}</p>
      <h1>{p.title}</h1>
      {#if p.stale}<p class="stale">Écrit pour le patch {p.patch} : les objets ont pu changer depuis.</p>{/if}
      {#if !session.scored && !result}<p class="muted">Déjà fait : entraînement, sans points.</p>{/if}
      <p class="context">{p.context}</p>
      {#if session.mode === "chrono" && !result}
        <Countdown startedAt={session.started_at} limit={p.time_limit} />
      {/if}
    </div>

    <View puzzle={p} />

    <div class="answer">
      {#if result}
        <Result {result} {chosen} />
        <div class="next">
          <button class="quiet" onclick={replay}>Rejouer</button>
          <a class="button" href={href("list")}>Puzzle suivant</a>
        </div>
      {:else}
        <ChoiceList choices={p.choices} disabled={busy} onchoose={choose} />
        <p class="muted hint">Raccourcis : touches 1 à {p.choices.length}.</p>
      {/if}
      {#if error}<p class="grade-erreur" role="alert">{error}</p>{/if}
    </div>
  </article>
{/if}

<style>
  .intro { max-width: 34rem; margin: 10vh auto; }
  .modes { display: flex; gap: 0.75rem; }
  .puzzle {
    display: grid; gap: 1.5rem 2.5rem;
    grid-template-columns: minmax(0, 27rem) minmax(0, 1fr);
    grid-template-areas: "board brief" "board answer" "me answer";
    align-items: start;
  }
  .brief { grid-area: brief; }
  .answer { grid-area: answer; }
  .meta { margin-bottom: 0.25rem; }
  .context { font-size: 1.1rem; }
  .stale { color: var(--excellent); }
  .hint { font-size: 0.85rem; margin-top: 0.75rem; }
  .next { display: flex; gap: 0.75rem; justify-content: flex-end; margin-top: 1.25rem; }
  @media (max-width: 52rem) {
    .puzzle { grid-template-columns: 1fr; grid-template-areas: "brief" "board" "me" "answer"; }
  }
</style>
