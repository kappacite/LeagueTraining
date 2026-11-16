<script>
  import { ddImg } from "../../lib/dd.js";
  import ItemIcons from "../ItemIcons.svelte";

  let { puzzle } = $props();
</script>

<div class="side">
<div class="board">
  <section class="team ally panel">
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
  <section class="team enemy panel">
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
<div class="me panel"><span class="num gold">{puzzle.me.gold} PO</span> <span class="muted">à dépenser</span></div>
</div>

<style>
  .side { grid-area: board; display: grid; gap: 1rem; align-content: start; }
  .board { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  .team { padding: 1rem 1.1rem; }
  .ally { box-shadow: inset 0 2px 0 var(--lol-blue-light), 0 12px 32px rgba(0, 0, 0, 0.55); }
  .enemy { box-shadow: inset 0 2px 0 var(--lol-danger), 0 12px 32px rgba(0, 0, 0, 0.55); }
  .row { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.6rem; flex-wrap: wrap; color: var(--lol-gold-bright); }
  .row img { border-radius: 50%; box-shadow: 0 0 0 1px var(--lol-gold-dark); }
  .mine img:first-child { box-shadow: 0 0 0 2px var(--lol-gold), 0 0 12px rgba(200, 170, 110, 0.4); }
  .me { padding: 0.9rem 1.1rem; display: flex; align-items: baseline; gap: 0.6rem; }
  .gold { color: var(--lol-gold); font-size: 1.8rem; }
  @media (max-width: 34rem) { .board { grid-template-columns: 1fr; } }
</style>
