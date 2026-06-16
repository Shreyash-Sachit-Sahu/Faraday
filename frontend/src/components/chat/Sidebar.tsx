"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { Plus, Trash2, FileText, Upload, X } from "lucide-react";
import { Wordmark } from "@/components/Button";
import type { Conversation, Doc } from "@/lib/data";

const ACCEPT = ".pdf,.txt,.md,.docx";
const FAIL_RED = "#C4615C"; // deliberate one-state semantic exception to the palette

function StatusBadge({ status }: { status: Doc["status"] }) {
  if (status === "INDEXED") {
    return (
      <span className="flex items-center gap-1.5 text-field">
        <span className="h-1.5 w-1.5 rounded-full bg-field" />
        Indexed
      </span>
    );
  }
  if (status === "PENDING") {
    return (
      <span className="flex items-center gap-1.5 text-copper">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-copper" />
        Indexing…
      </span>
    );
  }
  return (
    <span className="flex items-center gap-1.5" style={{ color: FAIL_RED }}>
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: FAIL_RED }} />
      Failed
    </span>
  );
}

export default function Sidebar({
  conversations,
  activeId,
  onSwitch,
  onNew,
  onDeleteConversation,
  docs,
  onUpload,
  onDeleteDoc,
  userName,
  onSignOut,
  open,
  onClose,
}: {
  conversations: Conversation[];
  activeId: string | null;
  onSwitch: (id: string) => void;
  onNew: () => void;
  onDeleteConversation: (id: string) => void;
  docs: Doc[];
  onUpload: (file: File) => Promise<void>;
  onDeleteDoc: (id: string) => void;
  userName: string;
  onSignOut: () => void;
  open: boolean;
  onClose: () => void;
}) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);
  const [uploadErr, setUploadErr] = useState<string | null>(null);

  const handleFiles = async (files: FileList | null) => {
    setUploadErr(null);
    const file = files?.[0];
    if (!file) return;
    try {
      await onUpload(file);
    } catch (e) {
      setUploadErr(e instanceof Error ? e.message : "Upload failed");
    }
  };

  return (
    <>
      {open && (
        <div className="fixed inset-0 z-30 bg-ink/60 md:hidden" onClick={onClose} />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-surface-2 bg-surface transition-transform md:static md:z-auto md:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between p-4">
          <Link href="/">
            <Wordmark size="text-lg" />
          </Link>
          <button className="md:hidden" onClick={onClose} aria-label="Close menu">
            <X size={18} />
          </button>
        </div>

        <div className="px-4">
          <button
            onClick={onNew}
            className="flex w-full items-center justify-center gap-2 rounded-full border border-surface-2 px-4 py-2.5 text-sm text-text transition hover:bg-surface-2"
          >
            <Plus size={16} /> New chat
          </button>
        </div>

        <div className="mt-5 flex-1 overflow-y-auto px-3">
          <p className="px-1 pb-2 font-mono text-[10px] uppercase tracking-wider text-muted">
            Conversations
          </p>
          <ul className="space-y-0.5">
            {conversations.map((c) => (
              <li key={c.id} className="group relative">
                <button
                  onClick={() => onSwitch(c.id)}
                  className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 pr-8 text-left text-sm transition ${
                    c.id === activeId
                      ? "border-l-2 border-copper bg-surface-2 text-text"
                      : "text-muted hover:bg-surface-2 hover:text-text"
                  }`}
                >
                  <span className="truncate">{c.title}</span>
                </button>
                <button
                  onClick={() => onDeleteConversation(c.id)}
                  aria-label="Delete conversation"
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-muted opacity-0 transition hover:text-text group-hover:opacity-100"
                >
                  <Trash2 size={14} />
                </button>
              </li>
            ))}
            {conversations.length === 0 && (
              <li className="px-3 py-2 text-sm text-muted">No conversations yet.</li>
            )}
          </ul>
        </div>

        <div className="border-t border-surface-2 p-4">
          <p className="pb-2 font-mono text-[10px] uppercase tracking-wider text-muted">
            Your documents
          </p>
          <input
            ref={fileRef}
            type="file"
            accept={ACCEPT}
            className="hidden"
            onChange={(e) => {
              handleFiles(e.target.files);
              e.target.value = "";
            }}
          />
          <div
            onClick={() => fileRef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault();
              setDrag(true);
            }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDrag(false);
              handleFiles(e.dataTransfer.files);
            }}
            className={`flex cursor-pointer flex-col items-center gap-1 rounded-xl border border-dashed px-3 py-4 text-center text-xs transition ${
              drag ? "border-field bg-surface-2" : "border-surface-2 hover:border-field"
            }`}
          >
            <Upload size={16} className="text-muted" />
            <span className="text-muted">
              Drop a file or <span className="text-field">browse</span>
            </span>
            <span className="text-[10px] text-muted">.pdf .txt .md .docx</span>
          </div>
          {uploadErr && (
            <p className="mt-2 text-xs" style={{ color: FAIL_RED }}>
              {uploadErr}
            </p>
          )}
          <ul className="mt-3 max-h-44 space-y-1 overflow-y-auto">
            {docs.map((d) => (
              <li
                key={d.id}
                className="group flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs hover:bg-surface-2"
              >
                <FileText size={14} className="shrink-0 text-muted" />
                <span className="min-w-0 flex-1 truncate font-mono text-text">
                  {d.filename}
                </span>
                <span className="shrink-0 font-mono text-[10px]">
                  <StatusBadge status={d.status} />
                </span>
                <button
                  onClick={() => onDeleteDoc(d.id)}
                  aria-label="Delete document"
                  className="shrink-0 rounded p-0.5 text-muted opacity-0 transition hover:text-text group-hover:opacity-100"
                >
                  <Trash2 size={13} />
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="flex items-center justify-between border-t border-surface-2 px-4 py-3">
          <span className="truncate font-mono text-xs text-muted">{userName}</span>
          <button
            onClick={onSignOut}
            className="shrink-0 rounded-full border border-surface-2 px-3 py-1.5 text-xs text-text transition hover:bg-surface-2"
          >
            Sign out
          </button>
        </div>
      </aside>
    </>
  );
}
