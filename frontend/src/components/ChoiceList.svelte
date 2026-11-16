<script>
  import ItemIcons from "./ItemIcons.svelte";

  let { choices, disabled = false, onchoose } = $props();

  function onkeydown(e) {
    const i = Number(e.key) - 1;
    if (!disabled && choices[i] && !e.target.closest("input, textarea, select")) onchoose(choices[i].id);
  }
</script>

<svelte:window {onkeydown} />

<ol class="choices">
  {#each choices as c, i}
    <li>
      <button class="choice" {disabled} onclick={() => onchoose(c.id)}>
        <span class="key"><span class="num">{i + 1}</span></span>
        <span class="text">{c.text}</span>
        <ItemIcons items={c.items} size={30} />
      </button>
    </li>
  {/each}
</ol>

<style>
  .choices { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.6rem; }
  .choice {
    width: 100%; justify-content: flex-start; gap: 1.1rem; padding: 0.9rem 1.1rem;
    text-align: left; text-transform: none; letter-spacing: 0.01em;
    font: 600 1rem/1.35 var(--font-body); color: var(--lol-text);
    border-image: var(--metal-soft) 1;
    background: linear-gradient(90deg, rgba(10, 20, 40, 0.95), rgba(1, 10, 19, 0.85));
    box-shadow: none;
  }
  .choice:hover:not(:disabled) {
    color: var(--lol-gold-bright);
    border-image: var(--metal) 1;
    background: linear-gradient(90deg, rgba(11, 196, 226, 0.12), rgba(10, 20, 40, 0.95) 45%);
    box-shadow: 0 0 16px rgba(11, 196, 226, 0.15);
  }
  /* Diamond key cap with an upright number. */
  .key {
    flex: none; display: grid; place-items: center; width: 26px; height: 26px; margin: 0 2px;
    border: 1px solid var(--lol-gold-dark); background: var(--lol-black);
    transform: rotate(45deg); transition: border-color 200ms, box-shadow 200ms;
  }
  .key .num { transform: rotate(-45deg); font-size: 0.85rem; color: var(--lol-gold); }
  .choice:hover:not(:disabled) .key { border-color: var(--lol-hextech); box-shadow: 0 0 8px rgba(11, 196, 226, 0.5); }
  .text { flex: 1; }
</style>
