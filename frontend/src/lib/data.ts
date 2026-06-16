import { api } from "./api";

export type Conversation = {
  id: string;
  title: string;
  createdAt?: string;
  updatedAt?: string;
};
export type Source = {
  n?: number;
  title: string;
  source?: string;
  url?: string;
  score?: number;
};
export type ChatMessage = {
  id?: string;
  role: "USER" | "ASSISTANT";
  content: string;
  sources?: Source[];
};
export type Doc = {
  id: string;
  filename: string;
  status: "PENDING" | "INDEXED" | "FAILED";
  chunkCount: number;
};

type RawMessage = {
  id?: string;
  role: "USER" | "ASSISTANT";
  content: string;
  sources?: string | null;
};

async function ok<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail || detail?.message || "Request failed");
  }
  return res.json() as Promise<T>;
}

function parseSources(raw: string | null | undefined): Source[] | undefined {
  if (!raw) return undefined;
  try {
    // The backend stores the SSE "sources" frame: {"sources":[...]} (or a bare array).
    const obj = typeof raw === "string" ? JSON.parse(raw) : raw;
    const arr = Array.isArray(obj) ? obj : obj?.sources;
    return Array.isArray(arr) ? (arr as Source[]) : undefined;
  } catch {
    return undefined;
  }
}

export async function listConversations(): Promise<Conversation[]> {
  return ok<Conversation[]>(await api("/api/conversations"));
}

export async function getMessages(id: string): Promise<ChatMessage[]> {
  const raw = await ok<RawMessage[]>(await api(`/api/conversations/${id}/messages`));
  return raw.map((m) => ({
    id: m.id,
    role: m.role,
    content: m.content,
    sources: parseSources(m.sources),
  }));
}

export async function deleteConversation(id: string): Promise<void> {
  const res = await api(`/api/conversations/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Could not delete conversation");
}

export async function listDocuments(): Promise<Doc[]> {
  return ok<Doc[]>(await api("/api/documents"));
}

export async function uploadDocument(file: File): Promise<Doc> {
  const form = new FormData();
  form.append("file", file);
  // No Content-Type header: the browser sets the multipart boundary; api() only
  // adds Authorization.
  return ok<Doc>(await api("/api/documents", { method: "POST", body: form }));
}

export async function deleteDocument(id: string): Promise<void> {
  const res = await api(`/api/documents/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Could not delete document");
}
