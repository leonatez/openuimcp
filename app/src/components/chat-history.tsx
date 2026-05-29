import type { ChatMessage } from "@/hooks/use-visualize-ws";

interface ChatHistoryProps {
  messages: ChatMessage[];
}

/** Mirrors the terminal visualize session conversation. */
export default function ChatHistory({ messages }: ChatHistoryProps) {
  if (!messages.length) {
    return <p className="text-neutral-600 text-xs mt-4">Waiting for chat messages…</p>;
  }
  return (
    <div className="flex flex-col gap-4">
      {messages.map((m, i) => (
        <div key={i} className="flex gap-2 text-sm">
          <span
            className={`shrink-0 font-mono font-bold ${
              m.role === "user" ? "text-blue-400" : "text-green-400"
            }`}
          >
            {m.role === "user" ? ">" : "AI"}
          </span>
          <p className="whitespace-pre-wrap break-words text-neutral-200">{m.content}</p>
        </div>
      ))}
    </div>
  );
}
