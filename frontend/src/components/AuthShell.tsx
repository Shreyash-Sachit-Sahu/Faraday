"use client";

import Link from "next/link";
import FieldLines from "@/components/FieldLines";
import { Wordmark } from "@/components/Button";

/** Auth pages reuse the field signature, faintly, so they feel part of the world. */
export default function AuthShell({ children }: { children: React.ReactNode }) {
  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden px-6 py-16">
      <div className="absolute inset-0 opacity-25">
        <FieldLines />
      </div>
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-ink/40 via-ink/70 to-ink" />
      <div className="relative w-full max-w-md rounded-2xl border border-surface-2 bg-surface p-8">
        <Link href="/" className="inline-block">
          <Wordmark />
        </Link>
        {children}
      </div>
    </main>
  );
}
