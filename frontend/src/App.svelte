<script>
  import { onMount } from "svelte";
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
</script>

{#if $user === undefined}
  <p class="loading muted">Chargement…</p>
{:else if $user === null || $route.page === "login"}
  <Login query={$route.query} />
{:else}
  <header>
    <a class="brand" href={href("home")}>LeagueTraining</a>
    <nav>
      <a href={href("list")} aria-current={$route.page === "list" ? "page" : undefined}>Puzzles</a>
      <a href={href("leaderboard")} aria-current={$route.page === "leaderboard" ? "page" : undefined}>Classement</a>
    </nav>
    <a class="me" href={href("profile", { id: $user.id })} aria-label="Mon profil"><Avatar user={$user} /></a>
    <button class="quiet" onclick={logout}>Déconnexion</button>
  </header>
  <main>
    {#key $route.page + JSON.stringify($route.params)}
      <Page params={$route.params} query={$route.query} />
    {/key}
  </main>
  <footer class="muted">Données Data Dragon {$meta.ddragon_version}. Projet de fans, non affilié à Riot Games.</footer>
{/if}

<style>
  header {
    display: flex; align-items: center; gap: 1.25rem;
    padding: 0.75rem 1.5rem; border-bottom: 1px solid var(--reed);
  }
  .brand { font: 700 1.4rem var(--display); color: var(--foam); text-decoration: none; margin-right: auto; }
  nav { display: flex; gap: 1.25rem; }
  nav a { color: var(--mist); text-decoration: none; font-weight: 600; }
  nav a[aria-current="page"], nav a:hover { color: var(--foam); }
  .me { display: flex; }
  main { max-width: 72rem; margin: 0 auto; padding: 2rem 1.5rem 4rem; }
  footer { font-size: 0.8rem; text-align: center; padding: 2rem 1rem; }
  .loading { text-align: center; margin-top: 30vh; }
  @media (max-width: 40rem) {
    header { flex-wrap: wrap; gap: 0.75rem; }
    nav { order: 3; width: 100%; }
  }
</style>
