<script>
  import { ddImg } from "../../lib/dd.js";
  import ItemIcons from "../ItemIcons.svelte";

  let { puzzle } = $props();
</script>

<div class="side">
<div class="board">
  <section class="team ally">
    <h3>Ton équipe</h3>
    <div class="row mine">
      <img src={ddImg("champion", puzzle.me.champion)} alt={puzzle.me.champion} width="48" height="48" />
      <span>{puzzle.me.champion} <span class="muted">niveau {puzzle.me.level}</span></span>
      <ItemIcons items={puzzle.me.items} />
    </div>
    {#each puzzle.allies as a}
      <div class="row"><img src={ddImg("champion", a)} alt={a} width="40" height="40" /><span>{a}</span></div>
    {/each}
  </section>
  <section class="team enemy">
    <h3>En face</h3>
    {#each puzzle.enemies as e}
      <div class="row">
        <img src={ddImg("champion", e.champion)} alt={e.champion} width="40" height="40" />
        <span>{e.champion}</span>
        <ItemIcons items={e.items} size={28} />
      </div>
    {/each}
  </section>
</div>
<div class="me"><span class="num gold">{puzzle.me.gold} PO</span> <span class="muted">à dépenser</span></div>
</div>

<style>
  .side { grid-area: board; display: grid; gap: 1rem; align-content: start; }
  .board { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  .team { padding: 1rem; background: var(--bank); border-radius: 6px; border-top: 3px solid; }
  .ally { border-color: var(--ally); }
  .enemy { border-color: var(--enemy); }
  .row { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.6rem; flex-wrap: wrap; }
  .row img { border-radius: 50%; }
  .mine img:first-child { box-shadow: 0 0 0 2px var(--excellent); }
  .gold { color: var(--excellent); font-size: 1.6rem; }
  @media (max-width: 34rem) { .board { grid-template-columns: 1fr; } }
</style>
