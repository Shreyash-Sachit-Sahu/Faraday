"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform } from "motion/react";
import FieldLines from "@/components/FieldLines";
import { Button } from "@/components/Button";
import AuthCTA from "@/components/AuthCTA";

export default function Hero() {
  const ref = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  });
  const y = useTransform(scrollYProgress, [0, 1], [0, -60]);
  const opacity = useTransform(scrollYProgress, [0, 0.85], [1, 0]);

  return (
    <section ref={ref} id="top" className="relative min-h-[100dvh] overflow-hidden">
      {/* ambient glow → live field → soft floor so the headline stays legible */}
      <div className="ambient" />
      <FieldLines />
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-ink/20 to-ink/90" />

      <div className="relative mx-auto flex min-h-[100dvh] max-w-[1100px] flex-col justify-end px-6 pb-28 md:pb-36">
        <motion.div style={{ y, opacity }} className="max-w-3xl">
          <span className="inline-flex items-center gap-2 rounded-full border border-text/10 bg-surface/40 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.22em] text-field backdrop-blur-sm">
            <span className="h-1.5 w-1.5 rounded-full bg-field" />
            Computer-science tutoring
          </span>
          <h1 className="mt-6 text-balance font-display text-6xl leading-[0.98] tracking-tight md:text-[5.4rem]">
            Office hours that never close.
          </h1>
          <p className="mt-6 max-w-xl text-pretty text-lg leading-relaxed text-muted">
            Faraday explains computer science clearly, shows you exactly where every
            answer comes from, and learns from the notes you bring.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-3">
            <AuthCTA variant="solid" arrow>
              Start asking
            </AuthCTA>
            <Button href="/login" variant="ghost">
              Sign in
            </Button>
          </div>
        </motion.div>
      </div>

      <div className="pointer-events-none absolute inset-x-0 bottom-7 flex justify-center">
        <span className="flex flex-col items-center gap-2 font-mono text-[10px] uppercase tracking-[0.3em] text-muted">
          scroll
          <span className="h-8 w-px animate-pulse bg-gradient-to-b from-field to-transparent" />
        </span>
      </div>
    </section>
  );
}
