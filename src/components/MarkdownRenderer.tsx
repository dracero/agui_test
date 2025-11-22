// src/components/MarkdownRenderer.tsx
"use client";

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

interface MarkdownRendererProps {
    content: string;
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
    return (
        <div className="markdown-content">
            <ReactMarkdown
                remarkPlugins={[remarkMath]}
                rehypePlugins={[rehypeKatex]}
                components={{
                    // Customize code blocks
                    code({ node, inline, className, children, ...props }: any) {
                        return inline ? (
                            <code className="bg-gray-100 px-1 py-0.5 rounded text-sm" {...props}>
                                {children}
                            </code>
                        ) : (
                            <pre className="bg-gray-100 p-3 rounded-lg overflow-x-auto my-2">
                                <code className={className} {...props}>
                                    {children}
                                </code>
                            </pre>
                        );
                    },
                    // Customize paragraphs
                    p({ children }) {
                        return <p className="mb-2">{children}</p>;
                    },
                    // Customize lists
                    ul({ children }) {
                        return <ul className="list-disc list-inside mb-2">{children}</ul>;
                    },
                    ol({ children }) {
                        return <ol className="list-decimal list-inside mb-2">{children}</ol>;
                    },
                    // Customize headings
                    h1({ children }) {
                        return <h1 className="text-2xl font-bold mb-2">{children}</h1>;
                    },
                    h2({ children }) {
                        return <h2 className="text-xl font-bold mb-2">{children}</h2>;
                    },
                    h3({ children }) {
                        return <h3 className="text-lg font-bold mb-2">{children}</h3>;
                    },
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
}
