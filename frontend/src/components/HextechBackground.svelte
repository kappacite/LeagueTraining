<script>
  // Global animated backdrop: drifting turquoise halos and slow particles on Canvas 2D.
  // Paused when the tab is hidden; static (no particles) with prefers-reduced-motion.
  import { onMount } from "svelte";

  let canvas;

  onMount(() => {
    const ctx = canvas.getContext("2d");
    const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const count = reduce ? 0 : innerWidth < 700 ? 20 : 60;
    let w, h, raf, particles;

    function resize() {
      const dpr = Math.min(devicePixelRatio || 1, 2);
      w = canvas.width = innerWidth * dpr;
      h = canvas.height = innerHeight * dpr;
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * w, y: Math.random() * h,
        r: (0.6 + Math.random() * 1.6) * dpr,
        vy: -(0.05 + Math.random() * 0.18) * dpr,
        vx: (Math.random() - 0.5) * 0.08 * dpr,
        a: 0.15 + Math.random() * 0.5,
        phase: Math.random() * Math.PI * 2,
      }));
    }

    function halo(x, y, radius, alpha) {
      const g = ctx.createRadialGradient(x, y, 0, x, y, radius);
      g.addColorStop(0, `rgba(11, 196, 226, ${alpha})`);
      g.addColorStop(1, "rgba(11, 196, 226, 0)");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, w, h);
    }

    function draw(time = 0) {
      const t = time / 1000;
      ctx.clearRect(0, 0, w, h);
      halo(w * (0.22 + 0.04 * Math.sin(t / 23)), h * (0.18 + 0.03 * Math.cos(t / 31)), w * 0.38, 0.07);
      halo(w * (0.82 + 0.03 * Math.cos(t / 27)), h * (0.78 + 0.04 * Math.sin(t / 19)), w * 0.32, 0.05);
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.y < -10) { p.y = h + 10; p.x = Math.random() * w; }
        const flicker = 0.6 + 0.4 * Math.sin(t * 1.3 + p.phase);
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(89, 193, 222, ${p.a * flicker})`;
        ctx.shadowColor = "rgba(11, 196, 226, 0.8)";
        ctx.shadowBlur = 6 * p.r;
        ctx.fill();
      }
      ctx.shadowBlur = 0;
      if (!reduce) raf = requestAnimationFrame(draw);
    }

    function onVisibility() {
      cancelAnimationFrame(raf);
      if (!document.hidden) raf = requestAnimationFrame(draw);
    }

    resize();
    draw();
    addEventListener("resize", resize);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      cancelAnimationFrame(raf);
      removeEventListener("resize", resize);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  });
</script>

<div class="backdrop" aria-hidden="true">
  <canvas bind:this={canvas}></canvas>
  <div class="hexgrid"></div>
  <div class="grain"></div>
</div>

<style>
  .backdrop {
    position: fixed; inset: 0; z-index: -1; pointer-events: none;
    background:
      radial-gradient(ellipse at 50% 0%, #0f2038 0%, var(--lol-dark) 35%, var(--lol-black) 75%),
      var(--lol-black);
  }
  canvas { position: absolute; inset: 0; width: 100%; height: 100%; }
  /* Faint Hextech lattice, fading toward the edges. */
  .hexgrid {
    position: absolute; inset: 0; opacity: 0.05;
    background-image:
      linear-gradient(30deg, var(--lol-gold) 1px, transparent 1px),
      linear-gradient(150deg, var(--lol-gold) 1px, transparent 1px);
    background-size: 56px 32px;
    mask-image: radial-gradient(ellipse at 50% 30%, black 0%, transparent 70%);
  }
  .grain {
    position: absolute; inset: 0; opacity: 0.06; mix-blend-mode: overlay;
        background-image: url("/grain.svg");
  }
  /* Vignette */
  .backdrop::after {
    content: ""; position: absolute; inset: 0;
    background: radial-gradient(ellipse at 50% 45%, transparent 55%, rgba(1, 10, 19, 0.85) 100%);
  }
</style>
