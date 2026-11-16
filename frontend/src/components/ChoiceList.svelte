<script>
  import ItemIcons from "./ItemIcons.svelte";

  let { choices, disabled = false, onchoose } = $props();

  function onkeydown(e) {
    const i = Number(e.key) - 1;
    if (!disabled && choices[i] && !e.target.closest("input, textarea")) onchoose(choices[i].id);
  }
</script>

<svelte:window {onkeydown} />

<ol class="choices">
  {#each choices as c, i}
    <li>
      <button class="quiet" {disabled} onclick={() => onchoose(c.id)}>
        <kbd class="num">{i + 1}</kbd>
        <span>{c.text}</span>
        <ItemIcons items={c.items} size={28} />
      </button>
    </li>
  {/each}
</ol>

<style>
  .choices { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.5rem; }
  button { width: 100%; display: flex; align-items: center; gap: 0.9rem; text-align: left; padding: 0.85rem 1rem; }
  button:not(:disabled):hover { box-shadow: inset 0 0 0 1px var(--foam); }
  kbd { font-size: 1.1rem; color: var(--mist); min-width: 1ch; }
  span { flex: 1; }
</style>
