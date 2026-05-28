"use client";
import "@openuidev/react-ui/components.css";
import "@openuidev/react-ui/styles/index.css";

import { useReducer, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";

import { useBrainstormWs } from "@/hooks/use-brainstorm-ws";
import type { BrainstormAction, ChatMessage, FileNode, DataPreview } from "@/hooks/use-brainstorm-ws";
import FileTree from "@/components/file-tree";
import ChatHistory from "@/components/chat-history";
import UiRenderer from "@/components/ui-renderer";
import DataPreviewPanel from "@/components/data-preview";

interface BrainstormState {
  uiSpec: string | null;
  messages: ChatMessage[];
  fileTree: FileNode[];
  dataPreview: DataPreview | null;
}

const INITIAL_STATE: BrainstormState = {
  uiSpec: null,
  messages: [],
  fileTree: [],
  dataPreview: null,
};

function reducer(state: BrainstormState, action: BrainstormAction): BrainstormState {
  switch (action.type) {
    case "SET_SPEC":
      return { ...state, uiSpec: action.spec, dataPreview: null };
    case "ADD_MESSAGE":
      return { ...state, messages: [...state.messages, action.msg] };
    case "SET_FILE_TREE":
      return { ...state, fileTree: action.tree };
    case "SET_DATA_PREVIEW":
      return { ...state, dataPreview: action.preview, uiSpec: null };
    default:
      return state;
  }
}

const WS_PORT = Number(process.env.NEXT_PUBLIC_MCP_WS_PORT ?? 8765);

function BrainstormUI() {
  const params = useSearchParams();
  const project = params.get("project") ?? "";
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);

  const stableDispatch = useCallback((action: BrainstormAction) => dispatch(action), []);
  useBrainstormWs(WS_PORT, stableDispatch);

  const rightPanel = state.uiSpec ? (
    <UiRenderer spec={state.uiSpec} />
  ) : state.dataPreview ? (
    <DataPreviewPanel preview={state.dataPreview} />
  ) : (
    <p className="text-neutral-600 text-xs mt-4">
      Waiting for Claude to render UI or parse a data file…
    </p>
  );

  return (
    <div className="flex flex-col h-screen bg-neutral-950 text-neutral-100 font-mono text-sm">
      {/* Header */}
      <header className="shrink-0 px-4 py-2 border-b border-neutral-800 flex items-center gap-3">
        <span className="text-neutral-400 text-xs font-semibold tracking-widest uppercase">
          brainstorm-ui
        </span>
        {project && (
          <span className="text-neutral-600 text-xs truncate" title={project}>
            {project}
          </span>
        )}
        <span className="ml-auto text-neutral-700 text-xs">ws:{WS_PORT}</span>
      </header>

      {/* 3-panel body */}
      <div className="flex flex-1 overflow-hidden">
        {/* File tree — fixed 220px */}
        <aside className="w-[220px] shrink-0 border-r border-neutral-800 overflow-y-auto p-2">
          <p className="text-neutral-600 text-xs uppercase tracking-widest mb-2 px-1">Files</p>
          <FileTree nodes={state.fileTree} />
        </aside>

        {/* Chat history — flex grow */}
        <main className="flex-1 overflow-y-auto p-4 border-r border-neutral-800">
          <p className="text-neutral-600 text-xs uppercase tracking-widest mb-4">Chat</p>
          <ChatHistory messages={state.messages} />
        </main>

        {/* Rendered UI / data preview — flex grow */}
        <aside className="flex-1 overflow-y-auto p-4">
          <p className="text-neutral-600 text-xs uppercase tracking-widest mb-4">Output</p>
          {rightPanel}
        </aside>
      </div>
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<div className="h-screen bg-neutral-950" />}>
      <BrainstormUI />
    </Suspense>
  );
}
