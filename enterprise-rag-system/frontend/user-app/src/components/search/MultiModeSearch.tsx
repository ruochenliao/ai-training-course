/**
 * 多模式搜索界面组件
 * 支持语义搜索、图谱搜索、混合搜索三种模式
 */

'use client';

import React, {useState} from 'react';
import {AnimatePresence, motion} from 'framer-motion';
import {Button, Card, Empty, Input, List, Select, Space, Spin, Tabs, Tag, Tooltip, Typography} from 'antd';
import {
    BookOutlined,
    FilterOutlined,
    NodeIndexOutlined,
    SearchOutlined,
    ShareAltOutlined,
    ThunderboltOutlined
} from '@ant-design/icons';
import {useTheme} from '@/contexts/ThemeContext';
import {SearchResultCard} from './SearchResultCard';
import {SearchFilters} from './SearchFilters';

const { Search } = Input;
const { Text, Title } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;

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

interface SearchFilters {
  documentTypes: string[];
  dateRange: [string, string] | null;
  scoreThreshold: number;
  maxResults: number;
  includeMetadata: boolean;
}

interface MultiModeSearchProps {
  onSearch?: (query: string, mode: string, filters: SearchFilters) => Promise<SearchResult[]>;
  className?: string;
}

export function MultiModeSearch({ onSearch, className = '' }: MultiModeSearchProps) {
  const { theme } = useTheme();
  const [activeTab, setActiveTab] = useState('semantic');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTime, setSearchTime] = useState(0);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({
    documentTypes: [],
    dateRange: null,
    scoreThreshold: 0.5,
    maxResults: 20,
    includeMetadata: true
  });

  // 搜索模式配置
  const searchModes = {
    semantic: {
      title: '语义搜索',
      icon: <BookOutlined />,
      description: '基于Qwen2.5嵌入模型的语义相似度搜索',
      color: theme.colors.primary
    },
    graph: {
      title: '图谱搜索',
      icon: <NodeIndexOutlined />,
      description: '基于Neo4j知识图谱的关系推理搜索',
      color: theme.colors.success
    },
    hybrid: {
      title: '混合搜索',
      icon: <ThunderboltOutlined />,
      description: 'BM25关键词搜索与语义搜索的融合',
      color: theme.colors.warning
    }
  };

  // 执行搜索
  const handleSearch = async (query: string = searchQuery) => {
    if (!query.trim()) return;

    setIsLoading(true);
    const startTime = Date.now();

    try {
      const results = await onSearch?.(query, activeTab, filters) || [];
      setSearchResults(results);
      setSearchTime(Date.now() - startTime);
    } catch (error) {
      console.error('搜索失败:', error);
      setSearchResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  // 清空搜索结果
  const handleClear = () => {
    setSearchQuery('');
    setSearchResults([]);
    setSearchTime(0);
  };

  // 分享搜索结果
  const handleShare = () => {
    const shareData = {
      query: searchQuery,
      mode: activeTab,
      results: searchResults.length,
      timestamp: new Date().toISOString()
    };
    
    if (navigator.share) {
      navigator.share({
        title: '搜索结果',
        text: `搜索"${searchQuery}"找到${searchResults.length}个结果`,
        url: window.location.href
      });
    } else {
      navigator.clipboard.writeText(JSON.stringify(shareData, null, 2));
    }
  };

  // 获取搜索统计信息
  const getSearchStats = () => {
    if (!searchResults.length) return null;

    const avgScore = searchResults.reduce((sum, result) => sum + result.score, 0) / searchResults.length;
    const typeDistribution = searchResults.reduce((acc, result) => {
      acc[result.type] = (acc[result.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return { avgScore, typeDistribution };
  };

  const stats = getSearchStats();

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 搜索头部 */}
      <Card style={{ backgroundColor: theme.colors.surface }}>
        <div className="space-y-4">
          {/* 搜索模式选择 */}
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            type="card"
            className="search-mode-tabs"
          >
            {Object.entries(searchModes).map(([key, mode]) => (
              <TabPane
                key={key}
                tab={
                  <div className="flex items-center gap-2">
                    <span style={{ color: mode.color }}>{mode.icon}</span>
                    <span>{mode.title}</span>
                  </div>
                }
              >
                <div className="mb-4">
                  <Text style={{ color: theme.colors.onSurfaceVariant }}>
                    {mode.description}
                  </Text>
                </div>
              </TabPane>
            ))}
          </Tabs>

          {/* 搜索输入框 */}
          <div className="flex items-center gap-2">
            <Search
              placeholder={`使用${searchModes[activeTab as keyof typeof searchModes].title}搜索...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onSearch={handleSearch}
              loading={isLoading}
              size="large"
              style={{ flex: 1 }}
              enterButton={
                <Button 
                  type="primary" 
                  icon={<SearchOutlined />}
                  style={{ 
                    backgroundColor: searchModes[activeTab as keyof typeof searchModes].color,
                    borderColor: searchModes[activeTab as keyof typeof searchModes].color
                  }}
                >
                  搜索
                </Button>
              }
            />
            
            <Tooltip title="搜索过滤器">
              <Button
                icon={<FilterOutlined />}
                onClick={() => setShowFilters(!showFilters)}
                type={showFilters ? 'primary' : 'default'}
              />
            </Tooltip>
            
            <Tooltip title="分享结果">
              <Button
                icon={<ShareAltOutlined />}
                onClick={handleShare}
                disabled={!searchResults.length}
              />
            </Tooltip>
          </div>

          {/* 搜索过滤器 */}
          <AnimatePresence>
            {showFilters && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
              >
                <SearchFilters
                  filters={filters}
                  onChange={setFilters}
                  searchMode={activeTab}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </Card>

      {/* 搜索结果统计 */}
      {searchResults.length > 0 && (
        <Card size="small" style={{ backgroundColor: theme.colors.surface }}>
          <div className="flex items-center justify-between">
            <Space>
              <Text style={{ color: theme.colors.onSurface }}>
                找到 <strong>{searchResults.length}</strong> 个结果
              </Text>
              <Text style={{ color: theme.colors.onSurfaceVariant }}>
                用时 {searchTime}ms
              </Text>
              {stats && (
                <Text style={{ color: theme.colors.onSurfaceVariant }}>
                  平均相关性: {(stats.avgScore * 100).toFixed(1)}%
                </Text>
              )}
            </Space>
            
            <Space>
              {stats && Object.entries(stats.typeDistribution).map(([type, count]) => (
                <Tag key={type} color="blue">
                  {type}: {count}
                </Tag>
              ))}
            </Space>
          </div>
        </Card>
      )}

      {/* 搜索结果列表 */}
      <Card 
        style={{ backgroundColor: theme.colors.surface }}
        bodyStyle={{ padding: 0 }}
      >
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Spin size="large" />
            <Text className="ml-3" style={{ color: theme.colors.onSurfaceVariant }}>
              正在搜索...
            </Text>
          </div>
        ) : searchResults.length > 0 ? (
          <List
            dataSource={searchResults}
            renderItem={(result, index) => (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
              >
                <SearchResultCard
                  result={result}
                  searchQuery={searchQuery}
                  searchMode={activeTab}
                  onResultClick={(result) => {
                    // 处理结果点击
                    console.log('点击搜索结果:', result);
                  }}
                />
              </motion.div>
            )}
          />
        ) : searchQuery ? (
          <Empty
            description={
              <Text style={{ color: theme.colors.onSurfaceVariant }}>
                没有找到相关结果，请尝试其他关键词
              </Text>
            }
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <SearchOutlined 
                style={{ 
                  fontSize: 48, 
                  color: theme.colors.onSurfaceVariant,
                  marginBottom: 16 
                }} 
              />
              <Title level={4} style={{ color: theme.colors.onSurfaceVariant }}>
                开始搜索
              </Title>
              <Text style={{ color: theme.colors.onSurfaceVariant }}>
                输入关键词，选择搜索模式，探索知识库内容
              </Text>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
