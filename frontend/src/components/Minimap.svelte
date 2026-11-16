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
      <g transform="translate({p.cx} {p.cy})" class:stale={c.last_seen != null}>
        {#if c.me}<circle r={r + 6} class="me-halo" />{/if}
        <image href={ddImg("champion", c.champion)} x={-r} y={-r} width={r * 2} height={r * 2} clip-path="url(#round)" />
        <circle r={r} class="ring {c.team}" />
        {#if c.last_seen != null}
          <text y={r + 13} text-anchor="middle">il y a {c.last_seen} s</text>
        {/if}
        <title>{c.champion}{c.me ? " (toi)" : ""}</title>
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
  svg { width: 100%; height: auto; display: block; border-radius: 6px; background: #0c1a20; }
  .ring { fill: none; stroke-width: 3; }
  .ring.ally { stroke: var(--ally); }
  .ring.enemy { stroke: var(--enemy); }
  .me-halo { fill: none; stroke: var(--excellent); stroke-width: 2; stroke-dasharray: 4 3; }
  .stale { opacity: 0.55; }
  .ward { stroke: #0c1a20; stroke-width: 1.5; }
  .ward.ally { fill: var(--ally); }
  .ward.enemy { fill: var(--enemy); }
  text { fill: var(--foam); font: 600 12px var(--display); paint-order: stroke; stroke: #0c1a20; stroke-width: 3px; }
  figcaption { display: flex; flex-wrap: wrap; gap: 0.5rem 1.25rem; margin-top: 0.6rem; color: var(--mist); }
  figcaption strong { color: var(--foam); margin-left: 0.3em; }
</style>
