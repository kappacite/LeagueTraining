<script>
  let { query } = $props();
  const errors = {
    "not-allowed": "Ton compte Discord n'est pas sur la liste. Demande à l'admin de t'ajouter.",
    discord: "Discord n'a pas répondu. Réessaie dans un instant.",
  };
</script>

<main>
  <section class="panel major rise">
    <h1>League<br />Training</h1>
    <div class="ornament"><span></span></div>
    <p class="pitch">Des situations de jeu figées. Tu choisis, on t'explique, et tu compares avec tes potes.</p>
    {#if errors[query.error]}
      <p class="error" role="alert">{errors[query.error]}</p>
    {/if}
    <a class="button hextech" href="/api/auth/login">Se connecter avec Discord</a>
  </section>
  <p class="legal muted">Projet de fans, non affilié à Riot Games.</p>
</main>

<style>
  main { min-height: 100vh; display: grid; place-content: center; padding: 1.5rem; gap: 1.25rem; }
  section { width: min(30rem, 100%); text-align: center; padding: 3rem 2.5rem; }
  h1 { font-size: clamp(2.6rem, 9vw, 3.8rem); letter-spacing: 0.08em; margin: 0; }
  .ornament { margin: 1.5rem 2rem; }
  .pitch { margin: 0 auto 2rem; color: var(--lol-text-secondary); }
  .error { color: #e07a7a; border: 1px solid rgba(196, 63, 63, 0.5); background: rgba(196, 63, 63, 0.1); padding: 0.6rem 0.9rem; margin: 0 auto 1.5rem; }
  .button { width: 100%; padding: 1.15em; font-size: 0.9rem; }
  .legal { text-align: center; font-size: 0.8rem; margin: 0 auto; }
</style>
