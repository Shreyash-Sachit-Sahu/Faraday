import { API_BASE, getAccessToken, rotate } from "./api";

export type ChatEvent = { event: string; data: string };

export async function streamChat(
  body: { message: string; conversationId?: string },
  onEvent: (e: ChatEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const send = async (retry: boolean): Promise<Response> => {
    const headers = new Headers({ "Content-Type": "application/json" });
    const token = getAccessToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      signal,
    });
    if (res.status === 401 && retry && (await rotate())) return send(false);
    return res;
  };

  const res = await send(true);
  if (!res.ok || !res.body) throw new Error("Chat request failed");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      let event = "message";
      let data = "";
      for (const line of frame.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trimStart();
      }
      if (data) onEvent({ event, data });
    }
  }
}
