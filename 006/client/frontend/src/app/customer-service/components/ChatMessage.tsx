import React from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { UserIcon, BrainIcon } from '@/components/icons';
import { cn } from '@/lib/utils';

import { MessageContent } from '../types';

interface ChatMessageProps {
  message: {
    role: 'user' | 'assistant';
    content: string | MessageContent;
    status?: 'pending' | 'complete' | 'error';
  };
  isLast?: boolean;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, isLast }) => {
  const isUser = message.role === 'user';
  const isPending = message.status === 'pending';

  const CodeBlock = {
    code({ node, inline, className, children, ...props }: any) {
      const match = /language-(\w+)/.exec(className || '');
      const language = match ? match[1] : '';

      if (!inline && language) {
        return (
          <div className="relative group my-3">
            <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                className="text-xs bg-white/10 px-2 py-1 rounded hover:bg-white/20"
                onClick={() => navigator.clipboard.writeText(String(children))}
              >
                Copy
              </button>
            </div>
            <SyntaxHighlighter
              language={language}
              style={oneDark}
              showLineNumbers={true}
              startingLineNumber={1}
              customStyle={{
                margin: 0,
                borderRadius: '0.375rem',
                fontSize: '0.875rem',
              }}
              {...props}
            >
              {String(children).replace(/\n$/, '')}
            </SyntaxHighlighter>
          </div>
        );
      }

      return (
        <code className="bg-gray-100 dark:bg-gray-800 rounded px-1 py-0.5 text-sm">
          {children}
        </code>
      );
    },
    ol({ ordered, start, children, ...props }: any) {
      return <ol className="list-decimal pl-6 mb-4" start={start || 1} {...props}>{children}</ol>;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "px-4 py-6 sm:px-6",
        isUser ? "bg-white dark:bg-neutral-900" : "bg-gray-50 dark:bg-neutral-800/50"
      )}
    >
      <div className="max-w-3xl mx-auto flex space-x-4">
        <div className="flex-shrink-0 mt-1">
          {isUser ? (
            <div className="w-8 h-8 bg-gray-300 dark:bg-gray-600 rounded-full flex items-center justify-center">
              <UserIcon className="w-5 h-5 text-gray-600 dark:text-gray-300" />
            </div>
          ) : (
            <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
              <BrainIcon className="w-5 h-5 text-white" />
            </div>
          )}
        </div>
        <div className="flex-1 markdown-body">
          {isPending && isLast ? (
            <div className="flex items-center">
              <div className="animate-pulse flex space-x-1">
                <div className="w-1.5 h-1.5 bg-current rounded-full" />
                <div className="w-1.5 h-1.5 bg-current rounded-full animation-delay-200" />
                <div className="w-1.5 h-1.5 bg-current rounded-full animation-delay-400" />
              </div>
            </div>
          ) : typeof message.content === 'string' ? (
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkBreaks]}
              components={CodeBlock}
              className="prose dark:prose-invert max-w-none"
            >
              {message.content}
            </ReactMarkdown>
          ) : message.content.type === 'image' && message.content.image ? (
            <div className="my-2">
              <img
                src={message.content.image.url}
                alt={message.content.image.file_name || 'Uploaded image'}
                className="max-w-full rounded-lg max-h-64 object-contain"
              />
            </div>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkBreaks]}
              components={CodeBlock}
              className="prose dark:prose-invert max-w-none"
            >
              {message.content.text || ''}
            </ReactMarkdown>
          )
          )}
        </div>
      </div>
    </motion.div>
  );
};