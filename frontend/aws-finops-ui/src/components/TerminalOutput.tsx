'use client';

import React, { useEffect, useRef } from 'react';

interface TerminalOutputProps {
  content: string;
  height?: string;
  className?: string;
}

export function TerminalOutput({ content, height = '300px', className = '' }: TerminalOutputProps) {
  const containerRef = useRef<HTMLPreElement>(null);
  
  // Auto-scroll to bottom when content changes
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [content]);

  return (
    <pre
      ref={containerRef}
      className={`${className} bg-black text-white font-mono text-sm p-4 overflow-auto`}
      style={{
        height,
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
        fontFamily: 'Menlo, Monaco, Consolas, monospace',
        lineHeight: 1.5
      }}
    >
      {content || 'No output yet.'}
    </pre>
  );
} 