<script>
  let { user, size = 28 } = $props();
</script>

{#if user.avatar_url}
  <img class="avatar" src={user.avatar_url} alt={user.name} title={user.name} width={size} height={size}
       style:width="{size}px" style:height="{size}px" />
{:else}
  <span class="avatar initial" title={user.name} style:width="{size}px" style:height="{size}px">
    {user.name.slice(0, 1).toUpperCase()}
  </span>
{/if}
