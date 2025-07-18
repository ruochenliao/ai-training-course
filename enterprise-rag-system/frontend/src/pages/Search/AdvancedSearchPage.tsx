import React, { useState, useEffect } from 'react'
import {
  Card,
  Form,
  Input,
  Select,
  DatePicker,
  Button,
  Space,
  Row,
  Col,
  Tabs,
  Table,
  Tag,
  Tooltip,
  Collapse,
  Slider,
  Switch,
  message,
  Empty,
  Spin
} from 'antd'
import {
  SearchOutlined,
  FilterOutlined,
  ClearOutlined,
  DownloadOutlined,
  EyeOutlined,
  BookOutlined,
  FileTextOutlined,
  TagsOutlined,
  CalendarOutlined
} from '@ant-design/icons'
import { multiAgentChat } from '@/api/multi-agent'
import './AdvancedSearchPage.css'

const { TextArea } = Input
const { Option } = Select
const { RangePicker } = DatePicker
const { TabPane } = Tabs
const { Panel } = Collapse

interface SearchFilters {
  query: string
  searchModes: string[]
  knowledgeBases: number[]
  documentTypes: string[]
  dateRange: [string, string] | null
  minScore: number
  maxResults: number
  includeMetadata: boolean
  semanticSimilarity: number
}

interface SearchResult {
  id: string
  title: string
  content: string
  source: string
  score: number
  type: string
  knowledgeBase: string
  createdAt: string
  metadata: Record<string, any>
  highlights: string[]
}

const AdvancedSearchPage: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [totalResults, setTotalResults] = useState(0)
  const [searchTime, setSearchTime] = useState(0)
  const [activeTab, setActiveTab] = useState('search')
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    searchModes: ['semantic'],
    knowledgeBases: [],
    documentTypes: [],
    dateRange: null,
    minScore: 0.5,
    maxResults: 20,
    includeMetadata: true,
    semanticSimilarity: 0.7
  })

  const searchModeOptions = [
    { value: 'semantic', label: '语义检索', description: '基于向量相似度的语义搜索' },
    { value: 'hybrid', label: '混合检索', description: '结合语义和关键词检索' },
    { value: 'graph', label: '图谱检索', description: '基于知识图谱的关系搜索' },
    { value: 'all', label: '全模式', description: '使用所有检索模式' }
  ]

  const documentTypeOptions = [
    { value: 'pdf', label: 'PDF文档' },
    { value: 'docx', label: 'Word文档' },
    { value: 'txt', label: '文本文件' },
    { value: 'md', label: 'Markdown文档' },
    { value: 'html', label: 'HTML文档' }
  ]

  const knowledgeBaseOptions = [
    { value: 1, label: '技术文档库' },
    { value: 2, label: '产品手册库' },
    { value: 3, label: '法律法规库' },
    { value: 4, label: '企业知识库' }
  ]

  const handleSearch = async () => {
    if (!filters.query.trim()) {
      message.warning('请输入搜索关键词')
      return
    }

    setLoading(true)
    const startTime = Date.now()

    try {
      const response = await multiAgentChat({
        query: filters.query,
        search_modes: filters.searchModes as any,
        top_k: filters.maxResults,
        knowledge_base_ids: filters.knowledgeBases.length > 0 ? filters.knowledgeBases : undefined
      })

      // 模拟搜索结果转换
      const mockResults: SearchResult[] = response.search_results.map((result, index) => ({
        id: `result_${index}`,
        title: `搜索结果 ${index + 1}`,
        content: result.content,
        source: result.source,
        score: result.score,
        type: 'document',
        knowledgeBase: '技术文档库',
        createdAt: '2024-01-15',
        metadata: result.metadata,
        highlights: [result.content.substring(0, 100) + '...']
      }))

      setSearchResults(mockResults)
      setTotalResults(mockResults.length)
      setSearchTime(Date.now() - startTime)
      setActiveTab('results')

    } catch (error) {
      message.error('搜索失败，请重试')
      console.error('搜索错误:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleClearFilters = () => {
    form.resetFields()
    setFilters({
      query: '',
      searchModes: ['semantic'],
      knowledgeBases: [],
      documentTypes: [],
      dateRange: null,
      minScore: 0.5,
      maxResults: 20,
      includeMetadata: true,
      semanticSimilarity: 0.7
    })
    setSearchResults([])
    setTotalResults(0)
  }

  const handleExportResults = () => {
    if (searchResults.length === 0) {
      message.warning('没有搜索结果可导出')
      return
    }

    const csvContent = [
      ['标题', '内容', '来源', '评分', '类型', '知识库', '创建时间'].join(','),
      ...searchResults.map(result => [
        result.title,
        result.content.replace(/,/g, '，'),
        result.source,
        result.score,
        result.type,
        result.knowledgeBase,
        result.createdAt
      ].join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `search_results_${Date.now()}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    message.success('搜索结果已导出')
  }

  const resultColumns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      width: 200,
      render: (title: string, record: SearchResult) => (
        <Space direction="vertical" size="small">
          <span style={{ fontWeight: 600 }}>{title}</span>
          <Space size="small">
            <Tag color="blue" icon={<BookOutlined />}>
              {record.knowledgeBase}
            </Tag>
            <Tag color="green">
              评分: {record.score.toFixed(3)}
            </Tag>
          </Space>
        </Space>
      )
    },
    {
      title: '内容摘要',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (content: string, record: SearchResult) => (
        <div>
          <p style={{ margin: 0, color: '#666' }}>
            {content.length > 150 ? content.substring(0, 150) + '...' : content}
          </p>
          {record.highlights.length > 0 && (
            <div style={{ marginTop: 8 }}>
              {record.highlights.map((highlight, index) => (
                <Tag key={index} color="orange" style={{ marginBottom: 4 }}>
                  {highlight}
                </Tag>
              ))}
            </div>
          )}
        </div>
      )
    },
    {
      title: '来源信息',
      dataIndex: 'source',
      key: 'source',
      width: 150,
      render: (source: string, record: SearchResult) => (
        <Space direction="vertical" size="small">
          <span>{source}</span>
          <Space size="small">
            <Tag icon={<FileTextOutlined />}>{record.type}</Tag>
            <Tag icon={<CalendarOutlined />}>{record.createdAt}</Tag>
          </Space>
        </Space>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_, record: SearchResult) => (
        <Space>
          <Tooltip title="查看详情">
            <Button type="text" icon={<EyeOutlined />} size="small" />
          </Tooltip>
          <Tooltip title="查看元数据">
            <Button type="text" icon={<TagsOutlined />} size="small" />
          </Tooltip>
        </Space>
      )
    }
  ]

  return (
    <div className="advanced-search-page">
      <Card className="search-header" title="高级搜索" size="small">
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="搜索配置" key="search">
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSearch}
              initialValues={filters}
            >
              <Row gutter={[16, 16]}>
                <Col xs={24} lg={16}>
                  <Form.Item
                    label="搜索查询"
                    name="query"
                    rules={[{ required: true, message: '请输入搜索关键词' }]}
                  >
                    <TextArea
                      placeholder="输入您的搜索查询，支持自然语言和关键词搜索..."
                      rows={3}
                      value={filters.query}
                      onChange={(e) => setFilters({ ...filters, query: e.target.value })}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} lg={8}>
                  <Form.Item label="搜索模式" name="searchModes">
                    <Select
                      mode="multiple"
                      placeholder="选择搜索模式"
                      value={filters.searchModes}
                      onChange={(value) => setFilters({ ...filters, searchModes: value })}
                    >
                      {searchModeOptions.map(option => (
                        <Option key={option.value} value={option.value}>
                          <Tooltip title={option.description}>
                            {option.label}
                          </Tooltip>
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Collapse ghost>
                <Panel header="高级筛选选项" key="filters" extra={<FilterOutlined />}>
                  <Row gutter={[16, 16]}>
                    <Col xs={24} md={12}>
                      <Form.Item label="知识库" name="knowledgeBases">
                        <Select
                          mode="multiple"
                          placeholder="选择知识库"
                          value={filters.knowledgeBases}
                          onChange={(value) => setFilters({ ...filters, knowledgeBases: value })}
                        >
                          {knowledgeBaseOptions.map(option => (
                            <Option key={option.value} value={option.value}>
                              {option.label}
                            </Option>
                          ))}
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col xs={24} md={12}>
                      <Form.Item label="文档类型" name="documentTypes">
                        <Select
                          mode="multiple"
                          placeholder="选择文档类型"
                          value={filters.documentTypes}
                          onChange={(value) => setFilters({ ...filters, documentTypes: value })}
                        >
                          {documentTypeOptions.map(option => (
                            <Option key={option.value} value={option.value}>
                              {option.label}
                            </Option>
                          ))}
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col xs={24} md={12}>
                      <Form.Item label="创建时间范围" name="dateRange">
                        <RangePicker
                          style={{ width: '100%' }}
                          onChange={(dates, dateStrings) => 
                            setFilters({ ...filters, dateRange: dateStrings as [string, string] })
                          }
                        />
                      </Form.Item>
                    </Col>
                    <Col xs={24} md={12}>
                      <Form.Item label={`最小相关性评分: ${filters.minScore}`} name="minScore">
                        <Slider
                          min={0}
                          max={1}
                          step={0.1}
                          value={filters.minScore}
                          onChange={(value) => setFilters({ ...filters, minScore: value })}
                        />
                      </Form.Item>
                    </Col>
                    <Col xs={24} md={12}>
                      <Form.Item label={`最大结果数: ${filters.maxResults}`} name="maxResults">
                        <Slider
                          min={5}
                          max={100}
                          step={5}
                          value={filters.maxResults}
                          onChange={(value) => setFilters({ ...filters, maxResults: value })}
                        />
                      </Form.Item>
                    </Col>
                    <Col xs={24} md={12}>
                      <Form.Item label="包含元数据" name="includeMetadata" valuePropName="checked">
                        <Switch
                          checked={filters.includeMetadata}
                          onChange={(checked) => setFilters({ ...filters, includeMetadata: checked })}
                        />
                      </Form.Item>
                    </Col>
                  </Row>
                </Panel>
              </Collapse>

              <Form.Item style={{ marginTop: 24 }}>
                <Space>
                  <Button
                    type="primary"
                    icon={<SearchOutlined />}
                    htmlType="submit"
                    loading={loading}
                    size="large"
                  >
                    开始搜索
                  </Button>
                  <Button
                    icon={<ClearOutlined />}
                    onClick={handleClearFilters}
                    size="large"
                  >
                    清空筛选
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane tab={`搜索结果 (${totalResults})`} key="results">
            <div className="search-results">
              {loading ? (
                <div style={{ textAlign: 'center', padding: '100px 0' }}>
                  <Spin size="large" />
                  <p style={{ marginTop: 16, color: '#666' }}>正在搜索中...</p>
                </div>
              ) : searchResults.length > 0 ? (
                <>
                  <div className="results-header">
                    <Space>
                      <span>
                        找到 <strong>{totalResults}</strong> 个结果，
                        耗时 <strong>{searchTime}ms</strong>
                      </span>
                      <Button
                        icon={<DownloadOutlined />}
                        onClick={handleExportResults}
                        size="small"
                      >
                        导出结果
                      </Button>
                    </Space>
                  </div>
                  <Table
                    columns={resultColumns}
                    dataSource={searchResults}
                    rowKey="id"
                    pagination={{
                      pageSize: 10,
                      showSizeChanger: true,
                      showQuickJumper: true,
                      showTotal: (total, range) => 
                        `第 ${range[0]}-${range[1]} 条，共 ${total} 条结果`
                    }}
                  />
                </>
              ) : (
                <Empty
                  description="暂无搜索结果"
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                >
                  <Button type="primary" onClick={() => setActiveTab('search')}>
                    返回搜索
                  </Button>
                </Empty>
              )}
            </div>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default AdvancedSearchPage
