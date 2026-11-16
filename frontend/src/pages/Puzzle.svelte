<script>
  import { api } from "../lib/api.js";
  import { ROLE_LABELS, TYPE_LABELS } from "../lib/dd.js";
  import { href } from "../lib/router.js";
  import { views } from "../components/puzzles/index.js";
  import ChoiceList from "../components/ChoiceList.svelte";
  import Countdown from "../components/Countdown.svelte";
  import DifficultyBadge from "../components/DifficultyBadge.svelte";
  import Result from "../components/Result.svelte";
  import RoleIcon from "../components/RoleIcon.svelte";

  let { params } = $props();
  let session = $state(null); // StartResult from the server
  let result = $state(null);
  let chosen = $state(null);
  let busy = $state(false);
  let error = $state("");

  async function begin(mode) {
    if (busy) return;
    busy = true;
    error = "";
    try {
      session = await api.start(params.id, mode);
    } catch (e) {
      error = e.status === 404 ? "Ce puzzle n'existe pas (ou plus)." : e.message;
    } finally {
      busy = false;
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
  <section class="intro panel major rise">
    <h1>Prêt ?</h1>
    <div class="ornament"><span></span></div>
    <p class="muted">En mode chrono, tu as un temps limité pour répondre. Au-delà, la réponse compte comme une erreur.</p>
    <div class="modes">
      <button class="hextech" disabled={busy} onclick={() => begin("normal")}>Jouer</button>
      <button class="quiet" disabled={busy} onclick={() => begin("chrono")}>Jouer en chrono</button>
    </div>
    {#if error}<p class="grade-erreur" role="alert">{error} <a href={href("list")}>Voir les puzzles</a></p>{/if}
  </section>
{:else}
  <article class="puzzle">
    <div class="brief rise">
      <div class="meta">
        <span class="role"><RoleIcon role={p.role} size={16} /> {ROLE_LABELS[p.role]}</span>
        <DifficultyBadge difficulty={p.difficulty} />
        <span class="muted">{TYPE_LABELS[p.type]}</span>
      </div>
      <h1>{p.title}</h1>
      {#if p.stale}<p class="notice">Écrit pour le patch {p.patch} : les objets ont pu changer depuis.</p>{/if}
      {#if !session.scored && !result}<p class="notice practice">Déjà fait : entraînement, sans points.</p>{/if}
      <p class="context">{p.context}</p>
      {#if session.mode === "chrono" && !result}
        <Countdown startedAt={session.started_at} limit={p.time_limit} />
      {/if}
    </div>

    <View puzzle={p} />

    <div class="answer rise-2">
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
  .intro { max-width: 36rem; margin: 8vh auto; text-align: center; }
  .intro .ornament { margin: 1rem 3rem 1.5rem; }
  .intro p { margin-inline: auto; }
  .modes { display: flex; gap: 0.75rem; justify-content: center; flex-wrap: wrap; margin-top: 1.5rem; }
  .puzzle {
    display: grid; gap: 1.5rem 2.5rem;
    grid-template-columns: minmax(0, 27rem) minmax(0, 1fr);
    grid-template-areas: "board brief" "board answer";
    grid-template-rows: auto 1fr;
    align-items: start;
  }
  .brief { grid-area: brief; }
  .answer { grid-area: answer; }
  .meta { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.6rem; }
  .role { display: inline-flex; align-items: center; gap: 0.4rem; color: var(--lol-gold-bright); font-weight: 600; }
  h1 { font-size: clamp(1.6rem, 3.2vw, 2.3rem); }
  .context { font-size: 1.1rem; color: var(--lol-text); }
  .notice { color: var(--lol-gold); border-left: 2px solid var(--lol-gold-dark); padding-left: 0.75rem; font-size: 0.9rem; }
  .practice { color: var(--lol-blue-light); border-color: var(--lol-blue-dark); }
  .hint { font-size: 0.8rem; margin-top: 0.75rem; letter-spacing: 0.04em; }
  .next { display: flex; gap: 0.75rem; justify-content: flex-end; flex-wrap: wrap; margin-top: 1.5rem; }
  @media (max-width: 52rem) {
    .puzzle { grid-template-columns: 1fr; grid-template-areas: "brief" "board" "answer"; }
  }
</style>
