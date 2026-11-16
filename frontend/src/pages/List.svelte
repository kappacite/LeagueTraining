<script>
  import { api } from "../lib/api.js";
  import { DIFFICULTY_LABELS, GRADE_LABELS, ROLE_LABELS, TYPE_LABELS } from "../lib/dd.js";
  import { href } from "../lib/router.js";

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

<h1>Puzzles</h1>

<form class="filters" onsubmit={(e) => e.preventDefault()}>
  {#each groups as [key, label, options]}
    <label>
      <span class="muted">{label}</span>
      <select value={filters[key]} onchange={(e) => set(key, e.currentTarget.value)}>
        <option value="">Tous</option>
        {#each Object.entries(options) as [value, text]}<option {value}>{text}</option>{/each}
      </select>
    </label>
  {/each}
</form>

{#await puzzles then list}
  {#if list.length}
    <ul>
      {#each list as p}
        <li>
          <a href={href("puzzle", { id: p.id })}>
            <span class="title">{p.title}</span>
            <span class="muted">{ROLE_LABELS[p.role]}, {DIFFICULTY_LABELS[p.difficulty].toLowerCase()}, {TYPE_LABELS[p.type].toLowerCase()}</span>
            <span class="status {p.done ? `grade-${p.grade}` : 'muted'}">{p.done ? GRADE_LABELS[p.grade] : "À faire"}</span>
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
  .filters { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; }
  label { display: grid; gap: 0.2rem; font-size: 0.9rem; }
  select { font: inherit; color: var(--foam); background: var(--bank); border: 1px solid var(--reed); border-radius: 4px; padding: 0.4rem 0.6rem; }
  ul { list-style: none; padding: 0; margin: 0; }
  li a {
    display: grid; grid-template-columns: 1fr auto auto; gap: 1.5rem; align-items: baseline;
    padding: 0.9rem 0.25rem; border-bottom: 1px solid var(--reed); color: var(--foam); text-decoration: none;
  }
  li a:hover .title { text-decoration: underline; }
  .title { font-weight: 600; }
  .status { font: 700 1rem var(--display); min-width: 5.5rem; text-align: right; }
  @media (max-width: 40rem) { li a { grid-template-columns: 1fr auto; } li a .muted:not(.status) { display: none; } }
</style>
