<script>
  import { ddImg } from "../../lib/dd.js";
  import Minimap from "../Minimap.svelte";
  import ItemIcons from "../ItemIcons.svelte";

  let { puzzle } = $props();
  const me = $derived(puzzle.me);
</script>

<div class="side">
<Minimap scene={puzzle.scene} />
<div class="me panel">
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
  .side { grid-area: board; display: grid; gap: 1.25rem; }
  .me { display: flex; flex-wrap: wrap; align-items: center; gap: 0.9rem; padding: 0.9rem 1rem; }
  .portrait { border-radius: 50%; box-shadow: 0 0 0 2px var(--lol-gold), 0 0 0 4px var(--lol-black), 0 0 0 5px var(--lol-blue-dark); }
  .bars { display: grid; gap: 4px; min-width: 9rem; flex: 1; }
  .bar { position: relative; height: 18px; background: var(--lol-black); border: 1px solid var(--lol-gold-deep); overflow: hidden; }
  .bar::before { content: ""; position: absolute; inset: 0; width: var(--v); }
  .hp::before { background: linear-gradient(180deg, #4fae5f, #23602f); }
  .mana::before { background: linear-gradient(180deg, #4d8fd6, #1f4f8c); }
  .bar span { position: relative; padding: 0 0.5rem; font-size: 0.75rem; line-height: 16px; color: var(--lol-gold-bright); text-shadow: 0 1px 2px #000; }
  .kit { display: flex; align-items: center; gap: 4px; }
  .kit img { border: 1px solid var(--lol-gold-dark); }
  .gold { color: var(--lol-gold); margin-right: 0.5rem; font-size: 1.1rem; }
</style>
