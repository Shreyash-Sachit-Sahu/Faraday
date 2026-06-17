"use client";

import Link from "next/link";
import { motion } from "motion/react";
import FieldLines from "@/components/FieldLines";
import { Wordmark } from "@/components/Button";

/** Auth pages reuse the field signature so they feel part of the world. */
export default function AuthShell({ children }: { children: React.ReactNode }) {
  return (
    <main className="relative flex min-h-[100dvh] items-center justify-center overflow-hidden px-6 py-16">
      <div className="ambient" />
      <div className="absolute inset-0 opacity-30">
        <FieldLines />
      </div>
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-ink/30 via-ink/60 to-ink/90" />
      <motion.div
        initial={{ opacity: 0, y: 20, filter: "blur(8px)" }}
        animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
        transition={{ duration: 0.6, ease: [0.32, 0.72, 0, 1] as [number, number, number, number] }}
        className="relative w-full max-w-md rounded-[1.75rem] border border-text/8 bg-surface/20 p-2"
      >
        <div className="card relative overflow-hidden rounded-[1.4rem] p-8">
          <div className="panel-glow opacity-60" />
          <div className="relative">
            <Link href="/" className="inline-block">
              <Wordmark />
            </Link>
            {children}
          </div>
        </div>
      </motion.div>
    </main>
  );
}
