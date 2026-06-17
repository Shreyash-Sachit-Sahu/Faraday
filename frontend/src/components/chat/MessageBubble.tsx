"use client";

import { motion } from "motion/react";
import { FieldGlyph } from "@/components/Button";
import Markdown from "@/components/Markdown";
import type { ChatMessage } from "@/lib/data";

// One-time sleek entry: fade + rise + blur-clear. Fires on mount only, so it
// never re-triggers as streamed tokens update the content.
const ENTER = {
  initial: { opacity: 0, y: 14, filter: "blur(6px)" },
  animate: { opacity: 1, y: 0, filter: "blur(0px)" },
  transition: { duration: 0.55, ease: [0.32, 0.72, 0, 1] as [number, number, number, number] },
};

function ThinkingDots() {
  return (
    <div className="flex items-center gap-1.5 py-2.5">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="dot-think h-2 w-2 rounded-full bg-field/70"
          style={{ animationDelay: `${i * 0.16}s` }}
        />
      ))}
    </div>
  );
}

export default function MessageBubble({
  message,
  streaming,
}: {
  message: ChatMessage;
  streaming?: boolean;
}) {
  if (message.role === "USER") {
    return (
      <motion.div {...ENTER} className="flex justify-end">
        <div className="max-w-[80%] whitespace-pre-wrap rounded-2xl rounded-br-md border border-text/10 bg-gradient-to-br from-surface-2 to-surface px-4 py-2.5 text-text shadow-[0_12px_30px_-18px_rgba(0,0,0,0.85)]">
          {message.content}
        </div>
      </motion.div>
    );
  }

  const empty = !message.content;
  return (
    <motion.div {...ENTER} className="flex gap-3">
      <FieldGlyph className={`mt-1 h-6 w-6 shrink-0 ${streaming ? "glyph-live" : ""}`} />
      <div className="min-w-0 flex-1">
        {empty && streaming ? (
          <ThinkingDots />
        ) : (
          <div className="relative">
            <Markdown content={message.content} />
            {streaming && (
              <span className="ml-0.5 inline-block h-4 w-[3px] animate-pulse rounded-full bg-field align-middle" />
            )}
          </div>
        )}

        {message.sources && message.sources.length > 0 && (
          <div className="mt-3.5">
            <p className="mb-2 font-mono text-[10px] uppercase tracking-wider text-muted">
              Sources
            </p>
            <div className="flex flex-wrap gap-2">
              {message.sources.map((s, i) => {
                const label = `[${s.n ?? i + 1}] ${s.title}`;
                const cls =
                  "rounded-full border border-text/10 bg-surface-2/70 px-3 py-1 font-mono text-xs text-field transition-all duration-300 ease-fluid hover:-translate-y-0.5 hover:border-field/40 hover:bg-surface-2";
                return s.url ? (
                  <a key={i} href={s.url} target="_blank" rel="noreferrer" className={cls}>
                    {label}
                  </a>
                ) : (
                  <span key={i} className={cls}>
                    {label}
                  </span>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}
