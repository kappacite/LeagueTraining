<script>
  import { api } from "../lib/api.js";
  import { DIFFICULTY_LABELS, GRADE_LABELS, ROLE_LABELS, TYPE_LABELS } from "../lib/dd.js";
  import { href } from "../lib/router.js";
  import DifficultyBadge from "../components/DifficultyBadge.svelte";
  import RoleIcon from "../components/RoleIcon.svelte";

  let { query } = $props();
  const filters = { role: query.role ?? "", difficulty: query.difficulty ?? "", type: query.type ?? "" };
  const puzzles = api.puzzles(filters);

  // Filters live in the URL so a reload or a shared link keeps them.
  function set(key, value) {
    location.hash = href("list", {}, { ...filters, [key]: value });
  }
  const groups = [
    ["role", "Rôle", ROLE_LABELS],
    ["difficulty", "Difficulté", DIFFICULTY_LABELS],
    ["type", "Type", TYPE_LABELS],
  ];
</script>

<header class="rise">
  <h1>Entraînement</h1>
  <form class="filters" onsubmit={(e) => e.preventDefault()}>
    {#each groups as [key, label, options]}
      <label>
        <span>{label}</span>
        <select value={filters[key]} onchange={(e) => set(key, e.currentTarget.value)}>
          <option value="">Tous</option>
          {#each Object.entries(options) as [value, text]}<option {value}>{text}</option>{/each}
        </select>
      </label>
    {/each}
  </form>
</header>

{#await puzzles then list}
  {#if list.length}
    <ul class="rise-2">
      {#each list as p}
        <li>
          <a class="panel interactive" class:done={p.done} href={href("puzzle", { id: p.id })}>
            <span class="role" title={ROLE_LABELS[p.role]}><RoleIcon role={p.role} size={22} /></span>
            <span class="body">
              <span class="title">{p.title}</span>
              <span class="meta">
                <DifficultyBadge difficulty={p.difficulty} />
                <span class="muted">{ROLE_LABELS[p.role]}, {TYPE_LABELS[p.type].toLowerCase()}</span>
              </span>
            </span>
            <span class="status {p.done ? `grade-${p.grade}` : ''}">
              {#if p.done}<span class="seal"></span>{GRADE_LABELS[p.grade]}{:else}À relever{/if}
            </span>
          </a>
        </li>
      {/each}
    </ul>
  {:else}
    <p class="muted">Aucun puzzle avec ces filtres. Essaie d'en retirer un.</p>
  {/if}
{:catch e}
  <p class="grade-erreur">{e.message}</p>
{/await}

<style>
  header { display: flex; align-items: end; justify-content: space-between; gap: 1.5rem; flex-wrap: wrap; margin-bottom: 1.5rem; }
  h1 { margin: 0; }
  .filters { display: flex; gap: 0.75rem; flex-wrap: wrap; }
  label { display: grid; gap: 0.3rem; }
  label span { font-size: 0.7rem; letter-spacing: 0.14em; text-transform: uppercase; color: var(--lol-text-secondary); }
  ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.6rem; }
  a.panel {
    display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 1.25rem;
    padding: 0.9rem 1.25rem; color: var(--lol-text); text-decoration: none;
  }
  .role {
    display: grid; place-items: center; width: 44px; height: 44px; color: var(--lol-gold);
    border: 1px solid var(--lol-gold-dark); transform: rotate(45deg); background: var(--lol-black);
  }
  .role :global(svg) { transform: rotate(-45deg); }
  .body { display: grid; gap: 0.3rem; min-width: 0; }
  .title { font: 700 1.05rem var(--font-display); letter-spacing: 0.04em; text-transform: uppercase; color: var(--lol-gold-bright); }
  .meta { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; font-size: 0.85rem; }
  .status { font: 700 0.8rem var(--font-body); letter-spacing: 0.12em; text-transform: uppercase; color: var(--lol-text-secondary); display: flex; align-items: center; gap: 0.5rem; }
  .seal { width: 9px; height: 9px; transform: rotate(45deg); background: currentColor; box-shadow: 0 0 8px currentColor; }
  .done { opacity: 0.85; }
  @media (max-width: 40rem) {
    a.panel { grid-template-columns: auto 1fr; gap: 0.9rem; }
    .status { grid-column: 2; }
    .role { width: 36px; height: 36px; }
  }
</style>
