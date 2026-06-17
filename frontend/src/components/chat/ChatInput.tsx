"use client";

import { useEffect, useRef } from "react";
import { motion } from "motion/react";
import { ArrowUp } from "lucide-react";
import { FieldGlyph } from "@/components/Button";

const EXAMPLES = [
  "Explain how B-trees stay balanced",
  "Walk me through Dijkstra's algorithm",
  "What's the difference between TCP and UDP?",
  "Write a Python function to reverse a linked list",
];

const EASE: [number, number, number, number] = [0.32, 0.72, 0, 1];

export function EmptyWelcome({ onPick }: { onPick: (s: string) => void }) {
  return (
    <div className="relative flex h-full flex-col items-center justify-center px-6 text-center">
      <div className="panel-glow opacity-70" />
      <motion.div
        initial={{ opacity: 0, scale: 0.85 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, ease: EASE }}
        className="relative"
      >
        <FieldGlyph className="glyph-live h-14 w-14" />
      </motion.div>
      <motion.h2
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.6, ease: EASE }}
        className="relative mt-7 text-balance font-display text-4xl tracking-tight"
      >
        What are you working on?
      </motion.h2>
      <motion.p
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.18, duration: 0.6, ease: EASE }}
        className="relative mt-3 max-w-md text-pretty text-muted"
      >
        Ask anything in computer science &mdash; Faraday cites where every answer
        comes from.
      </motion.p>
      <div className="relative mt-9 flex max-w-xl flex-wrap justify-center gap-2.5">
        {EXAMPLES.map((e, i) => (
          <motion.button
            key={e}
            onClick={() => onPick(e)}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.28 + i * 0.07, duration: 0.5, ease: EASE }}
            className="rounded-full border border-text/10 bg-surface/50 px-4 py-2 text-sm text-muted backdrop-blur-sm transition-all duration-300 ease-fluid hover:-translate-y-0.5 hover:border-field/40 hover:text-text"
          >
            {e}
          </motion.button>
        ))}
      </div>
    </div>
  );
}

export default function ChatInput({
  value,
  onChange,
  onSubmit,
  disabled,
}: {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  disabled: boolean;
}) {
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 168)}px`; // ~6 rows
  }, [value]);

  const submit = () => {
    if (!disabled && value.trim()) onSubmit();
  };

  return (
    <div className="border-t border-text/8 bg-ink/70 p-4 backdrop-blur-xl">
      <div className="mx-auto flex max-w-3xl items-end gap-2">
        <div className="input-shell flex flex-1 items-end rounded-2xl border border-surface-2 bg-surface/70">
          <textarea
            ref={ref}
            value={value}
            rows={1}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder="Ask Faraday about computer science…"
            className="max-h-[168px] flex-1 resize-none bg-transparent px-4 py-3 text-text outline-none placeholder:text-muted"
          />
        </div>
        <button
          onClick={submit}
          disabled={disabled || !value.trim()}
          aria-label="Send message"
          className="group flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-copper text-ink transition-all duration-300 ease-fluid hover:brightness-110 active:scale-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <ArrowUp
            size={20}
            className="transition-transform duration-300 ease-fluid group-hover:-translate-y-0.5"
          />
        </button>
      </div>
    </div>
  );
}
