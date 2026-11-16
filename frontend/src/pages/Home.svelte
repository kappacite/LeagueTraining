<script>
  import { api } from "../lib/api.js";
  import { DIFFICULTY_LABELS, ROLE_LABELS, TYPE_LABELS } from "../lib/dd.js";
  import { href } from "../lib/router.js";
  import { user } from "../lib/stores.js";
  import Avatar from "../components/Avatar.svelte";

  const daily = api.daily();
  const profile = api.profile($user.id);
  const dateFmt = new Intl.DateTimeFormat("fr-FR", { weekday: "long", day: "numeric", month: "long" });
</script>

{#await daily then d}
  <section class="daily">
    <p class="muted when">Puzzle du {dateFmt.format(new Date(d.date))}</p>
    <h1>{d.puzzle.title}</h1>
    <p class="muted">{ROLE_LABELS[d.puzzle.role]}, {DIFFICULTY_LABELS[d.puzzle.difficulty].toLowerCase()}, {TYPE_LABELS[d.puzzle.type].toLowerCase()}</p>
    <div class="row">
      <a class="button" href={href("puzzle", { id: d.puzzle.id })}>
        {d.done_by.some((u) => u.id === $user.id) ? "Revoir" : "Jouer"}
      </a>
      {#if d.done_by.length}
        <span class="who">{#each d.done_by as u}<Avatar user={u} />{/each}</span>
        <span class="muted">{d.done_by.length === 1 ? "l'a déjà fait" : "l'ont déjà fait"}</span>
      {:else}
        <span class="muted">Personne ne l'a encore fait aujourd'hui.</span>
      {/if}
    </div>
  </section>
{:catch e}
  <p class="grade-erreur">{e.message}</p>
{/await}

<section class="me">
  {#await profile then p}
    <p><span class="num big">{p.total_points}</span> points</p>
    <p><span class="num big">{Object.values(p.by_role).reduce((n, r) => n + r.answered, 0)}</span> puzzles faits</p>
  {/await}
</section>

<section>
  <h2>Par rôle</h2>
  <nav class="roles">
    {#each Object.entries(ROLE_LABELS) as [role, label]}
      <a class="button quiet" href={href("list", {}, { role })}>{label}</a>
    {/each}
  </nav>
</section>

<style>
  .daily { padding: 2rem 0 2.5rem; border-bottom: 1px solid var(--reed); margin-bottom: 2rem; }
  .when::first-letter { text-transform: uppercase; }
  h1 { font-size: clamp(2.4rem, 6vw, 4rem); margin-bottom: 0.25rem; }
  .row { display: flex; align-items: center; gap: 0.9rem; flex-wrap: wrap; margin-top: 1.25rem; }
  .who { display: flex; gap: 2px; }
  .me { display: flex; gap: 3rem; margin-bottom: 2rem; }
  .me p { margin: 0; color: var(--mist); }
  .big { font-size: 2.4rem; color: var(--foam); margin-right: 0.3rem; }
  .roles { display: flex; gap: 0.5rem; flex-wrap: wrap; }
</style>
