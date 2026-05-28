import type { DataPreview as DataPreviewType } from "@/hooks/use-brainstorm-ws";

interface DataPreviewProps {
  preview: DataPreviewType;
}

/** Renders a parsed CSV/Excel/PDF as a scrollable table. */
export default function DataPreview({ preview }: DataPreviewProps) {
  return (
    <div>
      <p className="text-xs text-neutral-500 mb-3">
        {preview.filename} — {preview.rows.length} rows × {preview.columns.length} cols
      </p>
      <div className="overflow-x-auto">
        <table className="text-xs border-collapse min-w-full">
          <thead>
            <tr>
              {preview.columns.map((col) => (
                <th
                  key={col}
                  className="border border-neutral-700 px-2 py-1 text-left text-neutral-400 bg-neutral-900 whitespace-nowrap"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {preview.rows.map((row, i) => (
              <tr key={i} className={i % 2 === 0 ? "bg-neutral-950" : "bg-neutral-900"}>
                {preview.columns.map((col) => (
                  <td
                    key={col}
                    className="border border-neutral-800 px-2 py-1 text-neutral-300 max-w-48 truncate"
                    title={String(row[col] ?? "")}
                  >
                    {String(row[col] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
