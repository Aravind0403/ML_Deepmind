"use client";

import dynamic from "next/dynamic";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), {
  ssr: false,
  loading: () => (
    <div className="flex h-80 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-900 font-mono text-xs text-zinc-500">
      Loading Monaco Python Editor...
    </div>
  ),
});

interface CodeEditorBoxProps {
  value: string;
  onChange: (val: string) => void;
  height?: string;
  language?: string;
}

export function CodeEditorBox({
  value,
  onChange,
  height = "360px",
  language = "python",
}: CodeEditorBoxProps) {
  return (
    <div className="overflow-hidden rounded-lg border border-zinc-800 bg-[#1e1e1e]">
      <MonacoEditor
        height={height}
        language={language}
        theme="vs-dark"
        value={value}
        onChange={(v) => onChange(v ?? "")}
        options={{
          minimap: { enabled: false },
          fontSize: 13,
          lineNumbers: "on",
          scrollBeyondLastLine: false,
          tabSize: 4,
          automaticLayout: true,
          padding: { top: 12, bottom: 12 },
        }}
      />
    </div>
  );
}
