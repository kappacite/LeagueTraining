<script>
  import { ddImg } from "../lib/dd.js";
  import { toSvg } from "../lib/minimap.js";

  let { scene, size = 420 } = $props();
  const r = $derived(size * 0.034);
  const OBJECTIVES = { dragon: "Dragon", baron: "Baron Nashor", herald: "Héraut", grubs: "Larves du Néant", atakhan: "Atakhan" };
</script>

<figure>
  <svg viewBox="0 0 {size} {size}" role="img" aria-label="Minimap : position des champions et des balises">
    <defs>
      <clipPath id="round"><circle r={r} /></clipPath>
    </defs>
    <image href={ddImg("map", "map11")} width={size} height={size} />
    {#each scene.wards as w}
      {@const p = toSvg(w.x, w.y, size)}
      <rect x={p.cx - 5} y={p.cy - 5} width="10" height="10" transform="rotate(45 {p.cx} {p.cy})"
            class="ward {w.team}" />
    {/each}
    {#each scene.champions as c}
      {@const p = toSvg(c.x, c.y, size)}
      <g transform="translate({p.cx} {p.cy})" class:stale={c.last_seen != null || c.hidden} class:dead={c.dead}>
        {#if c.me}<circle r={r + 6} class="me-halo" />{/if}
        <image href={ddImg("champion", c.champion)} x={-r} y={-r} width={r * 2} height={r * 2} clip-path="url(#round)" />
        <circle r={r} class="ring {c.team}" />
        {#if c.dead}<path class="cross" d="M{-r * 0.7} {-r * 0.7} L{r * 0.7} {r * 0.7} M{r * 0.7} {-r * 0.7} L{-r * 0.7} {r * 0.7}" />{/if}
        {#if c.last_seen != null}
          <text y={r + 13} text-anchor="middle">il y a {c.last_seen} s</text>
        {/if}
        <title>{c.champion}{c.me ? " (toi)" : ""}</title>
      </g>
    {/each}
    {#each scene.events ?? [] as e}
      {@const p = toSvg(e.x, e.y, size)}
      <g class="event {e.type}" transform="translate({p.cx} {p.cy})">
        <circle r={r * 1.6} />
        {#if e.label}<text y={-r * 2} text-anchor="middle">{e.label}</text>{/if}
      </g>
    {/each}
  </svg>
  {#if scene.objectives.length}
    <figcaption>
      {#each scene.objectives as o}
        <span>
          {OBJECTIVES[o.type] ?? o.type}
          <strong class="num">{o.spawn_in == null ? "en vie" : `dans ${o.spawn_in} s`}</strong>
        </span>
      {/each}
    </figcaption>
  {/if}
</figure>

<style>
  figure { margin: 0; }
  /* Gold setting around the map. */
  svg {
    width: 100%; height: auto; display: block; background: var(--lol-black);
    border: 2px solid transparent; border-image: var(--metal) 1;
    box-shadow: 0 0 0 4px var(--lol-black), 0 0 0 5px var(--lol-gold-deep), 0 18px 40px rgba(0, 0, 0, 0.6);
  }
  .ring { fill: none; stroke-width: 3; }
  .ring.ally { stroke: var(--lol-blue-light); }
  .ring.enemy { stroke: var(--lol-danger); }
  .me-halo { fill: none; stroke: var(--lol-gold); stroke-width: 2; stroke-dasharray: 4 3; filter: drop-shadow(0 0 4px var(--lol-gold)); }
  .stale { opacity: 0.45; }
  .dead image { filter: grayscale(1) brightness(0.5); }
  .cross { stroke: var(--lol-danger); stroke-width: 3; stroke-linecap: round; }
  .event circle { fill: none; stroke-width: 2; animation: ping 1.5s ease-out both; transform-box: fill-box; transform-origin: center; }
  .event.ping circle { stroke: var(--lol-gold-hover); }
  .event.kill circle { stroke: var(--lol-danger); }
  .event.objective circle { stroke: var(--lol-hextech); fill: rgba(11, 196, 226, 0.15); }
  @keyframes ping { from { transform: scale(0.3); opacity: 1; } to { transform: scale(1.4); opacity: 0; } }
  .ward { stroke: var(--lol-black); stroke-width: 1.5; }
  .ward.ally { fill: var(--lol-hextech); filter: drop-shadow(0 0 3px var(--lol-hextech)); }
  .ward.enemy { fill: var(--lol-danger); }
  text { fill: var(--lol-gold-bright); font: 600 11px var(--font-body); paint-order: stroke; stroke: var(--lol-black); stroke-width: 3px; }
  figcaption { display: flex; flex-wrap: wrap; gap: 0.5rem 1.25rem; margin-top: 0.9rem; color: var(--lol-text-secondary); font-size: 0.9rem; }
  figcaption strong { color: var(--lol-gold-bright); margin-left: 0.3em; font-family: var(--font-display); }
</style>
