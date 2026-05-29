import { useEffect, useRef, useCallback } from "react";
import type { SalesChartData } from "@/components/sales-chart";

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
};

export type FileNode = {
  name: string;
  path: string;
  type: "file" | "dir";
  children?: FileNode[];
};

export type DataPreview = {
  filename: string;
  columns: string[];
  rows: Record<string, unknown>[];
};

export type VisualizeAction =
  | { type: "SET_SPEC"; spec: string }
  | { type: "ADD_MESSAGE"; msg: ChatMessage }
  | { type: "SET_FILE_TREE"; tree: FileNode[] }
  | { type: "SET_DATA_PREVIEW"; preview: DataPreview }
  | { type: "SET_CHART"; chart: SalesChartData };

/** Connects to the visualize-ui MCP server WebSocket and dispatches incoming messages. */
export function useVisualizeWs(port: number, dispatch: (action: VisualizeAction) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const dispatchRef = useRef(dispatch);
  const isDestroyed = useRef(false);
  dispatchRef.current = dispatch;

  const connect = useCallback(() => {
    if (isDestroyed.current) return;
    const ws = new WebSocket(`ws://localhost:${port}`);
    wsRef.current = ws;

    ws.onmessage = (event: MessageEvent) => {
      let msg: Record<string, unknown>;
      try {
        msg = JSON.parse(event.data as string) as Record<string, unknown>;
      } catch {
        return;
      }
      switch (msg.type) {
        case "render_ui":
          if (typeof msg.spec === "string")
            dispatchRef.current({ type: "SET_SPEC", spec: msg.spec });
          break;
        case "push_message":
          if (
            (msg.role === "user" || msg.role === "assistant") &&
            typeof msg.content === "string" &&
            typeof msg.timestamp === "string"
          )
            dispatchRef.current({
              type: "ADD_MESSAGE",
              msg: { role: msg.role, content: msg.content, timestamp: msg.timestamp },
            });
          break;
        case "file_tree":
          if (Array.isArray(msg.tree))
            dispatchRef.current({ type: "SET_FILE_TREE", tree: msg.tree as FileNode[] });
          break;
        case "data_preview":
          if (
            typeof msg.filename === "string" &&
            Array.isArray(msg.columns) &&
            Array.isArray(msg.rows)
          )
            dispatchRef.current({
              type: "SET_DATA_PREVIEW",
              preview: {
                filename: msg.filename,
                columns: msg.columns as string[],
                rows: msg.rows as Record<string, unknown>[],
              },
            });
          break;
        case "chart_data":
          if (
            typeof msg.title === "string" &&
            typeof msg.x_key === "string" &&
            typeof msg.y_key === "string" &&
            Array.isArray(msg.rows)
          )
            dispatchRef.current({
              type: "SET_CHART",
              chart: msg as unknown as SalesChartData,
            });
          break;
      }
    };

    ws.onclose = () => {
      if (!isDestroyed.current) setTimeout(connect, 2000);
    };
  }, [port]);

  useEffect(() => {
    isDestroyed.current = false;
    connect();
    return () => {
      isDestroyed.current = true;
      wsRef.current?.close();
    };
  }, [connect]);
}
