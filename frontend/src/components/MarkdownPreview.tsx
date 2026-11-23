"use client";

import React from "react";

interface MarkdownPreviewProps {
  content: string;
  className?: string;
}

export function MarkdownPreview({ content, className = "" }: MarkdownPreviewProps) {
  if (!content || !content.trim()) {
    return (
      <div className="py-12 text-center font-mono text-xs text-zinc-500 italic">
        (No content written yet. Switch to Edit Mode to add content.)
      </div>
    );
  }

  const lines = content.split("\n");
  const renderedElements: React.ReactNode[] = [];
  let inList = false;
  let listItems: React.ReactNode[] = [];

  const flushList = (key: string) => {
    if (inList && listItems.length > 0) {
      renderedElements.push(
        <ul key={`ul-${key}`} className="my-2 space-y-1.5 pl-5 list-disc text-zinc-300">
          {listItems}
        </ul>
      );
      listItems = [];
      inList = false;
    }
  };

  const formatInline = (text: string): React.ReactNode => {
    // Splits text by bold (**...**) and inline code (`...`)
    const parts: React.ReactNode[] = [];
    const regex = /(\*\*[^*]+\*\*|`[^`]+`)/g;
    let lastIdx = 0;
    let match: RegExpExecArray | null;

    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIdx) {
        parts.push(text.substring(lastIdx, match.index));
      }
      const token = match[0];
      if (token.startsWith("**") && token.endsWith("**")) {
        parts.push(
          <strong key={match.index} className="font-semibold text-white">
            {token.slice(2, -2)}
          </strong>
        );
      } else if (token.startsWith("`") && token.endsWith("`")) {
        parts.push(
          <code
            key={match.index}
            className="rounded bg-zinc-800/80 px-1.5 py-0.5 font-mono text-xs text-emerald-300"
          >
            {token.slice(1, -1)}
          </code>
        );
      }
      lastIdx = regex.lastIndex;
    }

    if (lastIdx < text.length) {
      parts.push(text.substring(lastIdx));
    }

    return parts.length > 0 ? parts : text;
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();

    if (!trimmed) {
      flushList(`blank-${idx}`);
      return;
    }

    // Heading 1
    if (line.startsWith("# ")) {
      flushList(`h1-${idx}`);
      renderedElements.push(
        <h1
          key={`h1-${idx}`}
          className="mt-6 mb-3 text-xl font-bold tracking-tight text-white border-b border-zinc-800 pb-2 first:mt-0"
        >
          {formatInline(line.slice(2))}
        </h1>
      );
      return;
    }

    // Heading 2
    if (line.startsWith("## ")) {
      flushList(`h2-${idx}`);
      renderedElements.push(
        <h2
          key={`h2-${idx}`}
          className="mt-5 mb-2 text-base font-semibold tracking-wide text-emerald-400 first:mt-0"
        >
          {formatInline(line.slice(3))}
        </h2>
      );
      return;
    }

    // Heading 3
    if (line.startsWith("### ")) {
      flushList(`h3-${idx}`);
      renderedElements.push(
        <h3
          key={`h3-${idx}`}
          className="mt-4 mb-1.5 text-sm font-semibold text-zinc-200 first:mt-0"
        >
          {formatInline(line.slice(4))}
        </h3>
      );
      return;
    }

    // Blockquote
    if (line.startsWith("> ")) {
      flushList(`bq-${idx}`);
      renderedElements.push(
        <blockquote
          key={`bq-${idx}`}
          className="my-3 border-l-2 border-emerald-500 bg-zinc-900/60 py-1.5 px-3 italic text-zinc-300 text-xs rounded-r"
        >
          {formatInline(line.slice(2))}
        </blockquote>
      );
      return;
    }

    // Bullet item
    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      inList = true;
      listItems.push(
        <li key={`li-${idx}`} className="text-xs text-zinc-300 leading-relaxed">
          {formatInline(trimmed.slice(2))}
        </li>
      );
      return;
    }

    // Numbered list item
    const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
    if (numMatch) {
      flushList(`num-${idx}`);
      renderedElements.push(
        <div key={`num-${idx}`} className="my-1.5 flex gap-2 text-xs text-zinc-300">
          <span className="font-mono text-emerald-400 font-bold">{numMatch[1]}.</span>
          <span>{formatInline(numMatch[2])}</span>
        </div>
      );
      return;
    }

    // Normal paragraph
    flushList(`p-${idx}`);
    renderedElements.push(
      <p key={`p-${idx}`} className="my-1.5 text-xs text-zinc-300 leading-relaxed">
        {formatInline(line)}
      </p>
    );
  });

  flushList("final");

  return (
    <div className={`p-4 sm:p-6 bg-zinc-950 rounded-xl border border-zinc-800 ${className}`}>
      {renderedElements}
    </div>
  );
}
