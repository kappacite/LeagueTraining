<script>
  import { onMount } from "svelte";
  import { fade } from "svelte/transition";
  import { api } from "./lib/api.js";
  import { href, route } from "./lib/router.js";
  import { meta, user } from "./lib/stores.js";
  import Avatar from "./components/Avatar.svelte";
  import HextechBackground from "./components/HextechBackground.svelte";
  import Home from "./pages/Home.svelte";
  import List from "./pages/List.svelte";
  import Puzzle from "./pages/Puzzle.svelte";
  import Leaderboard from "./pages/Leaderboard.svelte";
  import Profile from "./pages/Profile.svelte";
  import Login from "./pages/Login.svelte";

  const pages = { home: Home, list: List, puzzle: Puzzle, leaderboard: Leaderboard, profile: Profile };
  const tabs = [
    { page: "home", label: "Accueil", icon: "M12 3 3 10h2v10h5v-6h4v6h5V10h2z" },
    { page: "list", label: "Entraînement", icon: "M14.5 3 21 9.5l-9 9-3-3-3 3H4v-2l3-3-3-3 9-9 1.5 1.5zM13 6l-6 6 1.5 1.5 6-6z" },
    { page: "leaderboard", label: "Classement", icon: "M5 4h14v3a5 5 0 0 1-4 4.9V14h2v3H7v-3h2v-2.1A5 5 0 0 1 5 7zm2 2v1a3 3 0 0 0 3 3h4a3 3 0 0 0 3-3V6zM6 19h12v2H6z" },
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

<HextechBackground />

{#if $user === undefined}
  <p class="loading muted">Chargement…</p>
{:else if $user === null || $route.page === "login"}
  <Login query={$route.query} />
{:else}
  <header>
    <a class="brand" href={href("home")}>
      <span class="diamond"></span>
      <span>League<b>Training</b></span>
    </a>
    <nav aria-label="Navigation principale">
      {#each tabs as t}
        <a href={href(t.page)} aria-current={activeTab === t.page ? "page" : undefined}>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d={t.icon} /></svg>
          {t.label}
        </a>
      {/each}
    </nav>
    <div class="account">
      <a class="me" href={href("profile", { id: $user.id })} aria-label="Mon profil" title="Mon profil">
        <Avatar user={$user} size={34} />
        <span class="name">{$user.name}</span>
      </a>
      <button class="quiet logout" onclick={logout}>Déconnexion</button>
    </div>
  </header>
  <main>
    {#key $route.page + JSON.stringify($route.params) + JSON.stringify($route.query)}
      <div in:fade={{ duration: 350 }}>
        <Page params={$route.params} query={$route.query} />
      </div>
    {/key}
  </main>
  <footer>
    <div class="ornament"><span></span></div>
    <p class="muted">Données Data Dragon {$meta.ddragon_version}. Projet de fans, non affilié à Riot Games.</p>
  </footer>
{/if}

<style>
  header {
    position: sticky; top: 0; z-index: 10;
    display: flex; align-items: stretch; gap: 2rem;
    padding: 0 1.5rem; height: 64px;
    background: linear-gradient(180deg, rgba(1, 10, 19, 0.96), rgba(10, 20, 40, 0.92));
    border-bottom: 1px solid var(--lol-gold-deep);
    box-shadow: 0 1px 0 rgba(200, 170, 110, 0.15), 0 8px 24px rgba(0, 0, 0, 0.5);
  }
  .brand {
    display: flex; align-items: center; gap: 0.7rem;
    font: 600 1.15rem var(--font-display); letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--lol-gold); text-decoration: none;
  }
  .brand b { color: var(--lol-gold-bright); font-weight: 700; }
  nav { display: flex; align-items: stretch; }
  nav a {
    position: relative; display: flex; align-items: center; gap: 0.5rem;
    padding: 0 1.25rem;
    font: 700 0.8rem var(--font-body); letter-spacing: 0.12em; text-transform: uppercase;
    color: var(--lol-text-secondary); text-decoration: none;
    transition: color 200ms;
  }
  nav a + a { border-left: 1px solid; border-image: linear-gradient(180deg, transparent 25%, var(--lol-gold-deep) 50%, transparent 75%) 1; }
  nav svg { width: 16px; height: 16px; fill: currentColor; opacity: 0.8; }
  nav a::after {
    content: ""; position: absolute; left: 20%; right: 20%; bottom: -1px; height: 2px;
    background: linear-gradient(90deg, transparent, var(--lol-gold-bright), transparent);
    box-shadow: 0 0 10px var(--lol-gold);
    transform: scaleX(0); transition: transform 250ms var(--ease);
  }
  nav a:hover { color: var(--lol-gold-bright); }
  nav a[aria-current="page"] { color: var(--lol-gold-bright); }
  nav a[aria-current="page"]::after { transform: scaleX(1); }
  .account { margin-left: auto; display: flex; align-items: center; gap: 1rem; }
  .me { display: flex; align-items: center; gap: 0.6rem; color: var(--lol-gold-bright); text-decoration: none; font-weight: 600; }
  .logout { padding: 0.6em 1em; font-size: 0.7rem; }
  main { max-width: 74rem; margin: 0 auto; padding: 2.5rem 1.5rem 3rem; }
  footer { text-align: center; padding: 0 1.5rem 2rem; font-size: 0.8rem; }
  footer .ornament { max-width: 30rem; margin: 0 auto 0.75rem; }
  footer p { margin: 0 auto; }
  .loading { text-align: center; margin-top: 30vh; font-family: var(--font-display); letter-spacing: 0.1em; }

  @media (max-width: 52rem) {
    header { height: auto; flex-wrap: wrap; gap: 0; padding: 0.5rem 1rem 0; }
    .brand { padding: 0.4rem 0; }
    .account { gap: 0.5rem; }
    .name { display: none; }
    nav { order: 3; width: 100%; justify-content: space-between; border-top: 1px solid var(--lol-gold-deep); margin-top: 0.4rem; }
    nav a { padding: 0.75rem 0.5rem; font-size: 0.7rem; letter-spacing: 0.08em; flex: 1; justify-content: center; }
    nav svg { display: none; }
    main { padding: 1.5rem 1rem 2rem; }
  }
</style>
