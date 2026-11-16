<script>
  // Original line glyphs for the five positions (not Riot's icons).
  let { role, size = 20 } = $props();
  const PATHS = {
    top: "M4 4h12v3H7v9H4zM10 10h4v4h-4z",
    jungle: "M12 3c3 3 4 6 3 10l3-2c0 4-3 8-6 10-3-2-6-6-6-10l3 2c-1-4 0-7 3-10z",
    mid: "M4 17 17 4h3v3L7 20H4zM4 4h6v3H7v3H4zM20 20h-6v-3h3v-3h3z",
    adc: "M20 20H8v-3h9V8h3zM10 10h4v4h-4z",
    support: "M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7zm0 4-4 2v3c0 3 2 5 4 6 2-1 4-3 4-6V9z",
  };
</script>

<svg class="role" viewBox="0 0 24 24" width={size} height={size} aria-hidden="true"><path d={PATHS[role]} /></svg>

<style>
  .role { fill: currentColor; flex: none; }
</style>
