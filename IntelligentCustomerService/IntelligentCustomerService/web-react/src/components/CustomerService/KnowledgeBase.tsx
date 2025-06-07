import React, {useCallback, useEffect, useState} from 'react'
import {Button, Card, Divider, Empty, Form, Input, List, message, Modal, Select, Space, Spin, Tag, Tooltip} from 'antd'
import {
    BookOutlined,
    ClockCircleOutlined,
    DeleteOutlined,
    EditOutlined,
    EyeOutlined,
    PlusOutlined,
    SearchOutlined,
    TagOutlined,
    UserOutlined
} from '@ant-design/icons'
import {customerServiceApi, KnowledgeArticle} from '@/api/customerService'
import {formatTime} from '@/utils'
import './KnowledgeBase.less'

interface KnowledgeBaseProps {
  onArticleSelect?: (article: KnowledgeArticle) => void
  mode?: 'search' | 'manage' // 搜索模式或管理模式
}

const { Search, TextArea } = Input
const { Option } = Select

const KnowledgeBase: React.FC<KnowledgeBaseProps> = ({
  onArticleSelect,
  mode = 'search'
}) => {
  const [articles, setArticles] = useState<KnowledgeArticle[]>([])
  const [loading, setLoading] = useState(false)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showViewModal, setShowViewModal] = useState(false)
  const [currentArticle, setCurrentArticle] = useState<KnowledgeArticle | null>(null)
  const [form] = Form.useForm()
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  })

  // 分类选项
  const categories = [
    { value: 'all', label: '全部分类' },
    { value: 'product', label: '产品相关' },
    { value: 'technical', label: '技术支持' },
    { value: 'billing', label: '计费问题' },
    { value: 'account', label: '账户管理' },
    { value: 'policy', label: '政策条款' },
    { value: 'other', label: '其他' }
  ]

  // 加载知识库文章
  const loadArticles = useCallback(async () => {
    try {
      setLoading(true)
      const params: {
        page: number;
        pageSize: number;
        keyword?: string;
        category?: string;
        isPublished: boolean;
      } = {
        page: pagination.current,
        pageSize: pagination.pageSize,
        isPublished: true
      }
      
      if (searchKeyword) {
        params.keyword = searchKeyword
      }
      
      if (selectedCategory !== 'all') {
        params.category = selectedCategory
      }
      
      const response = await customerServiceApi.getKnowledgeArticles(params)
      setArticles(response.list)
      setPagination(prev => ({
        ...prev,
        total: response.pagination.total
      }))
    } catch (error) {
      message.error('加载知识库失败')
    } finally {
      setLoading(false)
    }
  }, [pagination.current, pagination.pageSize, searchKeyword, selectedCategory])

  // 搜索知识库
  const handleSearch = useCallback(async (keyword: string) => {
    if (!keyword.trim()) {
      loadArticles()
      return
    }
    
    try {
      setLoading(true)
      const results = await customerServiceApi.searchKnowledge(keyword)
      setArticles(results)
      setPagination(prev => ({ ...prev, total: results.length }))
    } catch (error) {
      message.error('搜索失败')
    } finally {
      setLoading(false)
    }
  }, [loadArticles])

  // 创建文章
  const handleCreateArticle = useCallback(async (values: any) => {
    try {
      // TODO: 实现创建知识库文章API
      console.log('创建文章:', values)
      message.success('文章创建成功')
      setShowCreateModal(false)
      form.resetFields()
      loadArticles()
    } catch (error) {
      message.error('创建文章失败')
    }
  }, [form, loadArticles])

  // 更新文章
  const handleUpdateArticle = useCallback(async (values: any) => {
    if (!currentArticle) return
    
    try {
      // TODO: 实现更新知识库文章API
      console.log('更新文章:', currentArticle.id, values)
      
      message.success('文章更新成功')
      setShowEditModal(false)
      setCurrentArticle(null)
      form.resetFields()
      loadArticles()
    } catch (error) {
      message.error('更新文章失败')
    }
  }, [currentArticle, form, loadArticles])

  // 删除文章
  const handleDeleteArticle = useCallback(async (articleId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '删除后无法恢复，是否确认删除这篇文章？',
      onOk: async () => {
        try {
          // TODO: 实现删除知识库文章API
          console.log('删除文章:', articleId)
          message.success('文章删除成功')
          loadArticles()
        } catch (error) {
          message.error('删除文章失败')
        }
      }
    })
  }, [loadArticles])

  // 查看文章详情
  const handleViewArticle = useCallback(async (articleId: string) => {
    try {
      const article = await customerServiceApi.getKnowledgeArticle(articleId)
      setCurrentArticle(article)
      setShowViewModal(true)
    } catch (error) {
      message.error('加载文章详情失败')
    }
  }, [])

  // 编辑文章
  const handleEditArticle = useCallback(async (articleId: string) => {
    try {
      const article = await customerServiceApi.getKnowledgeArticle(articleId)
      setCurrentArticle(article)
      form.setFieldsValue({
        title: article.title,
        content: article.content,
        category: article.category,
        tags: article.tags
      })
      setShowEditModal(true)
    } catch (error) {
      message.error('加载文章详情失败')
    }
  }, [form])

  // 选择文章（用于插入到对话中）
  const handleSelectArticle = useCallback((article: KnowledgeArticle) => {
    onArticleSelect?.(article)
  }, [onArticleSelect])

  // 获取分类标签颜色
  const getCategoryColor = useCallback((category: string) => {
    const colorMap: Record<string, string> = {
      product: 'blue',
      technical: 'green',
      billing: 'orange',
      account: 'purple',
      policy: 'red',
      other: 'default'
    }
    return colorMap[category] || 'default'
  }, [])

  // 初始化加载
  useEffect(() => {
    loadArticles()
  }, [loadArticles])

  return (
    <div className="knowledge-base">
      {/* 搜索和筛选 */}
      <Card className="search-section" size="small">
        <Space direction="vertical" style={{ width: '100%' }}>
          <Search
            placeholder="搜索知识库文章..."
            allowClear
            enterButton={<SearchOutlined />}
            onSearch={handleSearch}
            onChange={(e) => setSearchKeyword(e.target.value)}
          />
          
          <div className="filter-row">
            <Select
              value={selectedCategory}
              onChange={setSelectedCategory}
              style={{ width: 150 }}
              size="small"
            >
              {categories.map(cat => (
                <Option key={cat.value} value={cat.value}>
                  {cat.label}
                </Option>
              ))}
            </Select>
            
            {mode === 'manage' && (
              <Button
                type="primary"
                icon={<PlusOutlined />}
                size="small"
                onClick={() => setShowCreateModal(true)}
              >
                新建文章
              </Button>
            )}
          </div>
        </Space>
      </Card>

      {/* 文章列表 */}
      <div className="articles-section">
        <Spin spinning={loading}>
          {articles.length === 0 ? (
            <Empty 
              description="暂无文章" 
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ) : (
            <List
              dataSource={articles}
              renderItem={(article) => (
                <List.Item
                  className="article-item"
                  actions={[
                    <Tooltip title="查看" key="view">
                      <Button
                        type="text"
                        icon={<EyeOutlined />}
                        size="small"
                        onClick={() => handleViewArticle(article.id)}
                      />
                    </Tooltip>,
                    mode === 'search' ? (
                      <Button
                        type="primary"
                        size="small"
                        onClick={() => handleSelectArticle(article)}
                        key="select"
                      >
                        选择
                      </Button>
                    ) : (
                      <Space key="manage">
                        <Tooltip title="编辑">
                          <Button
                            type="text"
                            icon={<EditOutlined />}
                            size="small"
                            onClick={() => handleEditArticle(article.id)}
                          />
                        </Tooltip>
                        <Tooltip title="删除">
                          <Button
                            type="text"
                            icon={<DeleteOutlined />}
                            size="small"
                            danger
                            onClick={() => handleDeleteArticle(article.id)}
                          />
                        </Tooltip>
                      </Space>
                    )
                  ]}
                >
                  <List.Item.Meta
                    avatar={<BookOutlined className="article-icon" />}
                    title={
                      <div className="article-title">
                        <span className="title-text">{article.title}</span>
                        <Tag color={getCategoryColor(article.category)}>
                          {categories.find(c => c.value === article.category)?.label || article.category}
                        </Tag>
                      </div>
                    }
                    description={
                      <div className="article-description">
                        <div className="summary">{article.summary}</div>
                        
                        <div className="article-meta">
                          <Space size={16}>
                            <span className="meta-item">
                              <EyeOutlined />
                              {article.viewCount} 次查看
                            </span>
                            
                            <span className="meta-item">
                              <UserOutlined />
                              {article.createdBy}
                            </span>
                            
                            <span className="meta-item">
                              <ClockCircleOutlined />
                              {formatTime(article.updatedAt)}
                            </span>
                          </Space>
                        </div>
                        
                        {article.tags.length > 0 && (
                          <div className="article-tags">
                            <TagOutlined />
                            {article.tags.map(tag => (
                              <Tag key={tag}>{tag}</Tag>
                            ))}
                          </div>
                        )}
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          )}
        </Spin>
      </div>

      {/* 创建文章弹窗 */}
      <Modal
        title="创建知识库文章"
        open={showCreateModal}
        onCancel={() => {
          setShowCreateModal(false)
          form.resetFields()
        }}
        footer={null}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateArticle}
        >
          <Form.Item
            name="title"
            label="文章标题"
            rules={[{ required: true, message: '请输入文章标题' }]}
          >
            <Input placeholder="请输入文章标题" />
          </Form.Item>
          
          <Form.Item
            name="category"
            label="文章分类"
            rules={[{ required: true, message: '请选择文章分类' }]}
          >
            <Select placeholder="请选择文章分类">
              {categories.filter(c => c.value !== 'all').map(cat => (
                <Option key={cat.value} value={cat.value}>
                  {cat.label}
                </Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item
            name="tags"
            label="标签"
          >
            <Select
              mode="tags"
              placeholder="请输入标签"
              tokenSeparators={[',', ' ']}
            />
          </Form.Item>
          
          <Form.Item
            name="content"
            label="文章内容"
            rules={[{ required: true, message: '请输入文章内容' }]}
          >
            <TextArea
              rows={12}
              placeholder="请输入文章内容，支持Markdown格式"
            />
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                创建文章
              </Button>
              <Button onClick={() => {
                setShowCreateModal(false)
                form.resetFields()
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑文章弹窗 */}
      <Modal
        title="编辑知识库文章"
        open={showEditModal}
        onCancel={() => {
          setShowEditModal(false)
          setCurrentArticle(null)
          form.resetFields()
        }}
        footer={null}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleUpdateArticle}
        >
          <Form.Item
            name="title"
            label="文章标题"
            rules={[{ required: true, message: '请输入文章标题' }]}
          >
            <Input placeholder="请输入文章标题" />
          </Form.Item>
          
          <Form.Item
            name="category"
            label="文章分类"
            rules={[{ required: true, message: '请选择文章分类' }]}
          >
            <Select placeholder="请选择文章分类">
              {categories.filter(c => c.value !== 'all').map(cat => (
                <Option key={cat.value} value={cat.value}>
                  {cat.label}
                </Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item
            name="tags"
            label="标签"
          >
            <Select
              mode="tags"
              placeholder="请输入标签"
              tokenSeparators={[',', ' ']}
            />
          </Form.Item>
          
          <Form.Item
            name="content"
            label="文章内容"
            rules={[{ required: true, message: '请输入文章内容' }]}
          >
            <TextArea
              rows={12}
              placeholder="请输入文章内容，支持Markdown格式"
            />
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                更新文章
              </Button>
              <Button onClick={() => {
                setShowEditModal(false)
                setCurrentArticle(null)
                form.resetFields()
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 查看文章弹窗 */}
      <Modal
        title={currentArticle?.title}
        open={showViewModal}
        onCancel={() => {
          setShowViewModal(false)
          setCurrentArticle(null)
        }}
        footer={[
          mode === 'search' && (
            <Button
              key="select"
              type="primary"
              onClick={() => {
                if (currentArticle) {
                  handleSelectArticle(currentArticle)
                  setShowViewModal(false)
                }
              }}
            >
              选择此文章
            </Button>
          ),
          <Button key="close" onClick={() => setShowViewModal(false)}>
            关闭
          </Button>
        ].filter(Boolean)}
        width={800}
      >
        {currentArticle && (
          <div className="article-detail">
            <div className="article-meta-detail">
              <Space size={16}>
                <Tag color={getCategoryColor(currentArticle.category)}>
                  {categories.find(c => c.value === currentArticle.category)?.label}
                </Tag>
                <span>作者: {currentArticle.createdBy}</span>
                <span>创建时间: {formatTime(currentArticle.createdAt)}</span>
                <span>查看次数: {currentArticle.viewCount}</span>
              </Space>
            </div>
            
            <Divider />
            
            <div className="article-content">
              <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                {currentArticle.content}
              </pre>
            </div>
            
            {currentArticle.tags.length > 0 && (
              <>
                <Divider />
                <div className="article-tags-detail">
                  <strong>标签: </strong>
                  {currentArticle.tags.map(tag => (
                    <Tag key={tag}>{tag}</Tag>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default KnowledgeBase