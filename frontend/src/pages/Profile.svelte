<script>
  import { api } from "../lib/api.js";
  import { DIFFICULTY_LABELS, ROLE_LABELS } from "../lib/dd.js";
  import Avatar from "../components/Avatar.svelte";
  import DifficultyBadge from "../components/DifficultyBadge.svelte";
  import RoleIcon from "../components/RoleIcon.svelte";

  let { params } = $props();
  const profile = api.profile(params.id);
  const R = 34;
  const C = 2 * Math.PI * R;
  const rate = (s) => (s.answered ? s.excellent / s.answered : 0);
</script>

{#await profile then p}
  <header class="panel major rise">
    <Avatar user={p.user} size={84} />
    <div>
      <h1>{p.user.name}</h1>
      <p class="muted">Taux de réponses excellentes par rôle et par difficulté, sur les puzzles faits.</p>
    </div>
    <div class="total"><span class="num">{p.total_points}</span><span class="label">Points</span></div>
  </header>

  <div class="ornament"><span></span></div>

  <section class="rise-2">
    <h2>Maîtrise par rôle</h2>
    <div class="medals">
      {#each Object.entries(ROLE_LABELS) as [role, label]}
        {@const s = p.by_role[role]}
        <div class="medal" class:empty={!s.answered}>
          <svg viewBox="0 0 80 80" aria-hidden="true">
            <polygon class="frame" points="40,2 76,40 40,78 4,40" />
            <circle class="track" cx="40" cy="40" r={R} />
            <circle class="ring" cx="40" cy="40" r={R} stroke-dasharray="{C * rate(s)} {C}" transform="rotate(-90 40 40)" />
          </svg>
          <span class="icon"><RoleIcon {role} size={26} /></span>
          <span class="name">{label}</span>
          <span class="muted small">{s.answered ? `${Math.round(rate(s) * 100)} % excellent` : "Pas encore joué"}</span>
          <span class="num small">{s.points} pts</span>
        </div>
      {/each}
    </div>
  </section>

  <section class="rise-3">
    <h2>Par difficulté</h2>
    <div class="levels">
      {#each Object.keys(DIFFICULTY_LABELS) as d}
        {@const s = p.by_difficulty[d]}
        <div class="level panel">
          <DifficultyBadge difficulty={d} />
          <div class="hexbar" title="{Math.round(rate(s) * 100)} % excellent"><span style:width="{rate(s) * 100}%"></span></div>
          <span class="muted small">{s.answered} faits, {s.excellent} excellents, <b class="num">{s.points}</b> pts</span>
        </div>
      {/each}
    </div>
  </section>
{:catch e}
  <p class="grade-erreur">{e.status === 404 ? "Ce joueur n'existe pas." : e.message}</p>
{/await}

<style>
  header { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 1.5rem; }
  header :global(.avatar) { box-shadow: 0 0 0 2px var(--lol-gold), 0 0 0 5px var(--lol-black), 0 0 0 6px var(--lol-gold-dark); }
  h1 { margin: 0 0 0.25rem; }
  header p { margin: 0; }
  .total { display: grid; justify-items: center; }
  .total .num { font-size: 3rem; color: var(--lol-gold-bright); line-height: 1; }
  .label { font-size: 0.7rem; letter-spacing: 0.14em; text-transform: uppercase; color: var(--lol-text-secondary); }
  section { margin-bottom: 2.5rem; }

  .medals { display: grid; grid-template-columns: repeat(5, 1fr); gap: 1rem; }
  .medal { position: relative; display: grid; justify-items: center; gap: 0.3rem; text-align: center; }
  .medal svg { width: 110px; height: 110px; }
  .frame { fill: var(--lol-black); stroke: var(--lol-gold-dark); stroke-width: 1.5; }
  .track { fill: none; stroke: var(--lol-gold-deep); stroke-width: 4; }
  .ring { fill: none; stroke: var(--lol-hextech); stroke-width: 4; stroke-linecap: butt; transition: stroke-dasharray 800ms var(--ease); }
  .icon { position: absolute; top: 42px; color: var(--lol-gold); }
  .empty .icon { color: var(--lol-muted); }
  .name { font: 0.95rem var(--font-display); color: var(--lol-gold-bright); }
  .small { font-size: 0.8rem; }

  .levels { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
  .level { display: grid; gap: 0.75rem; }
  .hexbar { height: 8px; background: var(--lol-black); border: 1px solid var(--lol-gold-dark); }
  .hexbar span { display: block; height: 100%; background: linear-gradient(90deg, var(--lol-blue-dark), var(--lol-hextech)); transition: width 800ms var(--ease); }
  .level b { color: var(--lol-gold-bright); }

  @media (max-width: 52rem) {
    .medals { grid-template-columns: repeat(auto-fit, minmax(8rem, 1fr)); }
    .levels { grid-template-columns: 1fr; }
  }
  @media (max-width: 34rem) {
    header { grid-template-columns: auto 1fr; }
    .total { grid-column: 1 / -1; justify-items: start; }
  }
</style>
