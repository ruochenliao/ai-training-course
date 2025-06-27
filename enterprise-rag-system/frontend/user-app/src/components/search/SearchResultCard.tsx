/**
 * 搜索结果卡片组件
 * 显示搜索结果的详细信息和操作
 */

'use client';

import React, {useState} from 'react';
import {motion} from 'framer-motion';
import {Avatar, Button, Card, Collapse, Progress, Space, Tag, Tooltip, Typography} from 'antd';
import {
    CalendarOutlined,
    CopyOutlined,
    EyeOutlined,
    FileTextOutlined,
    LinkOutlined,
    MoreOutlined,
    NodeIndexOutlined,
    ShareAltOutlined,
    TagOutlined,
    UserOutlined
} from '@ant-design/icons';
import {useTheme} from '@/contexts/ThemeContext';
import {formatDistanceToNow} from 'date-fns';
import {zhCN} from 'date-fns/locale';

const { Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface SearchResult {
  id: string;
  title: string;
  content: string;
  score: number;
  source: string;
  type: 'document' | 'chunk' | 'entity' | 'relation';
  metadata: {
    documentId?: string;
    chunkId?: string;
    entityType?: string;
    relationPath?: string[];
    timestamp?: string;
    author?: string;
    tags?: string[];
  };
  highlights?: string[];
}

interface SearchResultCardProps {
  result: SearchResult;
  searchQuery: string;
  searchMode: string;
  onResultClick?: (result: SearchResult) => void;
  onCopy?: (content: string) => void;
  onShare?: (result: SearchResult) => void;
  className?: string;
}

export function SearchResultCard({
  result,
  searchQuery,
  searchMode,
  onResultClick,
  onCopy,
  onShare,
  className = ''
}: SearchResultCardProps) {
  const { theme } = useTheme();
  const [showMetadata, setShowMetadata] = useState(false);

  // 获取结果类型图标和颜色
  const getTypeConfig = (type: string) => {
    const configs = {
      document: {
        icon: <FileTextOutlined />,
        color: theme.colors.primary,
        label: '文档'
      },
      chunk: {
        icon: <FileTextOutlined />,
        color: theme.colors.info,
        label: '文档片段'
      },
      entity: {
        icon: <NodeIndexOutlined />,
        color: theme.colors.success,
        label: '实体'
      },
      relation: {
        icon: <LinkOutlined />,
        color: theme.colors.warning,
        label: '关系'
      }
    };
    return configs[type as keyof typeof configs] || configs.document;
  };

  const typeConfig = getTypeConfig(result.type);

  // 高亮搜索关键词
  const highlightText = (text: string, query: string) => {
    if (!query) return text;
    
    const regex = new RegExp(`(${query})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark 
          key={index}
          style={{ 
            backgroundColor: theme.colors.primary + '20',
            color: theme.colors.primary,
            padding: '0 2px',
            borderRadius: '2px'
          }}
        >
          {part}
        </mark>
      ) : part
    );
  };

  // 处理复制
  const handleCopy = () => {
    navigator.clipboard.writeText(result.content);
    onCopy?.(result.content);
  };

  // 处理分享
  const handleShare = () => {
    onShare?.(result);
  };

  // 获取相关性分数颜色
  const getScoreColor = (score: number) => {
    if (score >= 0.8) return theme.colors.success;
    if (score >= 0.6) return theme.colors.warning;
    return theme.colors.error;
  };

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      transition={{ duration: 0.2 }}
      className={className}
    >
      <Card
        hoverable
        className="search-result-card"
        style={{ 
          backgroundColor: theme.colors.surface,
          borderColor: theme.colors.outline,
          marginBottom: 16
        }}
        onClick={() => onResultClick?.(result)}
      >
        <div className="space-y-3">
          {/* 头部信息 */}
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3 flex-1">
              {/* 类型图标 */}
              <Avatar
                icon={typeConfig.icon}
                style={{ 
                  backgroundColor: typeConfig.color + '20',
                  color: typeConfig.color
                }}
                size="small"
              />
              
              {/* 标题和来源 */}
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Text 
                    strong 
                    className="text-base"
                    style={{ color: theme.colors.onSurface }}
                  >
                    {highlightText(result.title, searchQuery)}
                  </Text>
                  <Tag 
                    color={typeConfig.color}
                    size="small"
                  >
                    {typeConfig.label}
                  </Tag>
                </div>
                
                <Text 
                  className="text-sm"
                  style={{ color: theme.colors.onSurfaceVariant }}
                >
                  来源: {result.source}
                </Text>
              </div>
            </div>
            
            {/* 相关性分数 */}
            <div className="text-right">
              <div className="flex items-center gap-2">
                <Text 
                  className="text-sm"
                  style={{ color: theme.colors.onSurfaceVariant }}
                >
                  相关性
                </Text>
                <Text 
                  strong
                  style={{ color: getScoreColor(result.score) }}
                >
                  {(result.score * 100).toFixed(1)}%
                </Text>
              </div>
              <Progress
                percent={result.score * 100}
                size="small"
                strokeColor={getScoreColor(result.score)}
                showInfo={false}
                style={{ width: 80 }}
              />
            </div>
          </div>

          {/* 内容预览 */}
          <div>
            <Paragraph
              ellipsis={{ rows: 3, expandable: true, symbol: '展开' }}
              style={{ 
                color: theme.colors.onSurface,
                marginBottom: 0
              }}
            >
              {highlightText(result.content, searchQuery)}
            </Paragraph>
          </div>

          {/* 高亮片段 */}
          {result.highlights && result.highlights.length > 0 && (
            <div className="space-y-2">
              <Text 
                className="text-sm"
                style={{ color: theme.colors.onSurfaceVariant }}
              >
                匹配片段:
              </Text>
              {result.highlights.map((highlight, index) => (
                <div
                  key={index}
                  className="p-2 rounded"
                  style={{ 
                    backgroundColor: theme.colors.surfaceVariant,
                    border: `1px solid ${theme.colors.outline}`
                  }}
                >
                  <Text 
                    className="text-sm"
                    style={{ color: theme.colors.onSurface }}
                  >
                    ...{highlightText(highlight, searchQuery)}...
                  </Text>
                </div>
              ))}
            </div>
          )}

          {/* 元数据和标签 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 flex-wrap">
              {/* 时间戳 */}
              {result.metadata.timestamp && (
                <div className="flex items-center gap-1">
                  <CalendarOutlined style={{ color: theme.colors.onSurfaceVariant }} />
                  <Text 
                    className="text-xs"
                    style={{ color: theme.colors.onSurfaceVariant }}
                  >
                    {formatDistanceToNow(new Date(result.metadata.timestamp), {
                      addSuffix: true,
                      locale: zhCN
                    })}
                  </Text>
                </div>
              )}
              
              {/* 作者 */}
              {result.metadata.author && (
                <div className="flex items-center gap-1">
                  <UserOutlined style={{ color: theme.colors.onSurfaceVariant }} />
                  <Text 
                    className="text-xs"
                    style={{ color: theme.colors.onSurfaceVariant }}
                  >
                    {result.metadata.author}
                  </Text>
                </div>
              )}
              
              {/* 标签 */}
              {result.metadata.tags && result.metadata.tags.length > 0 && (
                <div className="flex items-center gap-1">
                  <TagOutlined style={{ color: theme.colors.onSurfaceVariant }} />
                  <Space size={4}>
                    {result.metadata.tags.slice(0, 3).map(tag => (
                      <Tag key={tag} size="small">
                        {tag}
                      </Tag>
                    ))}
                    {result.metadata.tags.length > 3 && (
                      <Tag size="small">
                        +{result.metadata.tags.length - 3}
                      </Tag>
                    )}
                  </Space>
                </div>
              )}
            </div>
            
            {/* 操作按钮 */}
            <Space size="small">
              <Tooltip title="查看详情">
                <Button 
                  type="text" 
                  size="small" 
                  icon={<EyeOutlined />}
                  onClick={(e) => {
                    e.stopPropagation();
                    onResultClick?.(result);
                  }}
                />
              </Tooltip>
              
              <Tooltip title="复制内容">
                <Button 
                  type="text" 
                  size="small" 
                  icon={<CopyOutlined />}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCopy();
                  }}
                />
              </Tooltip>
              
              <Tooltip title="分享">
                <Button 
                  type="text" 
                  size="small" 
                  icon={<ShareAltOutlined />}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleShare();
                  }}
                />
              </Tooltip>
              
              <Tooltip title="更多信息">
                <Button 
                  type="text" 
                  size="small" 
                  icon={<MoreOutlined />}
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowMetadata(!showMetadata);
                  }}
                />
              </Tooltip>
            </Space>
          </div>

          {/* 详细元数据 */}
          {showMetadata && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
            >
              <Collapse size="small">
                <Panel header="详细信息" key="metadata">
                  <div className="space-y-2 text-sm">
                    <div>
                      <Text strong>结果ID: </Text>
                      <Text code>{result.id}</Text>
                    </div>
                    
                    {result.metadata.documentId && (
                      <div>
                        <Text strong>文档ID: </Text>
                        <Text code>{result.metadata.documentId}</Text>
                      </div>
                    )}
                    
                    {result.metadata.chunkId && (
                      <div>
                        <Text strong>分块ID: </Text>
                        <Text code>{result.metadata.chunkId}</Text>
                      </div>
                    )}
                    
                    {result.metadata.entityType && (
                      <div>
                        <Text strong>实体类型: </Text>
                        <Tag>{result.metadata.entityType}</Tag>
                      </div>
                    )}
                    
                    {result.metadata.relationPath && (
                      <div>
                        <Text strong>关系路径: </Text>
                        <div className="mt-1">
                          {result.metadata.relationPath.map((path, index) => (
                            <Tag key={index} color="blue">
                              {path}
                            </Tag>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <div>
                      <Text strong>搜索模式: </Text>
                      <Tag color="green">{searchMode}</Tag>
                    </div>
                  </div>
                </Panel>
              </Collapse>
            </motion.div>
          )}
        </div>
      </Card>
    </motion.div>
  );
}
