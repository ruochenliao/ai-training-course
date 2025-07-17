import React, { useState, useEffect } from 'react';
import { Card, List, Avatar, Typography, Input } from 'antd';
import { RobotOutlined, SearchOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface AIAssistantOption {
  id: string;
  name: string;
  description: string;
  icon: string;
}

interface AIAssistantPopupProps {
  visible: boolean;
  position: { x: number; y: number };
  onSelect: (option: AIAssistantOption) => void;
  onClose: () => void;
}

// AI助手选项
const AI_ASSISTANT_OPTIONS: AIAssistantOption[] = [
  {
    id: 'ai_writing',
    name: 'AI写作助手',
    description: '智能生成各类公文和文档',
    icon: '✍️'
  },
  {
    id: 'ai_polish',
    name: 'AI润色',
    description: '优化文本表达和语言风格',
    icon: '✨'
  },
  {
    id: 'ai_expand',
    name: 'AI扩写',
    description: '扩展和丰富文档内容',
    icon: '📝'
  },
  {
    id: 'ai_summarize',
    name: 'AI总结',
    description: '提取要点和核心内容',
    icon: '📋'
  },
  {
    id: 'ai_translate',
    name: 'AI翻译',
    description: '多语言翻译服务',
    icon: '🌐'
  },
  {
    id: 'ai_format',
    name: 'AI格式化',
    description: '规范文档格式和结构',
    icon: '📐'
  }
];

const AIAssistantPopup: React.FC<AIAssistantPopupProps> = ({
  visible,
  position,
  onSelect,
  onClose
}) => {
  const [searchText, setSearchText] = useState('');
  const [filteredOptions, setFilteredOptions] = useState(AI_ASSISTANT_OPTIONS);

  // 搜索过滤
  useEffect(() => {
    if (searchText.trim()) {
      const filtered = AI_ASSISTANT_OPTIONS.filter(option =>
        option.name.toLowerCase().includes(searchText.toLowerCase()) ||
        option.description.toLowerCase().includes(searchText.toLowerCase())
      );
      setFilteredOptions(filtered);
    } else {
      setFilteredOptions(AI_ASSISTANT_OPTIONS);
    }
  }, [searchText]);

  // 处理点击外部关闭
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('.ai-assistant-popup')) {
        onClose();
      }
    };

    if (visible) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [visible, onClose]);

  if (!visible) return null;

  return (
    <div
      className="ai-assistant-popup"
      style={{
        position: 'fixed',
        left: position.x,
        top: position.y,
        zIndex: 9999,
        width: '320px',
        maxHeight: '400px',
        backgroundColor: '#fff',
        borderRadius: '8px',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
        border: '1px solid #e8e8e8',
        overflow: 'hidden'
      }}
    >
      {/* 头部 */}
      <div style={{
        padding: '12px 16px',
        borderBottom: '1px solid #f0f0f0',
        background: 'linear-gradient(to right, #fafafa, #f5f5f5)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          marginBottom: '8px'
        }}>
          <RobotOutlined style={{ color: '#1890ff', marginRight: '8px' }} />
          <Text strong style={{ fontSize: '14px' }}>AI写作助手</Text>
        </div>
        
        {/* 搜索框 */}
        <Input
          size="small"
          placeholder="搜索AI功能..."
          prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{
            borderRadius: '6px',
            backgroundColor: '#fff'
          }}
        />
      </div>

      {/* 选项列表 */}
      <div style={{
        maxHeight: '300px',
        overflowY: 'auto'
      }}>
        <List
          size="small"
          dataSource={filteredOptions}
          renderItem={(option) => (
            <List.Item
              style={{
                padding: '12px 16px',
                cursor: 'pointer',
                borderBottom: '1px solid #f5f5f5',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#f0f8ff';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
              }}
              onClick={() => onSelect(option)}
            >
              <List.Item.Meta
                avatar={
                  <Avatar
                    size="small"
                    style={{
                      backgroundColor: '#f0f8ff',
                      color: '#1890ff',
                      fontSize: '16px',
                      border: '1px solid #e6f7ff'
                    }}
                  >
                    {option.icon}
                  </Avatar>
                }
                title={
                  <Text style={{ fontSize: '13px', fontWeight: 500 }}>
                    {option.name}
                  </Text>
                }
                description={
                  <Text
                    type="secondary"
                    style={{
                      fontSize: '12px',
                      lineHeight: '1.4'
                    }}
                  >
                    {option.description}
                  </Text>
                }
              />
            </List.Item>
          )}
        />
      </div>

      {/* 底部提示 */}
      <div style={{
        padding: '8px 16px',
        borderTop: '1px solid #f0f0f0',
        background: '#fafafa',
        textAlign: 'center'
      }}>
        <Text
          type="secondary"
          style={{
            fontSize: '11px'
          }}
        >
          在正文区域输入 @ 可以快速调用AI助手
        </Text>
      </div>
    </div>
  );
};

export default AIAssistantPopup;
