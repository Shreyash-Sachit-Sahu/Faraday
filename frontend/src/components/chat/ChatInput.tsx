"use client";

import { useEffect, useRef } from "react";
import { ArrowUp } from "lucide-react";
import { FieldGlyph } from "@/components/Button";

const EXAMPLES = [
  "Explain how B-trees stay balanced",
  "Walk me through Dijkstra's algorithm",
  "What's the difference between TCP and UDP?",
  "Write a Python function to reverse a linked list",
];

export function EmptyWelcome({ onPick }: { onPick: (s: string) => void }) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-6 text-center">
      <FieldGlyph className="h-12 w-12" />
      <h2 className="mt-6 font-display text-3xl tracking-tight">
        What are you working on?
      </h2>
      <p className="mt-2 max-w-md text-muted">
        Ask anything in computer science &mdash; Faraday cites where every answer
        comes from.
      </p>
      <div className="mt-8 flex max-w-xl flex-wrap justify-center gap-2.5">
        {EXAMPLES.map((e) => (
          <button
            key={e}
            onClick={() => onPick(e)}
            className="rounded-full border border-surface-2 bg-surface px-4 py-2 text-sm text-muted transition hover:border-field hover:text-text"
          >
            {e}
          </button>
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
    <div className="border-t border-surface-2 bg-ink/80 p-4 backdrop-blur">
      <div className="mx-auto flex max-w-3xl items-end gap-2">
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
          className="max-h-[168px] flex-1 resize-none rounded-2xl border border-surface-2 bg-surface px-4 py-3 text-text outline-none transition placeholder:text-muted focus:border-field"
        />
        <button
          onClick={submit}
          disabled={disabled || !value.trim()}
          aria-label="Send message"
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-copper text-ink transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <ArrowUp size={20} />
        </button>
      </div>
    </div>
  );
}
