<script>
  let { query } = $props();
  const errors = {
    "not-allowed": "Ton compte Discord n'est pas sur la liste. Demande à l'admin de t'ajouter.",
    discord: "Discord n'a pas répondu. Réessaie dans un instant.",
  };
</script>

<main>
  <h1>LeagueTraining</h1>
  <p class="muted">Des situations de jeu figées. Tu choisis, on t'explique, et tu compares avec tes potes.</p>
  {#if errors[query.error]}
    <p class="error" role="alert">{errors[query.error]}</p>
  {/if}
  <a class="button" href="/api/auth/login">Se connecter avec Discord</a>
</main>

<style>
  main { max-width: 34rem; margin: 18vh auto 0; padding: 0 1.5rem; }
  h1 { font-size: clamp(3rem, 10vw, 5rem); letter-spacing: -0.01em; }
  .error { color: var(--erreur); }
</style>
