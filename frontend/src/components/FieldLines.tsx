"use client";

import { useEffect, useRef } from "react";
import { createNoise3D } from "simplex-noise";

export default function FieldLines() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const noise3D = createNoise3D();
    const pointer = { x: -9999, y: -9999, active: false };
    let w = 0;
    let h = 0;
    let raf = 0;
    let t = 0;
    let particles: { x: number; y: number }[] = [];
    const COUNT = reduced ? 0 : 850;
    const SCALE = 0.0016;
    const SPEED = 0.0006;

    const resize = () => {
      w = canvas.clientWidth;
      h = canvas.clientHeight;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      particles = Array.from({ length: COUNT }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
      }));
      ctx.fillStyle = "#0b0d14";
      ctx.fillRect(0, 0, w, h);
    };

    const onMove = (e: PointerEvent) => {
      const r = canvas.getBoundingClientRect();
      pointer.x = e.clientX - r.left;
      pointer.y = e.clientY - r.top;
      pointer.active = true;
    };
    const onLeave = () => {
      pointer.active = false;
      pointer.x = -9999;
      pointer.y = -9999;
    };

    resize();
    window.addEventListener("resize", resize);
    canvas.addEventListener("pointermove", onMove);
    canvas.addEventListener("pointerleave", onLeave);

    if (reduced) {
      // Quiet static field: a few faint horizontal field curves.
      ctx.globalAlpha = 0.18;
      for (let i = 0; i < 7; i++) {
        const y = (h / 8) * (i + 1);
        ctx.strokeStyle = i % 2 ? "#5bc8e8" : "#e0915f";
        ctx.beginPath();
        for (let x = 0; x <= w; x += 6) {
          const yy = y + Math.sin(x * 0.004 + i) * 14;
          x === 0 ? ctx.moveTo(x, yy) : ctx.lineTo(x, yy);
        }
        ctx.stroke();
      }
      return () => {
        window.removeEventListener("resize", resize);
        canvas.removeEventListener("pointermove", onMove);
        canvas.removeEventListener("pointerleave", onLeave);
      };
    }

    const step = () => {
      ctx.fillStyle = "rgba(11,13,20,0.055)"; // fade => trails
      ctx.fillRect(0, 0, w, h);
      ctx.lineWidth = 1;
      for (const p of particles) {
        let angle = noise3D(p.x * SCALE, p.y * SCALE, t) * Math.PI * 2;
        if (pointer.active) {
          const dx = p.x - pointer.x;
          const dy = p.y - pointer.y;
          const dist2 = dx * dx + dy * dy;
          const radius = 230;
          if (dist2 < radius * radius) {
            const d = Math.sqrt(dist2) || 1;
            const tangent = Math.atan2(dy, dx) + Math.PI / 2; // curl around pointer
            const inf = 1 - d / radius;
            angle = angle * (1 - inf) + tangent * inf;
          }
        }
        const nx = p.x + Math.cos(angle) * 1.4;
        const ny = p.y + Math.sin(angle) * 1.4;
        const mix = Math.max(0, Math.min(1, ny / h));
        const r = Math.round(224 + (91 - 224) * mix);
        const g = Math.round(145 + (200 - 145) * mix);
        const b = Math.round(95 + (232 - 95) * mix);
        ctx.strokeStyle = `rgba(${r},${g},${b},0.34)`;
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(nx, ny);
        ctx.stroke();
        p.x = nx;
        p.y = ny;
        if (p.x < 0 || p.x > w || p.y < 0 || p.y > h) {
          p.x = Math.random() * w;
          p.y = Math.random() * h;
        }
      }
      t += SPEED;
      raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      canvas.removeEventListener("pointermove", onMove);
      canvas.removeEventListener("pointerleave", onLeave);
    };
  }, []);

  return <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" aria-hidden="true" />;
}
