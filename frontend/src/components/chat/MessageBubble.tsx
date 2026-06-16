"use client";

import { FieldGlyph } from "@/components/Button";
import Markdown from "@/components/Markdown";
import type { ChatMessage } from "@/lib/data";

function Dot({ delay = "0s" }: { delay?: string }) {
  return (
    <span
      className="h-2 w-2 animate-pulse rounded-full bg-muted"
      style={{ animationDelay: delay }}
    />
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
      <div className="flex justify-end">
        <div className="max-w-[80%] whitespace-pre-wrap rounded-2xl bg-surface-2 px-4 py-2.5 text-text">
          {message.content}
        </div>
      </div>
    );
  }

  const empty = !message.content;
  return (
    <div className="flex gap-3">
      <FieldGlyph className="mt-1 h-6 w-6 shrink-0" />
      <div className="min-w-0 flex-1">
        {empty && streaming ? (
          <div className="flex gap-1.5 py-2">
            <Dot />
            <Dot delay="0.15s" />
            <Dot delay="0.3s" />
          </div>
        ) : (
          <div className="relative">
            <Markdown content={message.content} />
            {streaming && (
              <span className="ml-0.5 inline-block h-4 w-[3px] animate-pulse bg-field align-middle" />
            )}
          </div>
        )}

        {message.sources && message.sources.length > 0 && (
          <div className="mt-3">
            <p className="mb-1.5 font-mono text-[10px] uppercase tracking-wider text-muted">
              Sources
            </p>
            <div className="flex flex-wrap gap-2">
              {message.sources.map((s, i) => {
                const label = `[${s.n ?? i + 1}] ${s.title}`;
                const cls =
                  "rounded-full bg-surface-2 px-3 py-1 font-mono text-xs text-field";
                return s.url ? (
                  <a
                    key={i}
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                    className={`${cls} transition hover:brightness-125`}
                  >
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
    </div>
  );
}
