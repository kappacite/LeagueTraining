<script>
  import { ddImg } from "../lib/dd.js";
  let { items = [], size = 32 } = $props();
</script>

{#if items.length}
  <span class="items">
    {#each items as id}
      <img src={ddImg("item", id)} alt="Objet {id}" width={size} height={size} loading="lazy" />
    {/each}
  </span>
{/if}

<style>
  .items { display: inline-flex; gap: 3px; vertical-align: middle; }
  img { border-radius: 3px; box-shadow: 0 0 0 1px var(--reed); }
</style>
