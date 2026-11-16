<script>
  // Drives a scene: intro → choices → consequence → next intro … → end screen.
  import { api } from "../../lib/api.js";
  import { GRADE_LABELS } from "../../lib/dd.js";
  import { endState, initialState } from "../../lib/timeline.js";
  import ChoiceList from "../ChoiceList.svelte";
  import Countdown from "../Countdown.svelte";
  import ScenePlayer from "../ScenePlayer.svelte";
  import SceneEnd from "../SceneEnd.svelte";

  let { session, puzzleId } = $props();

  // Rebuild the map from clips already played (resumed play).
  let base = $state(session.played.reduce(endState, initialState()));
  let step = $state(session.step);
  let clip = $state(session.step.intro);
  let key = $state(0);
  let phase = $state("intro"); // intro | choose | consequence | end
  let shownAt = $state(null);
  let last = $state(null); // last answer response
  let history = $state([]); // [{ step, response, chosen }]
  let end = $state(null);
  let busy = $state(false);
  let error = $state("");

  function show(newClip, newPhase) {
    base = endState(base, clip);
    clip = newClip;
    phase = newPhase;
    key += 1;
  }

  function onClipEnd() {
    if (phase === "intro") {
      phase = "choose";
      shownAt = new Date().toISOString();
    } else if (phase === "consequence") {
      if (last.next) {
        step = last.next;
        show(step.intro, "intro");
      } else {
        end = last.end;
        phase = "end";
      }
    }
  }

  async function choose(id) {
    if (busy || phase !== "choose") return;
    busy = true;
    error = "";
    try {
      last = await api.answer(puzzleId, id);
      history = [...history, { step, response: last, chosen: id }];
      show(last.consequence, "consequence");
    } catch (e) {
      error = e.message;
    } finally {
      busy = false;
    }
  }
</script>

{#if phase === "end"}
  <SceneEnd {end} {history} />
{:else}
  <div class="stage">
    <div class="board">
      {#key key}
        <ScenePlayer {base} {clip} onend={onClipEnd} />
      {/key}
    </div>

    <div class="side">
      <p class="progress muted">Décision {history.length + (phase === "consequence" ? 0 : 1)}</p>
      {#if phase === "intro"}
        <p class="waiting">Observe la carte…</p>
      {:else if phase === "choose"}
        <h2>{step.question}</h2>
        {#if session.mode === "chrono"}<Countdown startedAt={shownAt} limit={step.time_limit} />{/if}
        <ChoiceList choices={step.choices} disabled={busy} onchoose={choose} />
      {:else if phase === "consequence"}
        <div class="verdict {last.grade}">
          <span class="gem"></span>
          <span class="label">{last.timed_out ? "Temps écoulé" : GRADE_LABELS[last.grade]}</span>
          {#if last.scored}<span class="num">+{last.points}</span>{/if}
        </div>
        <p class="muted">{last.next ? "La partie continue…" : "Fin de la scène…"}</p>
      {/if}
      {#if error}<p class="grade-erreur" role="alert">{error}</p>{/if}
    </div>
  </div>
{/if}

<style>
  .stage { display: grid; grid-template-columns: minmax(0, 30rem) minmax(0, 1fr); gap: 2rem 2.5rem; align-items: start; }
  .progress { font-size: 0.75rem; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 0.4rem; }
  .waiting { font: 600 1.2rem var(--font-display); color: var(--lol-blue-light); letter-spacing: 0.06em; }
  h2 { font-size: 1.5rem; color: var(--lol-gold-bright); }
  .verdict { display: flex; align-items: center; gap: 0.8rem; font: 2rem var(--font-display); animation: rise 400ms var(--ease) both; }
  .verdict .gem { width: 14px; height: 14px; transform: rotate(45deg); background: currentColor; box-shadow: 0 0 12px currentColor; }
  .verdict .num { margin-left: auto; font-size: 1.5rem; color: var(--lol-gold-bright); }
  .excellent { color: var(--excellent); }
  .correct { color: var(--correct); }
  .erreur { color: var(--erreur); }
  @media (max-width: 52rem) { .stage { grid-template-columns: 1fr; } }
</style>
