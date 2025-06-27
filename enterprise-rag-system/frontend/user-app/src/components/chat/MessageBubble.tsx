/**
 * 消息气泡组件
 * 支持文本、图片、代码高亮、LaTeX公式等多种内容类型
 */

'use client';

import React, {useState} from 'react';
import {motion} from 'framer-motion';
import {Avatar, Button, Collapse, Tag, Tooltip} from 'antd';
import {
    ClockCircleOutlined,
    CopyOutlined,
    DislikeOutlined,
    LikeOutlined,
    RobotOutlined,
    SearchOutlined,
    SettingOutlined,
    UserOutlined
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import {Prism as SyntaxHighlighter} from 'react-syntax-highlighter';
import {oneDark, oneLight} from 'react-syntax-highlighter/dist/esm/styles/prism';
import 'katex/dist/katex.min.css';
import {useTheme} from '@/contexts/ThemeContext';
import {formatDistanceToNow} from 'date-fns';
import {zhCN} from 'date-fns/locale';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  images?: string[];
  metadata?: {
    searchResults?: any[];
    processingTime?: number;
    agentUsed?: boolean;
  };
}

interface MessageBubbleProps {
  message: Message;
  onCopy?: (content: string) => void;
  onLike?: (messageId: string) => void;
  onDislike?: (messageId: string) => void;
}

export function MessageBubble({ 
  message, 
  onCopy, 
  onLike, 
  onDislike 
}: MessageBubbleProps) {
  const { theme, isDark } = useTheme();
  const [showMetadata, setShowMetadata] = useState(false);
  
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  
  // 获取头像
  const getAvatar = () => {
    if (isUser) {
      return <Avatar icon={<UserOutlined />} style={{ backgroundColor: theme.colors.primary }} />;
    } else if (isSystem) {
      return <Avatar icon={<SettingOutlined />} style={{ backgroundColor: theme.colors.secondary }} />;
    } else {
      return <Avatar icon={<RobotOutlined />} style={{ backgroundColor: theme.colors.success }} />;
    }
  };

  // 获取消息气泡样式
  const getBubbleStyle = () => {
    if (isUser) {
      return {
        backgroundColor: theme.colors.userMessage,
        color: isDark ? theme.colors.onBackground : '#ffffff',
        marginLeft: '20%'
      };
    } else if (isSystem) {
      return {
        backgroundColor: theme.colors.systemMessage,
        color: theme.colors.onSurface,
        marginRight: '20%'
      };
    } else {
      return {
        backgroundColor: theme.colors.assistantMessage,
        color: theme.colors.onSurface,
        marginRight: '20%',
        border: `1px solid ${theme.colors.outline}`
      };
    }
  };

  // 复制消息内容
  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    onCopy?.(message.content);
  };

  // 处理代码块渲染
  const renderCode = ({ node, inline, className, children, ...props }: any) => {
    const match = /language-(\w+)/.exec(className || '');
    const language = match ? match[1] : '';
    
    if (!inline && language) {
      return (
        <SyntaxHighlighter
          style={isDark ? oneDark : oneLight}
          language={language}
          PreTag="div"
          {...props}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      );
    }
    
    return (
      <code 
        className={className} 
        style={{ 
          backgroundColor: theme.colors.surfaceVariant,
          color: theme.colors.onSurfaceVariant,
          padding: '2px 4px',
          borderRadius: '4px',
          fontSize: '0.9em'
        }}
        {...props}
      >
        {children}
      </code>
    );
  };

  // 处理LaTeX数学公式
  const renderMath = (content: string) => {
    // 处理块级数学公式 $$...$$
    const blockMathRegex = /\$\$([\s\S]*?)\$\$/g;
    // 处理行内数学公式 $...$
    const inlineMathRegex = /\$([^$\n]+?)\$/g;
    
    let processedContent = content;
    
    // 替换块级数学公式
    processedContent = processedContent.replace(blockMathRegex, (match, formula) => {
      return `<BlockMath>${formula}</BlockMath>`;
    });
    
    // 替换行内数学公式
    processedContent = processedContent.replace(inlineMathRegex, (match, formula) => {
      return `<InlineMath>${formula}</InlineMath>`;
    });
    
    return processedContent;
  };

  // 自定义Markdown组件
  const markdownComponents = {
    code: renderCode,
    // 自定义链接样式
    a: ({ href, children, ...props }: any) => (
      <a 
        href={href} 
        target="_blank" 
        rel="noopener noreferrer"
        style={{ color: theme.colors.primary }}
        {...props}
      >
        {children}
      </a>
    ),
    // 自定义表格样式
    table: ({ children, ...props }: any) => (
      <div style={{ overflowX: 'auto' }}>
        <table 
          style={{ 
            width: '100%',
            borderCollapse: 'collapse',
            border: `1px solid ${theme.colors.outline}`
          }}
          {...props}
        >
          {children}
        </table>
      </div>
    ),
    th: ({ children, ...props }: any) => (
      <th 
        style={{ 
          padding: '8px 12px',
          backgroundColor: theme.colors.surfaceVariant,
          border: `1px solid ${theme.colors.outline}`,
          textAlign: 'left'
        }}
        {...props}
      >
        {children}
      </th>
    ),
    td: ({ children, ...props }: any) => (
      <td 
        style={{ 
          padding: '8px 12px',
          border: `1px solid ${theme.colors.outline}`
        }}
        {...props}
      >
        {children}
      </td>
    )
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
    >
      <div className={`flex ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start gap-3 max-w-[80%]`}>
        {/* 头像 */}
        <div className="flex-shrink-0">
          {getAvatar()}
        </div>
        
        {/* 消息内容 */}
        <div className="flex-1">
          {/* 消息气泡 */}
          <div
            className="rounded-2xl px-4 py-3 shadow-sm"
            style={getBubbleStyle()}
          >
            {/* 图片内容 */}
            {message.images && message.images.length > 0 && (
              <div className="mb-3 grid grid-cols-2 gap-2">
                {message.images.map((image, index) => (
                  <img
                    key={index}
                    src={image}
                    alt={`消息图片 ${index + 1}`}
                    className="rounded-lg max-w-full h-auto cursor-pointer hover:opacity-80 transition-opacity"
                    onClick={() => {
                      // 可以添加图片预览功能
                      window.open(image, '_blank');
                    }}
                  />
                ))}
              </div>
            )}
            
            {/* 文本内容 */}
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown components={markdownComponents}>
                {renderMath(message.content)}
              </ReactMarkdown>
            </div>
          </div>
          
          {/* 消息元信息 */}
          <div className={`flex items-center gap-2 mt-2 px-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
            <span 
              className="text-xs"
              style={{ color: theme.colors.onSurfaceVariant }}
            >
              {formatDistanceToNow(message.timestamp, { 
                addSuffix: true, 
                locale: zhCN 
              })}
            </span>
            
            {/* 处理时间标签 */}
            {message.metadata?.processingTime && (
              <Tag 
                icon={<ClockCircleOutlined />} 
                size="small"
                style={{ 
                  backgroundColor: theme.colors.surfaceVariant,
                  color: theme.colors.onSurfaceVariant,
                  border: 'none'
                }}
              >
                {message.metadata.processingTime}ms
              </Tag>
            )}
            
            {/* 智能体使用标签 */}
            {message.metadata?.agentUsed && (
              <Tag 
                icon={<RobotOutlined />} 
                size="small"
                color="blue"
              >
                智能体
              </Tag>
            )}
            
            {/* 操作按钮 */}
            <div className="flex items-center gap-1">
              <Tooltip title="复制">
                <Button 
                  type="text" 
                  size="small" 
                  icon={<CopyOutlined />}
                  onClick={handleCopy}
                  style={{ color: theme.colors.onSurfaceVariant }}
                />
              </Tooltip>
              
              {!isUser && (
                <>
                  <Tooltip title="有用">
                    <Button 
                      type="text" 
                      size="small" 
                      icon={<LikeOutlined />}
                      onClick={() => onLike?.(message.id)}
                      style={{ color: theme.colors.onSurfaceVariant }}
                    />
                  </Tooltip>
                  
                  <Tooltip title="无用">
                    <Button 
                      type="text" 
                      size="small" 
                      icon={<DislikeOutlined />}
                      onClick={() => onDislike?.(message.id)}
                      style={{ color: theme.colors.onSurfaceVariant }}
                    />
                  </Tooltip>
                </>
              )}
              
              {message.metadata?.searchResults && (
                <Tooltip title="查看搜索结果">
                  <Button 
                    type="text" 
                    size="small" 
                    icon={<SearchOutlined />}
                    onClick={() => setShowMetadata(!showMetadata)}
                    style={{ color: theme.colors.onSurfaceVariant }}
                  />
                </Tooltip>
              )}
            </div>
          </div>
          
          {/* 搜索结果展开面板 */}
          {showMetadata && message.metadata?.searchResults && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-3"
            >
              <Collapse
                size="small"
                items={[
                  {
                    key: 'search-results',
                    label: `搜索结果 (${message.metadata.searchResults.length}条)`,
                    children: (
                      <div className="space-y-2">
                        {message.metadata.searchResults.map((result, index) => (
                          <div 
                            key={index}
                            className="p-3 rounded-lg"
                            style={{ 
                              backgroundColor: theme.colors.surfaceVariant,
                              border: `1px solid ${theme.colors.outline}`
                            }}
                          >
                            <div className="text-sm font-medium mb-1">
                              {result.title || `结果 ${index + 1}`}
                            </div>
                            <div 
                              className="text-xs"
                              style={{ color: theme.colors.onSurfaceVariant }}
                            >
                              {result.content || result.text}
                            </div>
                            {result.score && (
                              <div className="mt-1">
                                <Tag size="small">
                                  相关性: {(result.score * 100).toFixed(1)}%
                                </Tag>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )
                  }
                ]}
              />
            </motion.div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
