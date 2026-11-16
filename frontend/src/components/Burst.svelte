<script>
  // One-shot gold/turquoise particle burst with a brief Hextech flash (≈ 900 ms). Skipped with reduced motion.
  import { onMount } from "svelte";

  let canvas;
  let show = $state(true);

  onMount(() => {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return (show = false);
    const ctx = canvas.getContext("2d");
    const w = (canvas.width = canvas.offsetWidth * 2);
    const h = (canvas.height = canvas.offsetHeight * 2);
    const colors = ["240,230,210", "200,170,110", "11,196,226", "89,193,222"];
    const parts = Array.from({ length: 70 }, () => {
      const a = Math.random() * Math.PI * 2;
      const v = 4 + Math.random() * 9;
      return { x: w / 2, y: h * 0.45, vx: Math.cos(a) * v, vy: Math.sin(a) * v - 3, r: 1.5 + Math.random() * 3, c: colors[(Math.random() * 4) | 0] };
    });
    const start = performance.now();
    let raf;
    function frame(now) {
      const k = (now - start) / 900;
      if (k >= 1) return (show = false);
      ctx.clearRect(0, 0, w, h);
      for (const p of parts) {
        p.x += p.vx; p.y += p.vy; p.vy += 0.25; p.vx *= 0.97;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${p.c},${1 - k})`;
        ctx.shadowColor = `rgba(${p.c},1)`;
        ctx.shadowBlur = 10;
        ctx.fill();
      }
      raf = requestAnimationFrame(frame);
    }
    raf = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(raf);
  });
</script>

{#if show}
  <div class="burst" aria-hidden="true">
    <div class="flash"></div>
    <canvas bind:this={canvas}></canvas>
  </div>
{/if}

<style>
  .burst { position: absolute; inset: -40px; pointer-events: none; z-index: 2; }
  canvas { width: 100%; height: 100%; }
  .flash {
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at 50% 40%, rgba(11, 196, 226, 0.35), rgba(200, 170, 110, 0.12) 40%, transparent 70%);
    animation: flash 700ms ease-out both;
  }
  @keyframes flash { from { opacity: 1; transform: scale(0.9); } to { opacity: 0; transform: scale(1.1); } }
</style>
