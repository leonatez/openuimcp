"use client";
import type { FileNode } from "@/hooks/use-visualize-ws";

interface FileTreeProps {
  nodes: FileNode[];
}

function TreeNode({ node }: { node: FileNode }) {
  const handleClick = () => {
    if (node.type === "file") {
      navigator.clipboard.writeText(`@${node.path}`).catch(() => {});
    }
  };

  return (
    <div>
      <div
        onClick={handleClick}
        title={node.type === "file" ? `Click to copy @${node.path}` : node.path}
        className={`py-0.5 px-1 rounded truncate text-xs leading-5 ${
          node.type === "file"
            ? "text-neutral-300 hover:bg-neutral-800 cursor-pointer"
            : "text-neutral-500 cursor-default"
        }`}
      >
        {node.type === "dir" ? "▸ " : "  "}
        {node.name}
      </div>
      {node.children && node.children.length > 0 && (
        <div className="pl-3 border-l border-neutral-800 ml-1">
          {node.children.map((child, i) => (
            <TreeNode key={i} node={child} />
          ))}
        </div>
      )}
    </div>
  );
}

/** Project file tree. Click a file to copy its @path to clipboard. */
export default function FileTree({ nodes }: FileTreeProps) {
  if (!nodes.length) {
    return <p className="text-neutral-600 text-xs mt-2">No files yet…</p>;
  }
  return (
    <div className="text-xs">
      {nodes.map((node, i) => (
        <TreeNode key={i} node={node} />
      ))}
    </div>
  );
}
