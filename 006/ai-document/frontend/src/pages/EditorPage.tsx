import React, { useState, useEffect, useCallback } from 'react';
import { 
  Layout, 
  Button, 
  Input, 
  Space, 
  Typography, 
  message, 
  Spin,
  Dropdown,
  Menu
} from 'antd';
import { 
  ArrowLeftOutlined, 
  SaveOutlined, 
  ShareAltOutlined,
  MoreOutlined,
  UserOutlined,
  LogoutOutlined
} from '@ant-design/icons';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useAuthStore } from '@/stores/useAuthStore';
import { useDocumentStore } from '@/stores/useDocumentStore';
import { documentService } from '@/services/document';
import RichTextEditor from '@/components/RichTextEditor';
import AIPanel from '@/components/AIPanel';
import { Document, DocumentCreate, DocumentUpdate } from '@/types';

const { Header, Content, Sider } = Layout;
const { Text } = Typography;

const EditorPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const queryClient = useQueryClient();
  const { user, logout } = useAuthStore();
  const { setCurrentDocument } = useDocumentStore();

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [selectedText, setSelectedText] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const documentId = id ? parseInt(id) : undefined;
  const isNewDocument = !documentId;

  // 处理从AI写作向导或AI工具页面传递的初始内容
  useEffect(() => {
    const state = location.state as {
      initialContent?: string;
      initialTitle?: string;
      aiTool?: string;
      toolName?: string;
    };

    if (state?.initialContent && isNewDocument) {
      setContent(state.initialContent);
      setTitle(state.initialTitle || '');
    }

    if (state?.aiTool && isNewDocument) {
      // 如果是从AI工具页面进入，可以设置默认标题
      setTitle(state.toolName ? `${state.toolName}文档` : '新建文档');
    }

    // 清除location state以避免重复设置
    if (state && Object.keys(state).length > 0) {
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location.state, isNewDocument, navigate, location.pathname]);

  // 获取文档数据
  const { data: document, isLoading } = useQuery(
    ['document', documentId],
    () => documentId ? documentService.getDocument(documentId) : null,
    {
      enabled: !!documentId,
      onSuccess: (data) => {
        if (data) {
          setTitle(data.title);
          setContent(data.content || '');
          setCurrentDocument(data);
        }
      }
    }
  );

  // 创建文档
  const createMutation = useMutation(
    (data: DocumentCreate) => documentService.createDocument(data),
    {
      onSuccess: (data) => {
        message.success('文档创建成功');
        setCurrentDocument(data);
        navigate(`/editor/${data.id}`, { replace: true });
        queryClient.invalidateQueries(['documents']);
        setHasUnsavedChanges(false);
      },
      onError: () => {
        message.error('创建文档失败');
      }
    }
  );

  // 更新文档
  const updateMutation = useMutation(
    ({ id, data }: { id: number; data: DocumentUpdate }) => 
      documentService.updateDocument(id, data),
    {
      onSuccess: (data) => {
        message.success('保存成功');
        setCurrentDocument(data);
        queryClient.invalidateQueries(['documents']);
        queryClient.invalidateQueries(['document', documentId]);
        setHasUnsavedChanges(false);
      },
      onError: () => {
        message.error('保存失败');
      }
    }
  );

  // 保存文档
  const handleSave = useCallback(async () => {
    if (isSaving) return;

    setIsSaving(true);
    
    try {
      if (isNewDocument) {
        await createMutation.mutateAsync({
          title: title || '无标题文档',
          content,
          is_public: false
        });
      } else if (documentId) {
        await updateMutation.mutateAsync({
          id: documentId,
          data: { title, content }
        });
      }
    } finally {
      setIsSaving(false);
    }
  }, [title, content, isNewDocument, documentId, createMutation, updateMutation, isSaving]);

  // 自动保存
  useEffect(() => {
    if (!hasUnsavedChanges || isNewDocument) return;

    const timer = setTimeout(() => {
      handleSave();
    }, 2000);

    return () => clearTimeout(timer);
  }, [hasUnsavedChanges, handleSave, isNewDocument]);

  // 监听内容变化
  useEffect(() => {
    if (document && (title !== document.title || content !== (document.content || ''))) {
      setHasUnsavedChanges(true);
    } else if (isNewDocument && (title || content)) {
      setHasUnsavedChanges(true);
    }
  }, [title, content, document, isNewDocument]);

  // 处理AI响应
  const handleAIResponse = (aiContent: string) => {
    if (selectedText) {
      // 替换选中的文本
      const newContent = content.replace(selectedText, aiContent);
      setContent(newContent);
    } else {
      // 在光标位置插入内容
      setContent(prev => prev + '\n' + aiContent);
    }
    setHasUnsavedChanges(true);
  };

  // 统计字数
  const getWordCount = (text: string) => {
    const cleanText = text.replace(/<[^>]*>/g, '');
    const chineseChars = (cleanText.match(/[\u4e00-\u9fff]/g) || []).length;
    const englishWords = (cleanText.match(/\b[a-zA-Z]+\b/g) || []).length;
    return chineseChars + englishWords;
  };

  const wordCount = getWordCount(content);

  const userMenu = (
    <Menu>
      <Menu.Item key="profile" icon={<UserOutlined />}>
        个人资料
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item key="logout" icon={<LogoutOutlined />} onClick={logout}>
        退出登录
      </Menu.Item>
    </Menu>
  );

  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <Layout style={{ height: '100vh' }}>
      <Header style={{ 
        background: '#fff', 
        padding: '0 16px',
        borderBottom: '1px solid #f0f0f0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <Space>
          <Button 
            type="text" 
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/')}
          >
            返回
          </Button>
          
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="无标题文档"
            bordered={false}
            style={{ fontSize: 16, fontWeight: 500 }}
          />
          
          {hasUnsavedChanges && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              未保存
            </Text>
          )}
        </Space>

        <Space>
          <Text type="secondary" className="word-count">
            字数: {wordCount}
          </Text>
          
          <Button 
            type="primary"
            icon={<SaveOutlined />}
            loading={isSaving}
            onClick={handleSave}
          >
            保存
          </Button>

          <Button icon={<ShareAltOutlined />}>
            分享
          </Button>

          <Dropdown overlay={userMenu} placement="bottomRight">
            <Button type="text" icon={<MoreOutlined />} />
          </Dropdown>
        </Space>
      </Header>

      <Layout>
        <Content style={{ background: '#fff' }}>
          <RichTextEditor
            value={content}
            onChange={setContent}
            placeholder="请输入内容"
          />
        </Content>

        <Sider width={350} className="ai-panel">
          <AIPanel
            documentId={documentId}
            selectedText={selectedText}
            onAIResponse={handleAIResponse}
          />
        </Sider>
      </Layout>
    </Layout>
  );
};

export default EditorPage;
