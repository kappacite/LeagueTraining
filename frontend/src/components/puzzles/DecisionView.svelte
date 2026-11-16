<script>
  import { ddImg } from "../../lib/dd.js";
  import Minimap from "../Minimap.svelte";
  import ItemIcons from "../ItemIcons.svelte";

  let { puzzle } = $props();
  const me = $derived(puzzle.me);
</script>

<div class="side">
<Minimap scene={puzzle.scene} />
<div class="me">
  <img class="portrait" src={ddImg("champion", me.champion)} alt={me.champion} width="56" height="56" />
  <div class="bars">
    <div class="bar hp" style:--v="{me.hp}%"><span>PV <b class="num">{me.hp}%</b></span></div>
    {#if me.mana != null}
      <div class="bar mana" style:--v="{me.mana}%"><span>Mana <b class="num">{me.mana}%</b></span></div>
    {/if}
  </div>
  <div class="kit">
    <span class="num gold">{me.gold} PO</span>
    {#each me.summoners as s}<img src={ddImg("spell", s)} alt={s} width="28" height="28" />{/each}
    <ItemIcons items={me.items} size={28} />
  </div>
</div>
</div>

<style>
  .side { grid-area: board; display: grid; gap: 1rem; }
  .me { display: flex; flex-wrap: wrap; align-items: center; gap: 0.75rem; }
  .portrait { border-radius: 50%; box-shadow: 0 0 0 3px var(--ally); }
  .bars { display: grid; gap: 4px; min-width: 9rem; flex: 1; }
  .bar { position: relative; height: 20px; background: var(--river); border-radius: 3px; overflow: hidden; }
  .bar::before { content: ""; position: absolute; inset: 0; width: var(--v); }
  .hp::before { background: #3f8f4f; }
  .mana::before { background: #3a6fb0; }
  .bar span { position: relative; padding: 0 0.5rem; font-size: 0.8rem; line-height: 20px; }
  .kit { display: flex; align-items: center; gap: 4px; }
  .kit img { border-radius: 3px; }
  .gold { color: var(--excellent); margin-right: 0.5rem; font-size: 1.1rem; }
</style>
