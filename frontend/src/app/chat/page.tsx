"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Menu } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { streamChat } from "@/lib/chat";
import {
  listConversations,
  getMessages,
  deleteConversation,
  uploadDocument,
  deleteDocument,
  type Conversation,
  type ChatMessage,
  type Source,
} from "@/lib/data";
import { useDocuments } from "@/lib/useDocuments";
import Sidebar from "@/components/chat/Sidebar";
import MessageBubble from "@/components/chat/MessageBubble";
import ChatInput, { EmptyWelcome } from "@/components/chat/ChatInput";

export default function ChatPage() {
  const router = useRouter();
  const { user, ready, logout } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [input, setInput] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const threadEndRef = useRef<HTMLDivElement>(null);
  const signingOutRef = useRef(false);
  const { docs, refreshDocs } = useDocuments();

  useEffect(() => {
    // Skip during an intentional sign-out so it lands on the public landing
    // page ("/") instead of racing handleSignOut's push and bouncing to /login.
    if (ready && !user && !signingOutRef.current) router.replace("/login");
  }, [ready, user, router]);

  const refreshConversations = useCallback(async () => {
    try {
      setConversations(await listConversations());
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    if (user) refreshConversations();
  }, [user, refreshConversations]);

  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    threadEndRef.current?.scrollIntoView({
      behavior: reduced ? "auto" : "smooth",
      block: "end",
    });
  }, [messages]);

  const updateAssistant = useCallback(
    (fn: (a: ChatMessage) => ChatMessage) =>
      setMessages((m) => {
        const copy = m.slice();
        for (let i = copy.length - 1; i >= 0; i--) {
          if (copy[i].role === "ASSISTANT") {
            copy[i] = fn(copy[i]);
            break;
          }
        }
        return copy;
      }),
    [],
  );

  const send = useCallback(async () => {
    const content = input.trim();
    if (!content || streaming) return;
    setInput("");
    setMessages((m) => [
      ...m,
      { role: "USER", content },
      { role: "ASSISTANT", content: "" },
    ]);
    setStreaming(true);
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await streamChat(
        { message: content, conversationId: activeId ?? undefined },
        (e) => {
          if (e.event === "meta") {
            try {
              const id = JSON.parse(e.data).conversationId as string;
              if (id && !activeId) setActiveId(id);
            } catch {
              /* ignore */
            }
          } else if (e.event === "sources") {
            try {
              const arr = JSON.parse(e.data).sources as Source[];
              updateAssistant((a) => ({ ...a, sources: arr }));
            } catch {
              /* ignore */
            }
          } else if (e.event === "token") {
            try {
              const t = JSON.parse(e.data).text as string;
              updateAssistant((a) => ({ ...a, content: a.content + t }));
            } catch {
              /* ignore */
            }
          } else if (e.event === "error") {
            updateAssistant((a) => ({
              ...a,
              content:
                a.content || "Something went wrong while answering. Please try again.",
            }));
          }
        },
        controller.signal,
      );
    } catch {
      if (controller.signal.aborted) return; // user switched/started a new chat
      updateAssistant((a) => ({
        ...a,
        content:
          a.content || "Couldn't reach the tutor. Check your connection and try again.",
      }));
    } finally {
      if (!controller.signal.aborted) {
        setStreaming(false);
        refreshConversations();
      }
    }
  }, [input, streaming, activeId, updateAssistant, refreshConversations]);

  const switchConversation = async (id: string) => {
    setSidebarOpen(false);
    if (id === activeId) return;
    abortRef.current?.abort();
    setStreaming(false);
    setActiveId(id);
    try {
      setMessages(await getMessages(id));
    } catch {
      setMessages([]);
    }
  };

  const newChat = () => {
    abortRef.current?.abort();
    setStreaming(false);
    setMessages([]);
    setActiveId(null);
    setSidebarOpen(false);
  };

  const handleDeleteConversation = async (id: string) => {
    try {
      await deleteConversation(id);
    } catch {
      /* ignore */
    }
    await refreshConversations();
    if (id === activeId) newChat();
  };

  const handleUpload = async (file: File) => {
    await uploadDocument(file);
    refreshDocs();
  };

  const handleDeleteDoc = async (id: string) => {
    try {
      await deleteDocument(id);
    } catch {
      /* ignore */
    }
    refreshDocs();
  };

  const handleSignOut = async () => {
    signingOutRef.current = true;
    await logout();
    router.push("/");
  };

  if (!ready || !user) {
    return (
      <div className="flex h-screen items-center justify-center bg-ink text-muted">
        Loading…
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-ink">
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSwitch={switchConversation}
        onNew={newChat}
        onDeleteConversation={handleDeleteConversation}
        docs={docs}
        onUpload={handleUpload}
        onDeleteDoc={handleDeleteDoc}
        userName={user.displayName}
        onSignOut={handleSignOut}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center gap-3 border-b border-surface-2 p-3 md:hidden">
          <button onClick={() => setSidebarOpen(true)} aria-label="Open menu">
            <Menu size={20} />
          </button>
          <span className="font-display text-lg">Faraday</span>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <EmptyWelcome onPick={(s) => setInput(s)} />
          ) : (
            <div className="mx-auto max-w-3xl space-y-6 px-4 py-8">
              {messages.map((m, i) => (
                <MessageBubble
                  key={m.id ?? i}
                  message={m}
                  streaming={
                    streaming && i === messages.length - 1 && m.role === "ASSISTANT"
                  }
                />
              ))}
              <div ref={threadEndRef} />
            </div>
          )}
        </div>

        <ChatInput value={input} onChange={setInput} onSubmit={send} disabled={streaming} />
      </main>
    </div>
  );
}
