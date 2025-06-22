'use client'

import {useState} from 'react'
import {Button, Card, Input, Layout, Space, Typography} from 'antd'
import {BookOutlined, MessageOutlined, SearchOutlined} from '@ant-design/icons'

const { Header, Content, Footer } = Layout
const { Title, Paragraph } = Typography
const { Search } = Input

export default function HomePage() {
  const [loading, setLoading] = useState(false)

  const handleSearch = async (value: string) => {
    if (!value.trim()) return
    
    setLoading(true)
    try {
      // 这里将实现搜索功能
      console.log('搜索:', value)
    } catch (error) {
      console.error('搜索失败:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout className="min-h-screen">
      <Header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto flex items-center justify-between h-16">
          <div className="flex items-center space-x-4">
            <BookOutlined className="text-2xl text-blue-600" />
            <Title level={3} className="!mb-0 !text-gray-800">
              企业级RAG知识库
            </Title>
          </div>
          <Space>
            <Button type="primary" icon={<MessageOutlined />}>
              开始对话
            </Button>
          </Space>
        </div>
      </Header>

      <Content className="flex-1">
        <div className="max-w-4xl mx-auto py-12 px-4">
          {/* 欢迎区域 */}
          <div className="text-center mb-12">
            <Title level={1} className="!text-4xl !font-bold !text-gray-900 mb-4">
              智能知识问答系统
            </Title>
            <Paragraph className="!text-xl !text-gray-600 mb-8">
              基于多智能体协作的企业级知识库，提供精准、全面、可溯源的智能问答体验
            </Paragraph>
            
            {/* 搜索框 */}
            <div className="max-w-2xl mx-auto">
              <Search
                placeholder="请输入您的问题..."
                size="large"
                enterButton={<SearchOutlined />}
                loading={loading}
                onSearch={handleSearch}
                className="shadow-lg"
              />
            </div>
          </div>

          {/* 功能卡片 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <Card 
              hoverable
              className="text-center"
              cover={
                <div className="p-8 bg-blue-50">
                  <MessageOutlined className="text-4xl text-blue-600" />
                </div>
              }
            >
              <Card.Meta
                title="智能对话"
                description="与AI助手进行自然语言对话，获得准确的答案和建议"
              />
            </Card>

            <Card 
              hoverable
              className="text-center"
              cover={
                <div className="p-8 bg-green-50">
                  <SearchOutlined className="text-4xl text-green-600" />
                </div>
              }
            >
              <Card.Meta
                title="多模态检索"
                description="支持向量检索、图谱检索和混合检索，全方位获取信息"
              />
            </Card>

            <Card 
              hoverable
              className="text-center"
              cover={
                <div className="p-8 bg-purple-50">
                  <BookOutlined className="text-4xl text-purple-600" />
                </div>
              }
            >
              <Card.Meta
                title="知识管理"
                description="高效管理企业知识资产，支持多种文档格式"
              />
            </Card>
          </div>

          {/* 特性介绍 */}
          <div className="bg-gray-50 rounded-lg p-8">
            <Title level={2} className="text-center mb-8">
              核心特性
            </Title>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <Title level={4}>🤖 多智能体协作</Title>
                <Paragraph>
                  基于AutoGen的智能体编排和协调，实现复杂查询的智能分解和协作处理
                </Paragraph>
              </div>
              <div>
                <Title level={4}>🔍 多模态检索融合</Title>
                <Paragraph>
                  深度整合向量检索、图谱检索和关键词检索，提供全方位的信息获取能力
                </Paragraph>
              </div>
              <div>
                <Title level={4}>📊 智能结果融合</Title>
                <Paragraph>
                  通过AI驱动的结果分析和融合，确保答案的准确性和完整性
                </Paragraph>
              </div>
              <div>
                <Title level={4}>🔒 企业级安全</Title>
                <Paragraph>
                  完整的权限管理和数据安全保障，满足企业级应用需求
                </Paragraph>
              </div>
            </div>
          </div>
        </div>
      </Content>

      <Footer className="text-center bg-gray-50">
        <Paragraph className="!mb-0 !text-gray-600">
          企业级Agent+RAG知识库系统 ©2024 - 基于多智能体协作的下一代知识管理平台
        </Paragraph>
      </Footer>
    </Layout>
  )
}
