<script>
  import { api } from "../lib/api.js";
  import { href } from "../lib/router.js";
  import { user } from "../lib/stores.js";
  import Avatar from "../components/Avatar.svelte";

  const board = api.leaderboard();
  let tab = $state("general");
  const TABS = { general: "Général", daily: "Puzzles du jour" };
  // Podium order on screen: 2nd, 1st, 3rd.
  const podium = (rows) => [rows[1], rows[0], rows[2]].map((r, i) => r && { ...r, place: [2, 1, 3][i] }).filter(Boolean);
</script>

<header class="rise">
  <h1>Classement</h1>
  <div class="tabs" role="tablist">
    {#each Object.entries(TABS) as [key, label]}
      <button role="tab" class:quiet={tab !== key} aria-selected={tab === key} onclick={() => (tab = key)}>{label}</button>
    {/each}
  </div>
</header>

{#await board then b}
  {@const rows = b[tab]}
  {#key tab}
    <div class="podium rise-2">
      {#each podium(rows) as r}
        <a class="step panel p{r.place}" class:me={r.user_id === $user.id} href={href("profile", { id: r.user_id })}>
          <span class="num rank">{r.place}</span>
          <Avatar user={r} size={r.place === 1 ? 72 : 56} />
          <span class="name">{r.name}</span>
          <span class="num pts">{r.points}<small> pts</small></span>
        </a>
      {/each}
    </div>

    {#if rows.length > 3}
      <ol class="rest rise-3">
        {#each rows.slice(3) as r, i}
          <li class:me={r.user_id === $user.id}>
            <span class="num rank">{i + 4}</span>
            <a href={href("profile", { id: r.user_id })}><Avatar user={r} size={32} /> {r.name}</a>
            <span class="muted">{r.answered} faits</span>
            <span class="num pts">{r.points}</span>
          </li>
        {/each}
      </ol>
    {/if}
  {/key}
{:catch e}
  <p class="grade-erreur">{e.message}</p>
{/await}

<style>
  header { display: flex; align-items: end; justify-content: space-between; flex-wrap: wrap; gap: 1rem; margin-bottom: 2rem; }
  h1 { margin: 0; }
  .tabs { display: flex; gap: 0.5rem; }
  .tabs button { padding: 0.7em 1.2em; }

  .podium { display: grid; grid-template-columns: repeat(3, minmax(0, 14rem)); justify-content: center; align-items: end; gap: 1rem; margin-bottom: 2rem; }
  .step { display: grid; justify-items: center; gap: 0.5rem; padding: 1.5rem 1rem; text-decoration: none; color: var(--lol-text); text-align: center; }
  .p1 { border-image: var(--metal) 1; padding-top: 2.25rem; padding-bottom: 2.25rem; box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6), 0 0 30px rgba(200, 170, 110, 0.15); }
  .p1 :global(.avatar) { box-shadow: 0 0 0 2px var(--lol-gold), 0 0 18px rgba(200, 170, 110, 0.5); }
  .rank { font-size: 1.6rem; color: var(--lol-gold-dark); }
  .p1 .rank { font-size: 2.2rem; color: var(--lol-gold); }
  .name { font: 1rem var(--font-display); color: var(--lol-gold-bright); }
  .pts { font-size: 1.5rem; color: var(--lol-gold-bright); }
  .pts small { font-size: 0.8rem; color: var(--lol-text-secondary); }
  .me { outline: 1px solid var(--lol-hextech); outline-offset: 3px; }

  .rest { list-style: none; padding: 0; margin: 0 auto; max-width: 44rem; }
  .rest li { display: grid; grid-template-columns: 3rem 1fr auto 4rem; align-items: center; gap: 1rem; padding: 0.7rem 0.5rem; border-bottom: 1px solid var(--lol-gold-deep); }
  .rest .rank { font-size: 1.2rem; text-align: center; }
  .rest a { display: flex; align-items: center; gap: 0.75rem; color: var(--lol-gold-bright); text-decoration: none; font-weight: 600; }
  .rest .pts { text-align: right; font-size: 1.2rem; }
  @media (max-width: 40rem) {
    .podium { grid-template-columns: repeat(3, 1fr); gap: 0.5rem; }
    .step { padding: 1rem 0.4rem; }
    .name { font-size: 0.8rem; }
    .rest li { grid-template-columns: 2rem 1fr 3rem; }
    .rest .muted { display: none; }
  }
</style>
