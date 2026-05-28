"use client";
import { Renderer } from "@openuidev/react-lang";
import { openuiLibrary } from "@openuidev/react-ui/genui-lib";

interface UiRendererProps {
  spec: string;
}

/** Renders an OpenUI Lang spec string using the pre-built openuiLibrary. */
export default function UiRenderer({ spec }: UiRendererProps) {
  return (
    <div className="openui-output">
      <Renderer library={openuiLibrary} response={spec} isStreaming={false} />
    </div>
  );
}
