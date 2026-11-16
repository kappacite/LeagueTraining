<script>
  import { api } from "../lib/api.js";
  import { DIFFICULTY_LABELS, ROLE_LABELS } from "../lib/dd.js";
  import Avatar from "../components/Avatar.svelte";

  let { params } = $props();
  const profile = api.profile(params.id);
  const tables = [["by_role", "Par rôle", ROLE_LABELS], ["by_difficulty", "Par difficulté", DIFFICULTY_LABELS]];
</script>

{#await profile then p}
  <header>
    <Avatar user={p.user} size={64} />
    <h1>{p.user.name}</h1>
    <p><span class="num big">{p.total_points}</span> points</p>
  </header>

  <div class="tables">
    {#each tables as [key, title, labels]}
      <table>
        <caption>{title}</caption>
        <thead><tr><th></th><th>Faits</th><th>Excellents</th><th>Points</th></tr></thead>
        <tbody>
          {#each Object.entries(labels) as [k, label]}
            {@const s = p[key][k]}
            <tr class:empty={!s.answered}>
              <th scope="row">{label}</th>
              <td class="num">{s.answered}</td>
              <td class="num">{s.excellent}</td>
              <td class="num">{s.points}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/each}
  </div>
{:catch e}
  <p class="grade-erreur">{e.status === 404 ? "Ce joueur n'existe pas." : e.message}</p>
{/await}

<style>
  header { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 2rem; }
  h1 { margin: 0 auto 0 0; }
  header p { margin: 0; color: var(--mist); }
  .big { font-size: 2.4rem; color: var(--foam); margin-right: 0.3rem; }
  .tables { display: grid; grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr)); gap: 2rem; }
  table { width: 100%; border-collapse: collapse; }
  caption { font: 700 1.3rem var(--display); text-align: left; margin-bottom: 0.5rem; }
  th, td { padding: 0.5rem; border-bottom: 1px solid var(--reed); text-align: right; }
  th:first-child { text-align: left; }
  thead th { color: var(--mist); font-weight: 400; font-size: 0.85rem; }
  td { font-size: 1.15rem; }
  .empty { color: var(--mist); }
</style>
