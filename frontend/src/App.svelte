<script>
  import { onMount } from "svelte";
  import { fade } from "svelte/transition";
  import { api } from "./lib/api.js";
  import { href, route } from "./lib/router.js";
  import { meta, user } from "./lib/stores.js";
  import Avatar from "./components/Avatar.svelte";
  import Home from "./pages/Home.svelte";
  import List from "./pages/List.svelte";
  import Puzzle from "./pages/Puzzle.svelte";
  import Leaderboard from "./pages/Leaderboard.svelte";
  import Profile from "./pages/Profile.svelte";
  import Login from "./pages/Login.svelte";

  const pages = { home: Home, list: List, puzzle: Puzzle, leaderboard: Leaderboard, profile: Profile };
  const tabs = [
    { page: "home", label: "Accueil", icon: "m12 3-9 8h2v10h6v-6h3v6h6V11h2z" },
    { page: "list", label: "Entraînement", icon: "m6.1 2 3.1 5.4L7.5 9 3 6.5V4L6.1 2ZM18 2l3 2v2.5L16.5 9l-1.7-1.6L18 2ZM12 9.8l6.7 6.7-2.2 2.2L9.8 12zm-2.2 2.1L3.3 18.4 5.6 21l6.5-6.6z" },
    { page: "leaderboard", label: "Classement", icon: "M7 3h10v3h4v3c0 3-2 5-5 5-.6 1.5-1.7 2.5-3 2.8V20h4v2H7v-2h4v-3.2c-1.3-.3-2.4-1.3-3-2.8-3 0-5-2-5-5V6h4V3Zm0 5H5v1c0 1.5.7 2.4 2 2.8V8Zm10 0v3.8c1.3-.4 2-1.3 2-2.8V8h-2Z" },
  ];

  onMount(async () => {
    api.meta().then(meta.set).catch(() => {});
    try {
      user.set(await api.me());
    } catch {
      user.set(null);
    }
  });

  async function logout() {
    await api.logout().catch(() => {});
    user.set(null);
  }

  const Page = $derived(pages[$route.page] ?? Home);
  const activeTab = $derived($route.page === "puzzle" ? "list" : $route.page);
</script>

{#if $user === undefined}
  <p class="loading muted">Chargement…</p>
{:else if $user === null || $route.page === "login"}
  <Login query={$route.query} />
{:else}
  <header>
    <a class="brand" href={href("home")}>
      <span class="brand-mark">L</span>
      <span class="brand-name">League<span>Training</span></span>
    </a>
    <nav aria-label="Navigation principale">
      {#each tabs as t}
        <a class="navitem" href={href(t.page)} aria-current={activeTab === t.page ? "page" : undefined}>
          <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true"><path d={t.icon} /></svg>
          <span>{t.label}</span>
        </a>
      {/each}
    </nav>
    <div class="user">
      <a class="me" href={href("profile", { id: $user.id })} aria-label="Mon profil">
        <Avatar user={$user} size={31} />
        <span class="name">{$user.name}</span>
      </a>
      <button class="quiet logout" onclick={logout}>Déconnexion</button>
    </div>
  </header>
  <main>
    {#key $route.page + JSON.stringify($route.params) + JSON.stringify($route.query)}
      <div in:fade={{ duration: 250 }}>
        <Page params={$route.params} query={$route.query} />
      </div>
    {/key}
  </main>
  <footer>
    <span>Données Data Dragon {$meta.ddragon_version}</span>
    <span>Projet de fans, non affilié à Riot Games.</span>
  </footer>
{/if}

<style>
  header {
    position: sticky; top: 0; z-index: 10;
    height: 69px; display: flex; align-items: center; gap: 53px; padding: 0 56px;
    background: rgba(6, 13, 22, 0.97); border-bottom: 1px solid #283440;
  }
  .brand { display: flex; align-items: center; gap: 13px; color: #e8d5a6; text-decoration: none; white-space: nowrap; }
  .brand-mark {
    position: relative; padding-right: 7px; font: 32px/1 var(--font-display); color: #d5b876;
    text-shadow: 0 0 11px rgba(184, 152, 86, 0.19);
  }
  .brand-mark::after { content: ""; position: absolute; left: 3px; bottom: -1px; width: 19px; height: 1px; background: #b79d68; }
  .brand-name { font: small-caps 21px/1 var(--font-display); letter-spacing: 0.06em; }
  .brand-name span { color: #b9c1c9; }
  nav { display: flex; height: 100%; gap: 6px; align-items: stretch; }
  .navitem {
    position: relative; display: flex; align-items: center; gap: 10px; padding: 0 21px;
    color: #939ba3; text-decoration: none; font-weight: 600; letter-spacing: 0.015em;
  }
  .navitem svg { fill: currentColor; opacity: 0.77; }
  .navitem:hover { color: #ece8db; }
  .navitem[aria-current="page"] { color: #f0ede7; }
  .navitem[aria-current="page"]::after {
    content: ""; position: absolute; bottom: 0; left: 20px; right: 20px; height: 2px;
    background: var(--lol-gold); box-shadow: 0 -1px 8px rgba(202, 171, 100, 0.2);
  }
  .navitem[aria-current="page"] svg { color: var(--lol-gold); opacity: 1; }
  .user { margin-left: auto; display: flex; align-items: center; gap: 13px; white-space: nowrap; }
  .me { display: flex; align-items: center; gap: 13px; color: #dfdfe0; font-weight: 600; text-decoration: none; }
  .logout { height: 34px; padding: 0 0.9em; font-size: 11px; }
  main { max-width: 1336px; margin: 0 auto; padding: 53px 22px 66px; }
  footer {
    max-width: 1336px; margin: 0 auto; padding: 0 22px 28px;
    display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap; font-size: 11px; color: #596c7a;
  }
  .loading { text-align: center; margin-top: 30vh; }

  @media (max-width: 1040px) {
    header { padding: 0 24px; gap: 20px; }
    .brand-name { font-size: 17px; }
    .navitem { padding: 0 11px; }
    main { padding: 34px 24px; }
  }
  @media (max-width: 680px) {
    header { height: 61px; padding: 0 17px; gap: 12px; }
    .brand-name { font-size: 15px; }
    nav { gap: 0; }
    .navitem { padding: 0 9px; }
    .navitem span { display: none; }
    .name { display: none; }
    main { padding: 28px 14px; }
  }
</style>
