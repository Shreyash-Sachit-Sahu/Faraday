"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform } from "motion/react";
import FieldLines from "@/components/FieldLines";
import { Button } from "@/components/Button";

export default function Hero() {
  const ref = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  });
  const y = useTransform(scrollYProgress, [0, 1], [0, -60]);
  const opacity = useTransform(scrollYProgress, [0, 0.85], [1, 0]);

  return (
    <section ref={ref} id="top" className="relative min-h-screen overflow-hidden">
      <FieldLines />
      {/* radial vignette so the headline stays legible over the live field */}
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-ink/10 via-ink/40 to-ink" />

      <div className="relative mx-auto flex min-h-screen max-w-[1100px] flex-col justify-end px-6 pb-28 md:pb-36">
        <motion.div style={{ y, opacity }} className="max-w-3xl">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-field">
            Computer-science tutoring
          </p>
          <h1 className="mt-5 font-display text-6xl leading-[1.02] tracking-tight md:text-7xl">
            Office hours that never close.
          </h1>
          <p className="mt-6 max-w-xl text-lg text-muted">
            Faraday explains computer science clearly, shows you exactly where every
            answer comes from, and learns from the notes you bring.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-4">
            <Button href="/register" variant="solid">
              Start asking
            </Button>
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
