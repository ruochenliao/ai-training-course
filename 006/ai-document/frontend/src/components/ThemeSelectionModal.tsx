import React, { useState, useEffect } from 'react';
import { Modal, Input, List, Avatar, Typography, Spin, message, Empty } from 'antd';
import { SearchOutlined, FileTextOutlined } from '@ant-design/icons';
import { AIWritingTheme, aiWritingThemesService } from '@/services/aiWritingThemes';

const { Text, Title } = Typography;
const { Search } = Input;

interface ThemeSelectionModalProps {
  visible: boolean;
  onSelect: (theme: AIWritingTheme) => void;
  onCancel: () => void;
}

const ThemeSelectionModal: React.FC<ThemeSelectionModalProps> = ({
  visible,
  onSelect,
  onCancel
}) => {
  const [themes, setThemes] = useState<AIWritingTheme[]>([]);
  const [filteredThemes, setFilteredThemes] = useState<AIWritingTheme[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');

  // 加载主题数据
  useEffect(() => {
    if (visible) {
      loadThemes();
    }
  }, [visible]);

  // 搜索过滤
  useEffect(() => {
    if (searchText.trim()) {
      const filtered = themes.filter(theme =>
        theme.name.toLowerCase().includes(searchText.toLowerCase()) ||
        theme.description.toLowerCase().includes(searchText.toLowerCase()) ||
        theme.category.toLowerCase().includes(searchText.toLowerCase())
      );
      setFilteredThemes(filtered);
    } else {
      setFilteredThemes(themes);
    }
  }, [searchText, themes]);

  const loadThemes = async () => {
    setLoading(true);
    try {
      const themesData = await aiWritingThemesService.getThemes();
      setThemes(themesData);
      setFilteredThemes(themesData);
    } catch (error) {
      console.error('加载主题失败:', error);
      message.error('加载主题失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleThemeSelect = (theme: AIWritingTheme) => {
    onSelect(theme);
  };

  const handleCancel = () => {
    setSearchText('');
    onCancel();
  };

  // 按分类分组主题
  const groupedThemes = filteredThemes.reduce((groups, theme) => {
    const category = theme.category;
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push(theme);
    return groups;
  }, {} as Record<string, AIWritingTheme[]>);

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <FileTextOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
          <span>选择写作主题</span>
        </div>
      }
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={600}
      centered
      destroyOnClose
      styles={{
        body: { padding: '16px 24px' }
      }}
    >
      {/* 搜索框 */}
      <div style={{ marginBottom: '16px' }}>
        <Search
          placeholder="搜索写作主题..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ width: '100%' }}
          size="large"
          allowClear
        />
      </div>

      {/* 主题列表 */}
      <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
        <Spin spinning={loading}>
          {filteredThemes.length === 0 && !loading ? (
            <Empty
              description="暂无匹配的写作主题"
              style={{ margin: '40px 0' }}
            />
          ) : (
            Object.entries(groupedThemes).map(([category, categoryThemes]) => (
              <div key={category} style={{ marginBottom: '24px' }}>
                {/* 分类标题 */}
                <div style={{
                  padding: '8px 0',
                  borderBottom: '1px solid #f0f0f0',
                  marginBottom: '12px'
                }}>
                  <Text strong style={{ color: '#1890ff', fontSize: '14px' }}>
                    {category}
                  </Text>
                  <Text type="secondary" style={{ marginLeft: '8px', fontSize: '12px' }}>
                    ({categoryThemes.length} 个主题)
                  </Text>
                </div>

                {/* 主题列表 */}
                <List
                  grid={{ gutter: 8, column: 2 }}
                  dataSource={categoryThemes}
                  renderItem={(theme) => (
                    <List.Item>
                      <div
                        style={{
                          padding: '16px',
                          border: '1px solid #e8e8e8',
                          borderRadius: '8px',
                          cursor: 'pointer',
                          transition: 'all 0.3s',
                          height: '100%',
                          display: 'flex',
                          flexDirection: 'column'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.borderColor = '#1890ff';
                          e.currentTarget.style.boxShadow = '0 2px 8px rgba(24, 144, 255, 0.2)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.borderColor = '#e8e8e8';
                          e.currentTarget.style.boxShadow = 'none';
                        }}
                        onClick={() => handleThemeSelect(theme)}
                      >
                        {/* 主题图标和名称 */}
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          marginBottom: '8px'
                        }}>
                          <Avatar
                            size="small"
                            style={{
                              backgroundColor: '#f0f8ff',
                              color: '#1890ff',
                              marginRight: '8px',
                              fontSize: '16px'
                            }}
                          >
                            {theme.icon || '📝'}
                          </Avatar>
                          <Text strong style={{ fontSize: '14px' }}>
                            {theme.name}
                          </Text>
                        </div>

                        {/* 主题描述 */}
                        <Text
                          type="secondary"
                          style={{
                            fontSize: '12px',
                            lineHeight: '1.5',
                            flex: 1
                          }}
                        >
                          {theme.description}
                        </Text>

                        {/* 字段数量提示 */}
                        {theme.fields && theme.fields.length > 0 && (
                          <div style={{
                            marginTop: '8px',
                            padding: '4px 8px',
                            backgroundColor: '#f0f8ff',
                            borderRadius: '4px',
                            textAlign: 'center'
                          }}>
                            <Text style={{ fontSize: '11px', color: '#1890ff' }}>
                              {theme.fields.length} 个配置项
                            </Text>
                          </div>
                        )}
                      </div>
                    </List.Item>
                  )}
                />
              </div>
            ))
          )}
        </Spin>
      </div>

      {/* 底部提示 */}
      <div style={{
        marginTop: '16px',
        padding: '12px',
        backgroundColor: '#f8f9fa',
        borderRadius: '6px',
        textAlign: 'center'
      }}>
        <Text type="secondary" style={{ fontSize: '12px' }}>
          💡 选择主题后，系统将引导您填写相关信息，然后生成专业的文档内容
        </Text>
      </div>
    </Modal>
  );
};

export default ThemeSelectionModal;
