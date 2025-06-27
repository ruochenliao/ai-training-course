/**
 * 搜索过滤器组件
 * 提供搜索结果的过滤和排序选项
 */

'use client';

import React from 'react';
import {Button, Card, DatePicker, Divider, InputNumber, Select, Slider, Space, Switch, Tooltip, Typography} from 'antd';
import {FilterOutlined, ReloadOutlined, SaveOutlined} from '@ant-design/icons';
import {useTheme} from '@/contexts/ThemeContext';
import dayjs from 'dayjs';

const { Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

interface SearchFilters {
  documentTypes: string[];
  dateRange: [string, string] | null;
  scoreThreshold: number;
  maxResults: number;
  includeMetadata: boolean;
}

interface SearchFiltersProps {
  filters: SearchFilters;
  onChange: (filters: SearchFilters) => void;
  searchMode: string;
  onReset?: () => void;
  onSave?: (filters: SearchFilters) => void;
  className?: string;
}

export function SearchFilters({
  filters,
  onChange,
  searchMode,
  onReset,
  onSave,
  className = ''
}: SearchFiltersProps) {
  const { theme } = useTheme();

  // 文档类型选项
  const documentTypeOptions = [
    { value: 'pdf', label: 'PDF文档' },
    { value: 'docx', label: 'Word文档' },
    { value: 'pptx', label: 'PowerPoint' },
    { value: 'xlsx', label: 'Excel表格' },
    { value: 'txt', label: '文本文件' },
    { value: 'md', label: 'Markdown' },
    { value: 'html', label: 'HTML页面' },
    { value: 'json', label: 'JSON数据' }
  ];

  // 更新过滤器
  const updateFilter = <K extends keyof SearchFilters>(
    key: K,
    value: SearchFilters[K]
  ) => {
    onChange({
      ...filters,
      [key]: value
    });
  };

  // 重置过滤器
  const handleReset = () => {
    const defaultFilters: SearchFilters = {
      documentTypes: [],
      dateRange: null,
      scoreThreshold: 0.5,
      maxResults: 20,
      includeMetadata: true
    };
    onChange(defaultFilters);
    onReset?.();
  };

  // 保存过滤器配置
  const handleSave = () => {
    onSave?.(filters);
  };

  // 根据搜索模式显示不同的过滤选项
  const getSearchModeSpecificFilters = () => {
    switch (searchMode) {
      case 'semantic':
        return (
          <div className="space-y-4">
            <div>
              <Text strong style={{ color: theme.colors.onSurface }}>
                语义相似度阈值
              </Text>
              <div className="mt-2">
                <Slider
                  min={0}
                  max={1}
                  step={0.1}
                  value={filters.scoreThreshold}
                  onChange={(value) => updateFilter('scoreThreshold', value)}
                  marks={{
                    0: '0%',
                    0.5: '50%',
                    1: '100%'
                  }}
                  tooltip={{
                    formatter: (value) => `${(value! * 100).toFixed(0)}%`
                  }}
                />
              </div>
              <Text 
                className="text-sm"
                style={{ color: theme.colors.onSurfaceVariant }}
              >
                只显示相似度高于此阈值的结果
              </Text>
            </div>
          </div>
        );
      
      case 'graph':
        return (
          <div className="space-y-4">
            <div>
              <Text strong style={{ color: theme.colors.onSurface }}>
                关系跳数限制
              </Text>
              <div className="mt-2">
                <Select
                  value={filters.maxResults <= 10 ? 1 : filters.maxResults <= 20 ? 2 : 3}
                  onChange={(value) => updateFilter('maxResults', value === 1 ? 10 : value === 2 ? 20 : 30)}
                  style={{ width: '100%' }}
                >
                  <Option value={1}>1跳关系</Option>
                  <Option value={2}>2跳关系</Option>
                  <Option value={3}>3跳关系</Option>
                </Select>
              </div>
              <Text 
                className="text-sm"
                style={{ color: theme.colors.onSurfaceVariant }}
              >
                限制图谱搜索的关系推理深度
              </Text>
            </div>
          </div>
        );
      
      case 'hybrid':
        return (
          <div className="space-y-4">
            <div>
              <Text strong style={{ color: theme.colors.onSurface }}>
                混合权重配置
              </Text>
              <div className="mt-2 space-y-2">
                <div className="flex items-center justify-between">
                  <Text style={{ color: theme.colors.onSurfaceVariant }}>
                    BM25权重
                  </Text>
                  <InputNumber
                    min={0}
                    max={1}
                    step={0.1}
                    value={0.3}
                    onChange={() => {}}
                    size="small"
                    style={{ width: 80 }}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Text style={{ color: theme.colors.onSurfaceVariant }}>
                    语义权重
                  </Text>
                  <InputNumber
                    min={0}
                    max={1}
                    step={0.1}
                    value={0.7}
                    onChange={() => {}}
                    size="small"
                    style={{ width: 80 }}
                  />
                </div>
              </div>
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <Card
      size="small"
      className={className}
      style={{ 
        backgroundColor: theme.colors.surfaceVariant,
        borderColor: theme.colors.outline
      }}
      title={
        <div className="flex items-center gap-2">
          <FilterOutlined style={{ color: theme.colors.primary }} />
          <Text strong style={{ color: theme.colors.onSurface }}>
            搜索过滤器
          </Text>
        </div>
      }
      extra={
        <Space size="small">
          <Tooltip title="重置过滤器">
            <Button 
              size="small" 
              icon={<ReloadOutlined />} 
              onClick={handleReset}
            />
          </Tooltip>
          <Tooltip title="保存配置">
            <Button 
              size="small" 
              icon={<SaveOutlined />} 
              onClick={handleSave}
            />
          </Tooltip>
        </Space>
      }
    >
      <div className="space-y-4">
        {/* 文档类型过滤 */}
        <div>
          <Text strong style={{ color: theme.colors.onSurface }}>
            文档类型
          </Text>
          <div className="mt-2">
            <Select
              mode="multiple"
              placeholder="选择文档类型"
              value={filters.documentTypes}
              onChange={(value) => updateFilter('documentTypes', value)}
              style={{ width: '100%' }}
              maxTagCount={3}
            >
              {documentTypeOptions.map(option => (
                <Option key={option.value} value={option.value}>
                  {option.label}
                </Option>
              ))}
            </Select>
          </div>
        </div>

        {/* 时间范围过滤 */}
        <div>
          <Text strong style={{ color: theme.colors.onSurface }}>
            时间范围
          </Text>
          <div className="mt-2">
            <RangePicker
              value={filters.dateRange ? [
                dayjs(filters.dateRange[0]),
                dayjs(filters.dateRange[1])
              ] : null}
              onChange={(dates) => {
                if (dates && dates[0] && dates[1]) {
                  updateFilter('dateRange', [
                    dates[0].toISOString(),
                    dates[1].toISOString()
                  ]);
                } else {
                  updateFilter('dateRange', null);
                }
              }}
              style={{ width: '100%' }}
              placeholder={['开始日期', '结束日期']}
            />
          </div>
        </div>

        {/* 结果数量限制 */}
        <div>
          <Text strong style={{ color: theme.colors.onSurface }}>
            最大结果数
          </Text>
          <div className="mt-2">
            <Select
              value={filters.maxResults}
              onChange={(value) => updateFilter('maxResults', value)}
              style={{ width: '100%' }}
            >
              <Option value={10}>10个结果</Option>
              <Option value={20}>20个结果</Option>
              <Option value={50}>50个结果</Option>
              <Option value={100}>100个结果</Option>
            </Select>
          </div>
        </div>

        <Divider style={{ margin: '16px 0' }} />

        {/* 搜索模式特定过滤器 */}
        {getSearchModeSpecificFilters()}

        <Divider style={{ margin: '16px 0' }} />

        {/* 高级选项 */}
        <div className="space-y-3">
          <Text strong style={{ color: theme.colors.onSurface }}>
            高级选项
          </Text>
          
          <div className="flex items-center justify-between">
            <div>
              <Text style={{ color: theme.colors.onSurface }}>
                包含元数据
              </Text>
              <div>
                <Text 
                  className="text-sm"
                  style={{ color: theme.colors.onSurfaceVariant }}
                >
                  在结果中显示文档元数据信息
                </Text>
              </div>
            </div>
            <Switch
              checked={filters.includeMetadata}
              onChange={(checked) => updateFilter('includeMetadata', checked)}
            />
          </div>
        </div>

        {/* 过滤器摘要 */}
        <div 
          className="p-3 rounded-lg"
          style={{ 
            backgroundColor: theme.colors.background,
            border: `1px solid ${theme.colors.outline}`
          }}
        >
          <Text 
            className="text-sm"
            style={{ color: theme.colors.onSurfaceVariant }}
          >
            <strong>当前过滤器:</strong> {' '}
            {filters.documentTypes.length > 0 && `文档类型(${filters.documentTypes.length}) `}
            {filters.dateRange && '时间范围 '}
            {filters.scoreThreshold > 0 && `相关性>${(filters.scoreThreshold * 100).toFixed(0)}% `}
            最多{filters.maxResults}个结果
          </Text>
        </div>
      </div>
    </Card>
  );
}
