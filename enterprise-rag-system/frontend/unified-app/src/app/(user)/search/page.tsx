'use client';

import { useState } from 'react';
import { Card, Input, Button, Select, Space, Typography, Empty, Spin, Tag, Pagination } from 'antd';
import { SearchOutlined, FilterOutlined, BookOutlined, FileTextOutlined } from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/utils/api';
import { formatDate, highlightSearchTerm } from '@/utils';

const { Search } = Input;
const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

interface SearchResult {
  id: number;
  document_id: number;
  document_title: string;
  content: string;
  relevance_score: number;
  metadata: any;
  highlights?: string[];
}

export default function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState<'semantic' | 'keyword' | 'hybrid'>('hybrid');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);
  const [hasSearched, setHasSearched] = useState(false);

  // 搜索结果查询
  const { data: searchResults, isLoading, refetch } = useQuery({
    queryKey: ['search', searchQuery, searchType, currentPage],
    queryFn: () => apiClient.search({
      query: searchQuery,
      search_type: searchType,
      limit: pageSize,
    }),
    enabled: false, // 手动触发
  });

  const handleSearch = (value: string) => {
    if (value.trim()) {
      setSearchQuery(value.trim());
      setCurrentPage(1);
      setHasSearched(true);
      refetch();
    }
  };

  const handleSearchTypeChange = (type: 'semantic' | 'keyword' | 'hybrid') => {
    setSearchType(type);
    if (searchQuery) {
      refetch();
    }
  };

  const renderSearchResult = (result: SearchResult, index: number) => (
    <motion.div
      key={result.id}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.1 }}
    >
      <Card
        className="mb-4 hover:shadow-lg transition-shadow duration-300 cursor-pointer"
        onClick={() => {
          // 跳转到文档详情
          console.log('查看文档:', result.document_id);
        }}
      >
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <FileTextOutlined className="text-white text-lg" />
            </div>
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-2">
              <Title level={5} className="!mb-0 truncate">
                {result.document_title}
              </Title>
              <div className="flex items-center space-x-2">
                <Tag color="blue">
                  相关度: {(result.relevance_score * 100).toFixed(1)}%
                </Tag>
              </div>
            </div>
            
            <Paragraph
              className="text-gray-600 dark:text-gray-300 mb-3"
              ellipsis={{ rows: 3 }}
            >
              <span
                dangerouslySetInnerHTML={{
                  __html: highlightSearchTerm(result.content, searchQuery)
                }}
              />
            </Paragraph>
            
            <div className="flex items-center justify-between text-sm text-gray-500">
              <div className="flex items-center space-x-4">
                <span>文档ID: {result.document_id}</span>
                {result.metadata?.page_number && (
                  <span>第 {result.metadata.page_number} 页</span>
                )}
              </div>
              <span>{formatDate(new Date(), 'relative')}</span>
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  );

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* 搜索头部 */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6">
        <div className="max-w-4xl mx-auto">
          <Title level={2} className="!mb-4">
            知识搜索
          </Title>
          
          <div className="space-y-4">
            {/* 搜索框 */}
            <Search
              placeholder="输入关键词搜索知识库..."
              allowClear
              enterButton={
                <Button type="primary" icon={<SearchOutlined />}>
                  搜索
                </Button>
              }
              size="large"
              onSearch={handleSearch}
              className="w-full"
            />
            
            {/* 搜索选项 */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <FilterOutlined className="text-gray-500" />
                <Text type="secondary">搜索类型:</Text>
                <Select
                  value={searchType}
                  onChange={handleSearchTypeChange}
                  style={{ width: 120 }}
                >
                  <Option value="hybrid">智能搜索</Option>
                  <Option value="semantic">语义搜索</Option>
                  <Option value="keyword">关键词搜索</Option>
                </Select>
              </div>
              
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <BookOutlined />
                <span>搜索范围: 全部知识库</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 搜索结果 */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
        <div className="max-w-4xl mx-auto">
          <AnimatePresence mode="wait">
            {!hasSearched ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-20"
              >
                <Empty
                  image={
                    <div className="w-24 h-24 mx-auto mb-4 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center">
                      <SearchOutlined className="text-3xl text-white" />
                    </div>
                  }
                  description={
                    <div>
                      <Title level={3} className="!mb-2">开始搜索知识库</Title>
                      <Text type="secondary" className="text-base">
                        输入关键词，从企业知识库中找到您需要的信息
                      </Text>
                    </div>
                  }
                >
                  <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
                    {[
                      '产品使用手册',
                      '技术文档规范',
                      '项目管理流程',
                      '安全操作指南',
                    ].map((suggestion, index) => (
                      <motion.div
                        key={index}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <Card
                          hoverable
                          className="cursor-pointer border-dashed"
                          onClick={() => handleSearch(suggestion)}
                        >
                          <Text className="text-sm">{suggestion}</Text>
                        </Card>
                      </motion.div>
                    ))}
                  </div>
                </Empty>
              </motion.div>
            ) : isLoading ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-20"
              >
                <Spin size="large" />
                <div className="mt-4">
                  <Text type="secondary">正在搜索知识库...</Text>
                </div>
              </motion.div>
            ) : searchResults?.results?.length > 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                {/* 搜索结果统计 */}
                <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <Text strong>
                        找到 {searchResults.total} 个相关结果
                      </Text>
                      <Text type="secondary" className="ml-2">
                        (搜索耗时: {searchResults.query_time}ms)
                      </Text>
                    </div>
                    <Text type="secondary">
                      搜索词: "{searchQuery}"
                    </Text>
                  </div>
                </div>
                
                {/* 搜索结果列表 */}
                <div className="space-y-4">
                  {searchResults.results.map((result, index) => 
                    renderSearchResult(result, index)
                  )}
                </div>
                
                {/* 分页 */}
                {searchResults.total > pageSize && (
                  <div className="mt-8 text-center">
                    <Pagination
                      current={currentPage}
                      total={searchResults.total}
                      pageSize={pageSize}
                      onChange={setCurrentPage}
                      showSizeChanger={false}
                      showQuickJumper
                      showTotal={(total, range) =>
                        `第 ${range[0]}-${range[1]} 条，共 ${total} 条结果`
                      }
                    />
                  </div>
                )}
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-20"
              >
                <Empty
                  description={
                    <div>
                      <Title level={4} className="!mb-2">未找到相关结果</Title>
                      <Text type="secondary">
                        尝试使用不同的关键词或搜索类型
                      </Text>
                    </div>
                  }
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
