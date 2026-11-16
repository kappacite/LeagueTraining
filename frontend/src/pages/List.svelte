<script>
  import { api } from "../lib/api.js";
  import { DIFFICULTY_LABELS, GRADE_LABELS, ROLE_LABELS, TYPE_LABELS } from "../lib/dd.js";
  import { href } from "../lib/router.js";
  import DifficultyBadge from "../components/DifficultyBadge.svelte";
  import RoleIcon from "../components/RoleIcon.svelte";

  let { query } = $props();
  const filters = { role: query.role ?? "", difficulty: query.difficulty ?? "", type: query.type ?? "" };
  const groups = [
    ["role", "Tous les rôles", ROLE_LABELS],
    ["difficulty", "Difficulté", DIFFICULTY_LABELS],
    ["type", "Type", TYPE_LABELS],
  ];

  let puzzles = $state(null);
  let error = $state("");
  let search = $state("");
  let selectedId = $state(null);
  api.puzzles(filters).then((list) => {
    puzzles = list;
    selectedId = list[0]?.id ?? null;
  }).catch((e) => (error = e.message));

  // Filters live in the URL so a reload or a shared link keeps them.
  function set(key, value) {
    location.hash = href("list", {}, { ...filters, [key]: value });
  }

  const shown = $derived((puzzles ?? []).filter((p) => p.title.toLowerCase().includes(search.trim().toLowerCase())));
  const selected = $derived(shown.find((p) => p.id === selectedId) ?? shown[0]);
  const roles = $derived(new Set((puzzles ?? []).map((p) => p.role)).size);
  const narrow = matchMedia("(max-width: 1040px)");

  function pick(e, p) {
    if (narrow.matches) return; // small screens: the row link opens the puzzle directly
    e.preventDefault();
    selectedId = p.id;
  }
  const statusClass = (p) => (!p.done ? "" : p.grade === "erreur" ? "error" : "success");
</script>

<p class="eyebrow">Centre d'entraînement</p>
<div class="heading">
  <div>
    <h1>Entraînement</h1>
    <p class="subtitle">Travaille tes décisions sur des situations de jeu, puis compare-toi à tes potes.</p>
  </div>
  {#if puzzles}
    <div class="heading-side">
      <b>{puzzles.length} exercice{puzzles.length > 1 ? "s" : ""}</b><span class="dot"></span>
      {roles} rôle{roles > 1 ? "s" : ""} disponible{roles > 1 ? "s" : ""}
    </div>
  {/if}
</div>

<div class="workspace">
  <section class="left">
    <div class="toolbar">
      <label class="search">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 5 5" /></svg>
        <input bind:value={search} placeholder="Rechercher un exercice" aria-label="Rechercher un exercice" />
      </label>
      {#each groups as [key, label, options]}
        <select class="filter" value={filters[key]} aria-label={label} onchange={(e) => set(key, e.currentTarget.value)}>
          <option value="">{label}</option>
          {#each Object.entries(options) as [value, text]}<option {value}>{text}</option>{/each}
        </select>
      {/each}
    </div>

    <div class="section-label"><span class="label">Exercices disponibles</span><span class="count">{shown.length} résultat{shown.length > 1 ? "s" : ""}</span></div>

    {#if error}
      <p class="grade-erreur">{error}</p>
    {:else if puzzles && !shown.length}
      <p class="muted empty">Aucun exercice ne correspond. Retire un filtre ou change ta recherche.</p>
    {:else if puzzles}
      <div class="list">
        {#each shown as p (p.id)}
          <a href={href("puzzle", { id: p.id })} class="exercise" class:selected={selected?.id === p.id}
             aria-current={selected?.id === p.id ? "true" : undefined} onclick={(e) => pick(e, p)}>
            <span class="ex-icon"><RoleIcon role={p.role} size={18} /></span>
            <span class="ex-details">
              <span class="ex-title">{p.title}</span>
              <span class="ex-sub"><DifficultyBadge difficulty={p.difficulty} /><span class="dot"></span>{ROLE_LABELS[p.role]} · {TYPE_LABELS[p.type]}</span>
            </span>
            <span class="status {statusClass(p)}">{p.done ? GRADE_LABELS[p.grade] : "À relever"}</span>
            <span class="row-arrow" aria-hidden="true">›</span>
          </a>
        {/each}
      </div>
    {/if}
  </section>

  {#if selected}
    <aside class="detail" aria-label="Aperçu de l'exercice sélectionné">
      <div class="detail-head">
        <span>Aperçu de l'exercice</span>
        <span>{String(shown.indexOf(selected) + 1).padStart(2, "0")} / {String(shown.length).padStart(2, "0")}</span>
      </div>
      <div class="detail-body">
        <div class="detail-kicker">{selected.type === "scene" ? "Scène animée" : "Situation de jeu"}</div>
        <h2>{selected.title}</h2>
        <div class="chips">
          <span class="chip">{ROLE_LABELS[selected.role]}</span>
          <span class="chip">{TYPE_LABELS[selected.type]}</span>
          <span class="chip {selected.difficulty}">{DIFFICULTY_LABELS[selected.difficulty]}</span>
          {#if selected.stale}<span class="chip stale">Patch ancien</span>{/if}
        </div>
        <div class="rule"></div>
        <div class="content-label">Contexte</div>
        <p class="desc">{selected.context}</p>
        <div class="meta">
          <div><small>Rôle</small><strong>{ROLE_LABELS[selected.role]}</strong></div>
          <div><small>Compétence</small><strong>{TYPE_LABELS[selected.type]}</strong></div>
        </div>
        <a class="button start" href={href("puzzle", { id: selected.id })}>
          {selected.done ? "Rejouer l'exercice" : "Commencer l'exercice"}
        </a>
        <div class="small-note">
          {#if selected.done}Ta note : <span class="grade-{selected.grade}">{GRADE_LABELS[selected.grade]}</span>. Rejouer ne rapporte pas de points.
          {:else if selected.type === "scene"}Plusieurs décisions qui s'enchaînent.{:else}Une situation, une décision.{/if}
        </div>
      </div>
    </aside>
  {/if}
</div>

<style>
  .heading { display: flex; justify-content: space-between; align-items: end; gap: 1rem; margin-bottom: 35px; }
  h1 { margin: 0; }
  .subtitle { color: #a3adb5; margin: 11px 0 0; }
  .heading-side { display: flex; align-items: center; gap: 12px; color: #8e9ca9; padding-bottom: 5px; font-size: 13px; white-space: nowrap; }
  .heading-side b { font-weight: 600; color: #ddd9c9; }

  .workspace { display: grid; grid-template-columns: minmax(0, 1.75fr) minmax(320px, 1fr); gap: 22px; align-items: start; }
  .left { min-width: 0; }
  .toolbar { display: flex; gap: 10px; align-items: center; margin-bottom: 17px; }
  .search { flex: 1; min-width: 120px; display: flex; align-items: center; gap: 12px; height: 42px; padding: 0 14px; color: #8593a0; background: #0c1926; border: 1px solid #27394a; }
  .search:focus-within { border-color: var(--lol-gold-dark); }
  .search input { height: 100%; border: 0; padding: 0; background: transparent; color: #eee; width: 100%; }
  .search input:focus { border: 0; }
  .search input::placeholder { color: #81909e; }
  .filter { flex: 0 0 128px; }

  .section-label { display: flex; align-items: center; justify-content: space-between; margin: 0 0 11px; }
  .count { font-size: 12px; color: #68798a; }
  .empty { padding: 2rem 0; }
  .list { border: 1px solid #1a2938; background: rgba(8, 18, 28, 0.75); }
  .exercise {
    position: relative; display: flex; align-items: center; gap: 16px; padding: 0 19px; height: 77px;
    border-bottom: 1px solid #223040; color: inherit; text-decoration: none;
    background: rgba(12, 26, 39, 0.27); transition: background 160ms ease;
  }
  .exercise:last-child { border-bottom: 0; }
  .exercise:hover { background: #132638; }
  .exercise.selected { background: linear-gradient(90deg, #142f3b 0%, #102331 59%, #0d1c2a 100%); }
  .exercise.selected::before { content: ""; position: absolute; width: 2px; top: 0; bottom: 0; left: -1px; background: #c5a465; }
  .ex-icon { height: 38px; width: 38px; flex-shrink: 0; display: grid; place-items: center; border: 1px solid #344456; color: #a6b1b6; }
  .exercise.selected .ex-icon { color: #e6cc93; border-color: #716649; background: rgba(202, 165, 99, 0.05); }
  .ex-details { min-width: 0; flex: 1; display: grid; }
  .ex-title { font-weight: 600; color: #e9e9e6; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .ex-sub { margin-top: 5px; display: flex; align-items: center; gap: 9px; color: #82919e; font-size: 12px; white-space: nowrap; }
  .status { margin-left: auto; font-size: 10px; font-weight: 700; letter-spacing: 0.07em; color: #8e9ba6; text-transform: uppercase; white-space: nowrap; }
  .status.success { color: #60bcb6; }
  .status.error { color: #c68f87; }
  .row-arrow { color: #526677; margin-left: 6px; }
  .exercise.selected .row-arrow { color: #c1a46d; }

  .detail { position: sticky; top: 90px; overflow: hidden; background: var(--panel-bg); border: 1px solid #29394a; }
  .detail::before {
    content: ""; position: absolute; right: -160px; top: -230px; width: 410px; height: 410px; pointer-events: none;
    border: 1px solid rgba(139, 173, 179, 0.06); border-radius: 50%;
    box-shadow: 0 0 0 55px rgba(105, 143, 163, 0.017), 0 0 0 115px rgba(105, 143, 163, 0.012);
  }
  .detail::after { content: ""; position: absolute; left: 0; right: 0; top: 0; height: 2px; opacity: 0.9; background: linear-gradient(90deg, #b79960 0%, #a68e5a 29%, transparent 75%); }
  .detail-head { padding: 24px 27px 0; display: flex; justify-content: space-between; align-items: center; color: #a6b5c0; font-size: 11px; letter-spacing: 0.12em; font-weight: 700; text-transform: uppercase; }
  .detail-head span:last-child { color: #647e90; font-weight: 500; letter-spacing: 0.02em; }
  .detail-body { position: relative; z-index: 1; padding: 37px 27px 28px; }
  .detail-kicker { font-size: 11px; color: #c6ad77; font-weight: 700; letter-spacing: 0.09em; text-transform: uppercase; margin-bottom: 15px; }
  h2 { font-size: 30px; line-height: 1.17; color: #efe8d9; margin: 0 0 20px; }
  .chips { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 30px; }
  .chip { font-size: 11px; padding: 5px 9px; border: 1px solid #344456; color: #a7b6c3; background: #101f2c; }
  .chip.facile { border-color: #245259; color: #5cccc8; }
  .chip.moyen { border-color: #5e533f; color: #cfb47a; }
  .chip.difficile { border-color: #5a3434; color: #d37a74; }
  .chip.stale { border-color: #5e533f; color: #c6ad77; }
  .rule { height: 1px; background: linear-gradient(90deg, #5e533f, rgba(62, 79, 91, 0.6), transparent); margin-bottom: 27px; }
  .content-label { font-size: 10px; color: #8d9ba7; text-transform: uppercase; letter-spacing: 0.14em; font-weight: 700; margin-bottom: 14px; }
  .desc { font-size: 15px; color: #c1cad2; line-height: 1.72; margin: 0 0 36px; }
  .meta { display: grid; grid-template-columns: 1fr 1fr; margin: 0 0 33px; padding: 18px 0; border-top: 1px solid #293947; border-bottom: 1px solid #293947; }
  .meta > div + div { border-left: 1px solid #293947; padding-left: 20px; }
  .meta small { display: block; color: #7e8f9c; font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 7px; }
  .meta strong { font-size: 13px; font-weight: 600; color: #d8dad8; }
  .start { width: 100%; height: 47px; }
  .small-note { margin-top: 17px; color: #8193a1; font-size: 12px; text-align: center; }

  @media (max-width: 1040px) {
    .workspace { grid-template-columns: 1fr; }
    .detail { display: none; } /* rows open the puzzle directly */
  }
  @media (max-width: 680px) {
    .heading { display: block; margin-bottom: 25px; }
    .heading-side { margin-top: 20px; }
    .toolbar { flex-wrap: wrap; }
    .search { flex-basis: 100%; }
    .filter { flex: 1 1 29%; font-size: 12px; min-width: 0; }
    .exercise { padding: 0 11px; gap: 10px; }
    .status { font-size: 9px; }
    .row-arrow { display: none; }
    .ex-icon { height: 32px; width: 32px; }
  }
</style>
