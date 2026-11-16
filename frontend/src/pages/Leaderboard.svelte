<script>
  import { api } from "../lib/api.js";
  import { href } from "../lib/router.js";
  import { user } from "../lib/stores.js";
  import Avatar from "../components/Avatar.svelte";

  const board = api.leaderboard();
  let tab = $state("general");
</script>

<h1>Classement</h1>

<div class="tabs" role="tablist">
  <button role="tab" class:quiet={tab !== "general"} aria-selected={tab === "general"} onclick={() => (tab = "general")}>Général</button>
  <button role="tab" class:quiet={tab !== "daily"} aria-selected={tab === "daily"} onclick={() => (tab = "daily")}>Puzzles du jour</button>
</div>

{#await board then b}
  <ol>
    {#each b[tab] as row, i}
      <li class:me={row.user_id === $user.id}>
        <span class="num rank">{i + 1}</span>
        <a href={href("profile", { id: row.user_id })}><Avatar user={row} size={32} /> {row.name}</a>
        <span class="muted">{row.answered} faits</span>
        <span class="num pts">{row.points}</span>
      </li>
    {/each}
  </ol>
{:catch e}
  <p class="grade-erreur">{e.message}</p>
{/await}

<style>
  .tabs { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }
  ol { list-style: none; padding: 0; margin: 0; max-width: 40rem; }
  li { display: grid; grid-template-columns: 2.5rem 1fr auto 4rem; align-items: center; gap: 1rem; padding: 0.6rem 0; border-bottom: 1px solid var(--reed); }
  li.me { background: var(--bank); }
  .rank { font-size: 1.4rem; color: var(--mist); text-align: center; }
  li:first-child .rank { color: var(--excellent); }
  a { display: flex; align-items: center; gap: 0.6rem; color: var(--foam); text-decoration: none; font-weight: 600; }
  .pts { font-size: 1.5rem; text-align: right; padding-right: 0.5rem; }
</style>
