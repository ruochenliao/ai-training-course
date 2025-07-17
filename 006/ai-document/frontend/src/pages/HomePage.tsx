import React, { useEffect } from 'react';
import { Layout, Typography, Button, List, Card, Input, Space } from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  FileTextOutlined,
  DatabaseOutlined,
  RobotOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useQuery } from 'react-query';
import { useAuthStore } from '@/stores/useAuthStore';
import { useDocumentStore } from '@/stores/useDocumentStore';
import { documentService } from '@/services/document';
import dayjs from 'dayjs';

const { Sider, Content } = Layout;
const { Title, Text } = Typography;
const { Search } = Input;

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { 
    documents, 
    searchQuery, 
    setDocuments, 
    setSearchQuery 
  } = useDocumentStore();

  // 获取文档列表
  const { data: documentsData, isLoading } = useQuery(
    ['documents', searchQuery],
    () => documentService.getDocuments({ search: searchQuery || undefined }),
    {
      onSuccess: (data) => {
        setDocuments(data);
      }
    }
  );

  const handleCreateDocument = () => {
    navigate('/standard-editor');
  };

  const handleAIWritingEditor = () => {
    navigate('/ai-writing-editor');
  };

  const handleOpenDocument = (id: number) => {
    navigate(`/editor/${id}`);
  };

  const handleTemplateManagement = () => {
    navigate('/templates');
  };

  const handleAgentManagement = () => {
    navigate('/agents');
  };

  const handleSearch = (value: string) => {
    setSearchQuery(value);
  };



  return (
    <Layout style={{ height: '100%' }}>
        <Sider width={300} className="sidebar">
          <div style={{ padding: 16 }}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              size="large"
              style={{ width: '100%', marginBottom: 8 }}
              onClick={handleCreateDocument}
            >
              标准编辑器
            </Button>

            <Button
              icon={<RobotOutlined />}
              size="large"
              style={{ width: '100%', marginBottom: 16, background: '#f0f8ff', borderColor: '#1890ff', color: '#1890ff' }}
              onClick={handleAIWritingEditor}
            >
              AI智能写作
            </Button>

            {user?.is_superuser && (
              <>
                <Button
                  icon={<DatabaseOutlined />}
                  size="large"
                  style={{ width: '100%', marginBottom: 16 }}
                  onClick={handleTemplateManagement}
                >
                  模板管理
                </Button>
                <Button
                  icon={<RobotOutlined />}
                  size="large"
                  style={{ width: '100%', marginBottom: 16 }}
                  onClick={handleAgentManagement}
                >
                  智能体管理
                </Button>
              </>
            )}

            <Search
              placeholder="搜索文档"
              allowClear
              onSearch={handleSearch}
              style={{ marginBottom: 16 }}
            />

            <div style={{ marginBottom: 16 }}>
              <Title level={5} style={{ margin: 0 }}>我的文档</Title>
            </div>

            <List
              loading={isLoading}
              dataSource={documents}
              renderItem={(doc) => (
                <List.Item 
                  className="document-list-item"
                  style={{ padding: '12px 0', cursor: 'pointer' }}
                  onClick={() => handleOpenDocument(doc.id)}
                >
                  <List.Item.Meta
                    avatar={<FileTextOutlined style={{ fontSize: 16, color: '#1890ff' }} />}
                    title={
                      <Text ellipsis style={{ fontSize: 14 }}>
                        {doc.title || '无标题文档'}
                      </Text>
                    }
                    description={
                      <Space direction="vertical" size={4}>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {doc.word_count} 字
                        </Text>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {dayjs(doc.updated_at || doc.created_at).format('MM-DD HH:mm')}
                        </Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </div>
        </Sider>

        <Content className="main-content" style={{ padding: 24 }}>
          <div style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            justifyContent: 'center',
            height: '100%',
            textAlign: 'center'
          }}>
            <FileTextOutlined style={{ fontSize: 64, color: '#d9d9d9', marginBottom: 16 }} />
            <Title level={3} type="secondary">
              选择一个文档开始编辑
            </Title>
            <Text type="secondary" style={{ marginBottom: 24 }}>
              选择合适的编辑器开始您的写作之旅
            </Text>
            <Space size="large">
              <Button
                type="primary"
                size="large"
                icon={<PlusOutlined />}
                onClick={handleCreateDocument}
              >
                标准编辑器
              </Button>
              <Button
                size="large"
                icon={<RobotOutlined />}
                onClick={handleAIWritingEditor}
                style={{ background: '#f0f8ff', borderColor: '#1890ff', color: '#1890ff' }}
              >
                AI智能写作
              </Button>
            </Space>
          </div>
        </Content>
      </Layout>
  );
};

export default HomePage;
