<script>
  import { api } from "../lib/api.js";
  import { ROLE_LABELS, TYPE_LABELS } from "../lib/dd.js";
  import { href } from "../lib/router.js";
  import { user } from "../lib/stores.js";
  import Avatar from "../components/Avatar.svelte";
  import DifficultyBadge from "../components/DifficultyBadge.svelte";
  import RoleIcon from "../components/RoleIcon.svelte";

  const daily = api.daily();
  const data = Promise.all([api.profile($user.id), api.puzzles()]);
  const dateFmt = new Intl.DateTimeFormat("fr-FR", { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" });

  function totals(p) {
    const rows = Object.values(p.by_role);
    const answered = rows.reduce((n, r) => n + r.answered, 0);
    const excellent = rows.reduce((n, r) => n + r.excellent, 0);
    return { answered, rate: answered ? Math.round((excellent / answered) * 100) : 0 };
  }
</script>

{#await daily then d}
  <section class="panel major daily rise">
    <p class="when">Puzzle du {dateFmt.format(new Date(d.date))}</p>
    <h1>{d.puzzle.title}</h1>
    <div class="meta">
      <span class="role"><RoleIcon role={d.puzzle.role} size={16} /> {ROLE_LABELS[d.puzzle.role]}</span>
      <span class="diamond"></span>
      <DifficultyBadge difficulty={d.puzzle.difficulty} />
      <span class="diamond"></span>
      <span class="muted">{TYPE_LABELS[d.puzzle.type]}</span>
    </div>
    <div class="row">
      <a class="button hextech" href={href("puzzle", { id: d.puzzle.id })}>
        {d.done_by.some((u) => u.id === $user.id) ? "Revoir" : "Relever le défi"}
      </a>
      {#if d.done_by.length}
        <span class="who">{#each d.done_by as u}<Avatar user={u} size={30} />{/each}</span>
        <span class="muted">{d.done_by.length === 1 ? "l'a déjà fait" : "l'ont déjà fait"}</span>
      {:else}
        <span class="muted">Personne ne l'a encore fait aujourd'hui.</span>
      {/if}
    </div>
  </section>
{:catch e}
  <p class="grade-erreur">{e.message}</p>
{/await}

{#await data then [profile, puzzles]}
  {@const t = totals(profile)}
  <div class="stats rise-2">
    <div class="stat panel"><span class="num value">{profile.total_points}</span><span class="label">Points</span></div>
    <div class="stat panel"><span class="num value">{t.answered}<small>/{puzzles.length}</small></span><span class="label">Puzzles faits</span></div>
    <div class="stat panel"><span class="num value">{t.rate}<small>%</small></span><span class="label">Réponses excellentes</span></div>
  </div>

  <div class="ornament"><span></span></div>

  <section class="rise-3">
    <h2>Entraînement par rôle</h2>
    <nav class="roles">
      {#each Object.entries(ROLE_LABELS) as [role, label]}
        {@const total = puzzles.filter((p) => p.role === role).length}
        {@const done = profile.by_role[role].answered}
        <a class="panel interactive tile" href={href("list", {}, { role })}>
          <RoleIcon {role} size={30} />
          <span class="tile-name">{label}</span>
          <span class="bar"><span style:width="{total ? (done / total) * 100 : 0}%"></span></span>
          <span class="muted count">{done} / {total}</span>
        </a>
      {/each}
    </nav>
  </section>
{/await}

<style>
  .daily { margin-bottom: 1.5rem; }
  .when { color: #c6ad77; font-size: 11px; font-weight: 700; letter-spacing: 0.09em; text-transform: uppercase; margin-bottom: 0.75rem; }
  .when::first-letter { text-transform: uppercase; }
  h1 { font-size: clamp(2rem, 5vw, 3.2rem); margin-bottom: 0.75rem; }
  .meta { display: flex; align-items: center; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 1.75rem; }
  .meta .diamond { width: 5px; height: 5px; box-shadow: none; }
  .role { display: inline-flex; align-items: center; gap: 0.4rem; color: var(--lol-gold-bright); font-weight: 600; }
  .row { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }
  .who { display: flex; gap: 4px; }

  .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
  .stat { display: grid; justify-items: center; padding: 1.25rem; text-align: center; }
  .value { font-size: 2.4rem; color: var(--lol-gold-bright); line-height: 1.1; }
  .value small { font-size: 1rem; color: var(--lol-text-secondary); margin-left: 0.15rem; }
  .label { font-size: 0.75rem; letter-spacing: 0.14em; text-transform: uppercase; color: var(--lol-text-secondary); margin-top: 0.3rem; }

  .roles { display: grid; grid-template-columns: repeat(5, 1fr); gap: 1rem; }
  .tile { display: grid; justify-items: center; gap: 0.5rem; padding: 1.25rem 0.75rem; text-decoration: none; color: var(--lol-gold); }
  .tile:hover { color: var(--lol-gold-bright); }
  .tile-name { font: 0.95rem var(--font-display); color: var(--lol-gold-bright); }
  .bar { width: 100%; height: 4px; background: var(--lol-black); border: 1px solid var(--lol-gold-deep); }
  .bar span { display: block; height: 100%; background: linear-gradient(90deg, var(--lol-blue-dark), var(--lol-hextech)); }
  .count { font-size: 0.8rem; }

  @media (max-width: 52rem) {
    .roles { grid-template-columns: repeat(auto-fit, minmax(7.5rem, 1fr)); }
  }
  @media (max-width: 34rem) {
    .stats { grid-template-columns: 1fr; }
    .stat { grid-template-columns: auto 1fr; justify-items: start; align-items: baseline; gap: 0.75rem; text-align: left; }
    .daily { padding: 1.5rem 1.25rem; }
  }
</style>
