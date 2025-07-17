'use client'

import React, { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { Brain, AlertCircle, Copy, Image as ImageIcon } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { sendStreamingChatRequest, AVAILABLE_MODELS, createSession, getSession, uploadImage } from './api'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { tomorrow as codeTheme } from 'react-syntax-highlighter/dist/esm/styles/prism'
import remarkGfm from 'remark-gfm'
import remarkBreaks from 'remark-breaks'
import type { Message, MessageContent, ImageContent } from './types'
import { Toast } from '@/components/Toast'

// Define CodeBlock for markdown rendering
const CodeBlock = {
  pre({ node, ...props }) {
    return <pre className="bg-gray-50 dark:bg-neutral-900 rounded-xl p-4 my-3 overflow-auto" {...props} />;
  },
  code({ node, inline, className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || '');
    if (!inline && match) {
      const language = match[1];
      return (
        <SyntaxHighlighter
          language={language}
          style={codeTheme}
          showLineNumbers={true}
          customStyle={{
            borderRadius: '0.75rem',
            padding: '1.25rem',
            margin: 0,
            backgroundColor: 'var(--code-bg)',
          }}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      );
    }
    return (
      <code className="bg-blue-100 dark:bg-blue-900/40 text-blue-900 dark:text-blue-200 rounded-md px-2.5 py-1 font-mono text-sm" {...props}>
        {children}
      </code>
    );
  }
};

export default function CustomerServicePage() {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [messages, setMessages] = useState<Message[]>([]);
  const [userId, setUserId] = useState<string>(() => {
    // 从localStorage获取用户ID，如果没有则生成一个新的
    if (typeof window !== 'undefined') {
      const storedUserId = localStorage.getItem('chatUserId')
      if (storedUserId) return storedUserId
    }
    const newUserId = `user_${Date.now()}`
    if (typeof window !== 'undefined') {
      localStorage.setItem('chatUserId', newUserId)
    }
    return newUserId
  });
  const [sessionId, setSessionId] = useState<string | undefined>(() => {
    // 从localStorage获取会话ID
    if (typeof window !== 'undefined') {
      const storedSessionId = localStorage.getItem('chatSessionId')
      return storedSessionId || undefined
    }
    return undefined
  });
  const [inputValue, setInputValue] = useState('');
  const [selectedModel, setSelectedModel] = useState(AVAILABLE_MODELS[1].id);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showToast, setShowToast] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadedImage, setUploadedImage] = useState<ImageContent | null>(null);

  // 创建新会话
  const createNewSession = async () => {
    try {
      const sessionData = await createSession(userId);
      setSessionId(sessionData.session_id);
      if (typeof window !== 'undefined') {
        localStorage.setItem('chatSessionId', sessionData.session_id);
      }

      // 如果会话有历史消息，加载它们
      if (sessionData.messages && sessionData.messages.length > 0) {
        const formattedMessages = sessionData.messages.map((msg: any, index: number) => ({
          id: `history-${index}`,
          role: msg.role,
          content: msg.content,
          status: 'done'
        }));
        setMessages(formattedMessages);
      } else {
        // 清空消息
        setMessages([]);
      }
    } catch (error) {
      console.error('创建会话失败:', error);
      setError('创建会话失败，请稍后重试');
    }
  };

  // 加载会话历史
  const loadSessionHistory = async (sid: string) => {
    try {
      const sessionData = await getSession(sid);
      const formattedMessages = sessionData.messages.map((msg: any, index: number) => ({
        id: `history-${index}`,
        role: msg.role,
        content: msg.content,
        status: 'done'
      }));
      setMessages(formattedMessages);
    } catch (error) {
      console.error('加载会话历史失败:', error);
      // 如果会话不存在，创建新会话
      if (error instanceof Error && error.message === 'Session not found') {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('chatSessionId');
        }
        setSessionId(undefined);
        setMessages([]);
        createNewSession();
      } else {
        setError('加载会话历史失败，请稍后重试');
      }
    }
  };

  // 确定任务类型的函数
  const determineTaskType = (text: string): string => {
    // 分析用户输入，确定任务类型
    const textLower = text.toLowerCase();

    // 判断是否是图片描述任务
    if (textLower.includes('描述') || textLower.includes('说明') ||
        textLower.includes('这是什么') || textLower.includes('识别') ||
        textLower.includes('describe') || textLower.includes('what is this')) {
      return 'image_understanding';
    }

    // 判断是否是图片分析任务
    if (textLower.includes('分析') || textLower.includes('评估') ||
        textLower.includes('问题') || textLower.includes('缺陷') ||
        textLower.includes('analyze') || textLower.includes('issue')) {
      return 'image_analysis';
    }

    // 判断是否是图片比较任务
    if (textLower.includes('比较') || textLower.includes('区别') ||
        textLower.includes('不同') || textLower.includes('相似') ||
        textLower.includes('compare') || textLower.includes('difference')) {
      return 'image_comparison';
    }

    // 判断是否是图片编辑建议任务
    if (textLower.includes('编辑') || textLower.includes('修改') ||
        textLower.includes('改进') || textLower.includes('建议') ||
        textLower.includes('edit') || textLower.includes('suggestion')) {
      return 'image_editing_suggestion';
    }

    // 默认任务类型
    return 'general_image_task';
  };

  // 复制文本的函数
  const handleCopy = (content: string | MessageContent) => {
    let textToCopy = '';

    if (typeof content === 'string') {
      textToCopy = content;
    } else if (content.type === 'text') {
      textToCopy = content.text || '';
    } else if (content.type === 'multi-modal') {
      // 处理多模态消息
      if (content.text) {
        textToCopy += content.text + '\n\n';
      }

      if (content.content) {
        content.content.forEach((item, index) => {
          if (item.image) {
            textToCopy += `[Image ${index+1}: ${item.image.file_name || 'Unnamed image'}] ${item.image.url}\n`;
          }
          if (item.text) {
            textToCopy += `[Text ${index+1}]: ${item.text}\n`;
          }
        });
      }
    } else {
      textToCopy = JSON.stringify(content);
    }

    navigator.clipboard.writeText(textToCopy);
    setShowToast(true);
  };

  // Markdown 渲染组件
  const MarkdownContent: React.FC<{ content: string | MessageContent }> = ({ content }) => {
    // 如果是对象类型的内容
    if (typeof content !== 'string') {
      // 如果是多模态类型
      if (content.type === 'multi-modal') {
        return (
          <div className="my-2">
            {/* 显示多模态内容列表 */}
            {content.content && content.content.map((item, index) => (
              <div key={index} className="mb-2">
                {/* 显示图片内容 */}
                {item.image && (
                  <div className="mb-2">
                    <img
                      src={`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}${item.image.url}`}
                      alt={item.image.file_name || `Image ${index+1}`}
                      className="max-w-full rounded-lg max-h-64 object-contain"
                    />
                    <div className="text-xs text-gray-500 mt-1">
                      {item.image.file_name || `Image ${index+1}`}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* 只在底部显示文本内容 */}
            {content.text && (
              <div className="mb-2">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm, remarkBreaks]}
                  components={CodeBlock}
                  className="prose dark:prose-invert max-w-none"
                >
                  {content.text}
                </ReactMarkdown>
              </div>
            )}
          </div>
        );
      }
      // 如果是文本类型
      else if (content.type === 'text') {
        content = content.text || '';
      }
      else {
        // 其他类型处理
        content = JSON.stringify(content);
      }
    }
    return (
      <div className="relative group">
        <button
          onClick={() => handleCopy(content)}
          className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity
            bg-gray-100 dark:bg-neutral-700 hover:bg-gray-200 dark:hover:bg-neutral-600
            rounded-full p-1.5 shadow-sm"
          title="复制全部内容"
        >
          <Copy className="h-4 w-4 text-gray-600 dark:text-gray-300" />
        </button>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            pre({ node, ...props }) {
              return <pre className="bg-gray-50 dark:bg-neutral-900 rounded-xl p-4 my-3 overflow-auto" {...props} />;
            },
            code({ node, inline, className, children, ...props }: any) {
              const match = /language-(\w+)/.exec(className || '');
              if (!inline && match) {
                const language = match[1];
                return (
                  <div className="relative group my-4 code-block-container">
                    {/* Language indicator */}
                    <div className="language-indicator">
                      {language}
                    </div>

                    {/* Copy button */}
                    <button
                      className="copy-button"
                      onClick={() => handleCopy(String(children))}
                    >
                      <Copy className="h-3.5 w-3.5" />
                      复制
                    </button>

                    {/* Code block */}
                    <div className="code-block-wrapper overflow-hidden rounded-xl border border-gray-200 dark:border-neutral-800 shadow-md">
                      <SyntaxHighlighter
                        language={language}
                        style={codeTheme}
                        showLineNumbers={true}
                        startingLineNumber={1}
                        lineNumberStyle={{
                          minWidth: '2.5em',
                          paddingRight: '1em',
                          marginRight: '1em',
                          textAlign: 'right',
                          color: '#969896',
                          borderRight: '1px solid #373b41',
                          userSelect: 'none',
                          fontWeight: 'normal',
                          backgroundColor: 'transparent',
                        }}
                        customStyle={{
                          borderRadius: '0.75rem',
                          padding: '1.25rem',
                          paddingTop: '1.5rem',
                          paddingRight: '2.5rem', // 为复制按钮留出更多空间
                          margin: 0,
                          backgroundColor: 'var(--code-bg)',
                          fontSize: '1rem',
                          lineHeight: '1.7',
                          fontWeight: '600',
                          letterSpacing: '0.01em',
                        }}
                        codeTagProps={{
                          style: {
                            fontFamily: 'var(--font-mono), Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                          }
                        }}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    </div>
                  </div>
                );
              }
              return (
                <code className="bg-blue-100 dark:bg-blue-900/40 text-blue-900 dark:text-blue-200 rounded-md px-2.5 py-1 font-mono text-sm font-semibold tracking-tight" {...props}>
                  {children}
                </code>
              );
            },
            p: ({ children }) => <p className="mb-4 last:mb-0">{children}</p>,
            ul: ({ children }) => <ul className="list-disc pl-6 mb-4 last:mb-0">{children}</ul>,
            ol: ({ children, ordered, start }) => {
              return <ol className="list-decimal pl-6 mb-4 last:mb-0" start={start || 1}>{children}</ol>;
            },
            li: ({ children }) => <li className="mb-1">{children}</li>,
            a: ({ href, children }) => (
              <a href={href} className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">
                {children}
              </a>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    );
  };

  // 自动滚动到最新消息
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  // 在组件加载时，尝试从本地存储获取会话ID或创建新会话
  useEffect(() => {
    if (sessionId && sessionId.trim() !== '') {
      loadSessionHistory(sessionId);
    } else {
      createNewSession();
    }
  }, []);

  useEffect(() => {
    scrollToBottom()
  }, [messages]);

  const handleImageUpload = async () => {
    if (fileInputRef.current?.files?.length) {
      const file = fileInputRef.current.files[0];
      setIsUploading(true);
      setError(null);

      try {
        const imageData = await uploadImage(file, sessionId, userId);

        // 设置上传的图片信息
        setUploadedImage({
          url: imageData.url,
          file_name: imageData.file_name
        });

        // 显示成功消息
        setError(null);
      } catch (error) {
        console.error('Image upload error:', error);
        setError(error instanceof Error ? error.message : '图片上传失败');
      } finally {
        setIsUploading(false);

        // 清空文件输入
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    }
  };

  // 移除已上传的图片
  const removeUploadedImage = () => {
    setUploadedImage(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // 如果没有文本输入且没有图片，或者正在加载中，则不处理
    if ((!inputValue.trim() && !uploadedImage) || isLoading) return;

    setError(null);

    // 创建用户消息内容
    let messageContent: string | MessageContent;

    // 如果有图片和文本，创建复合消息
    if (uploadedImage && inputValue.trim()) {
      // 分析用户输入，确定任务类型
      const taskType = determineTaskType(inputValue.trim());

      // 创建多模态消息，参考AutoGen的MultiModalMessage格式
      messageContent = {
        type: 'multi-modal',
        text: inputValue.trim(),
        content: [
          {
            image: uploadedImage
          },
          {
            text: inputValue.trim()
          }
        ],
        task: taskType
      };
    }
    // 如果只有图片
    else if (uploadedImage) {
      messageContent = {
        type: 'multi-modal',
        content: [
          {
            image: uploadedImage
          }
        ],
        task: 'image_understanding' // 默认任务类型
      };
    }
    // 如果只有文本
    else {
      messageContent = inputValue;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: messageContent,
      status: 'done'
    };

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      status: 'streaming'
    };

    setMessages(prev => [...prev, userMessage, assistantMessage]);
    setInputValue('');
    setUploadedImage(null); // 清除已上传的图片
    setIsLoading(true);

    try {
      await sendStreamingChatRequest(
        {
          messages: [{
            role: userMessage.role,
            content: userMessage.content
          }],
          model: selectedModel,
          user_id: userId,
          session_id: sessionId || undefined,
        },
        // 处理每个数据块
        (chunk: string) => {
          setMessages(prev => prev.map(msg =>
            msg.id === assistantMessage.id
              ? { ...msg, content: msg.content + chunk, status: 'streaming' }
              : msg
          ));
        },
        // 完成回调
        () => {
          setMessages(prev => prev.map(msg =>
            msg.id === assistantMessage.id
              ? { ...msg, status: 'done' }
              : msg
          ));
          setIsLoading(false);
        },
        // 错误处理
        (error: Error) => {
          console.error('Chat error:', error);
          setError(error.message);
          setMessages(prev => prev.map(msg =>
            msg.id === assistantMessage.id
              ? { ...msg, content: '抱歉，发生了错误。请稍后重试。', status: 'error' }
              : msg
          ));
          setIsLoading(false);
        }
      );
    } catch (error) {
      console.error('Chat error:', error);
      setError(error instanceof Error ? error.message : '发生未知错误');
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#f8f9fd] dark:bg-neutral-900">
      <div className="wave-bg"></div>
      <div className="gemini-bg-dots absolute inset-0 oopacity-10 z-0"></div>

      {/* 导航栏 */}
      <nav className="gemini-navbar">
        <div className="container mx-auto flex items-center justify-between py-3 px-4">
          <Link href="/" className="flex items-center space-x-2">
            <div className="h-9 w-9 relative overflow-hidden rounded-full bg-gradient-to-r from-blue-500 to-purple-600 p-2 shadow-md">
              <Brain className="h-full w-full text-white" />
            </div>
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">但问智能体平台</h1>
          </Link>
          <div className="hidden md:flex gap-6">
            <Link href="/customer-service" className="text-sm font-medium text-blue-600 dark:text-blue-400 relative after:content-[''] after:absolute after:left-0 after:bottom-[-4px] after:w-full after:h-[2px] after:bg-blue-600 dark:after:bg-blue-400">
              智能客服
            </Link>
            <Link href="/text2sql" className="text-sm font-medium text-neutral-600 hover:text-blue-600 dark:text-neutral-300 dark:hover:text-blue-400 transition-colors">
              Text2SQL
            </Link>
            <Link href="/knowledge-base" className="text-sm font-medium text-neutral-600 hover:text-blue-600 dark:text-neutral-300 dark:hover:text-blue-400 transition-colors">
              知识库问答
            </Link>
            <Link href="/copywriting" className="text-sm font-medium text-neutral-600 hover:text-blue-600 dark:text-neutral-300 dark:hover:text-blue-400 transition-colors">
              文案创作
            </Link>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={createNewSession}
              className="px-3 py-1.5 text-sm rounded-md bg-blue-50 text-blue-600 hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-300 dark:hover:bg-blue-900/50 transition-colors"
              title="创建新会话"
            >
              新对话
            </button>
            <Link
              href="/dashboard"
              className="gemini-button-primary"
            >
              控制台
            </Link>
          </div>
        </div>
      </nav>

      {/* 主要内容区域 */}
      <main className="flex-1 w-full max-w-3xl mx-auto px-4 pt-20 pb-24">
        {/* 消息列表容器 */}
        <div className="space-y-6 mb-6">
          <AnimatePresence initial={false}>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`
                  flex items-start gap-4 max-w-[85%]
                  ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}
                `}>
                  {/* 头像 */}
                  <div className={`
                    w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                    ${message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gradient-to-br from-blue-500 to-purple-600 text-white'
                    }
                  `}>
                    {message.role === 'user' ? 'U' : 'AI'}
                  </div>

                  {/* 消息气泡 */}
                  <div className={`
                    rounded-2xl px-4 py-2.5
                    ${message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white dark:bg-neutral-800 shadow-sm border border-gray-100 dark:border-neutral-700'
                    }
                  `}>
                    {message.role === 'assistant' ? (
                      <div className="prose dark:prose-invert max-w-none">
                        <MarkdownContent content={message.content} />
                        {message.status === 'streaming' && (
                          <span className="inline-block w-2 h-4 ml-1 bg-blue-500 animate-pulse" />
                        )}
                      </div>
                    ) : (
                      <div className="whitespace-pre-wrap">
                        {typeof message.content === 'string' ? (
                          message.content
                        ) : message.content.type === 'multi-modal' ? (
                          <div>
                            {/* 显示多模态内容列表 */}
                            {message.content.content && message.content.content.map((item, index) => (
                              <div key={index} className="mb-2">
                                {/* 显示图片内容 */}
                                {item.image && (
                                  <div className="mb-2">
                                    <img
                                      src={`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}${item.image.url}`}
                                      alt={item.image.file_name || `Image ${index+1}`}
                                      className="max-w-full rounded-lg max-h-64 object-contain"
                                    />
                                  </div>
                                )}
                              </div>
                            ))}

                            {/* 只在底部显示文本内容 */}
                            {message.content.text && (
                              <div>{message.content.text}</div>
                            )}
                          </div>
                        ) : (
                          message.content.text || ''
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-[#f8f9fd] via-[#f8f9fd] to-transparent dark:from-neutral-900 dark:via-neutral-900 pb-6 pt-4">
          <div className="max-w-3xl mx-auto px-4">
            <form onSubmit={handleSubmit} className="relative">
              {/* 已上传图片预览 */}
              {uploadedImage && (
                <div className="mb-2 relative">
                  <div className="relative inline-block">
                    <img
                      src={`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}${uploadedImage.url}`}
                      alt={uploadedImage.file_name || 'Uploaded image'}
                      className="h-20 rounded-lg object-contain border border-gray-200 dark:border-neutral-700"
                    />
                    <button
                      type="button"
                      onClick={removeUploadedImage}
                      className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center"
                      aria-label="移除图片"
                    >
                      &times;
                    </button>
                  </div>
                </div>
              )}

              <div className="flex items-center">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isLoading || isUploading || uploadedImage !== null}
                  className={`
                    absolute left-2 top-1/2 -translate-y-1/2
                    w-8 h-8 rounded-full flex items-center justify-center
                    transition-all duration-200
                    ${isLoading || isUploading || uploadedImage !== null ? 'opacity-50 cursor-not-allowed' : 'text-gray-500 hover:text-blue-500'}
                  `}
                >
                  <ImageIcon className="w-5 h-5" />
                </button>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleImageUpload}
                  accept="image/*"
                  className="hidden"
                  disabled={isLoading || isUploading || uploadedImage !== null}
                />
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder={uploadedImage ? '请输入对图片的描述...' : '输入您的问题...'}
                  className="w-full h-12 pl-12 pr-12 rounded-full bg-white dark:bg-neutral-800
                    border border-gray-200 dark:border-neutral-700
                    focus:border-blue-500 dark:focus:border-blue-500
                    focus:ring-2 focus:ring-blue-500/20 dark:focus:ring-blue-500/20
                    focus:outline-none
                    shadow-sm"
                  disabled={isLoading || isUploading}
                />
                <button
                  type="submit"
                  disabled={isLoading || isUploading || (!inputValue.trim() && !uploadedImage)}
                  className={`
                    absolute right-2 top-1/2 -translate-y-1/2
                    w-8 h-8 rounded-full flex items-center justify-center
                    transition-all duration-200
                    ${(inputValue.trim() || uploadedImage) && !isLoading && !isUploading
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'bg-gray-100 dark:bg-neutral-700 text-gray-400'
                    }
                    ${(isLoading || isUploading) ? 'cursor-not-allowed opacity-70' : ''}
                  `}
                >
                  {isUploading ? (
                    <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                  ) : (
                    <svg
                      viewBox="0 0 24 24"
                      className="w-5 h-5 rotate-90"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M12 5l0 14M12 5l-4 4M12 5l4 4" />
                    </svg>
                  )}
                </button>
              </div>
            </form>

            {error && (
              <div className="mt-3 p-3 rounded-lg bg-red-50 border border-red-200 dark:bg-red-900/20 dark:border-red-800">
                <div className="flex items-center text-sm text-red-800 dark:text-red-300">
                  <AlertCircle className="h-4 w-4 mr-2" />
                  {error}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
      {/* 添加 Toast 组件 */}
      <Toast
        message="已复制到剪贴板"
        isVisible={showToast}
        onClose={() => setShowToast(false)}
      />
    </div>
  );
}
