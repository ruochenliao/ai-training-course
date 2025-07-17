import React, { useState } from 'react';
import {
  Card,
  Button,
  Input,
  Space,
  Typography,
  Divider,
  message,
  Spin,
  Tag,
  Tooltip,
  Collapse
} from 'antd';
import {
  EditOutlined,
  BulbOutlined,
  RobotOutlined,
  FileTextOutlined,
  SendOutlined,
  TeamOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';
import { AITool, AIToolType } from '@/types';
import { aiService } from '@/services/ai';

const { Text, Title } = Typography;
const { TextArea } = Input;
const { Panel } = Collapse;

interface AIPanelProps {
  documentId?: number;
  selectedText?: string;
  onAIResponse: (content: string) => void;
}

const aiTools: AITool[] = [
  {
    type: 'ai_writer',
    name: 'AI写作',
    description: '智能创作内容',
    icon: 'EditOutlined'
  },
  {
    type: 'ai_polish',
    name: 'AI润色',
    description: '优化文本表达',
    icon: 'BulbOutlined'
  },
  {
    type: 'ai_outline',
    name: 'AI大纲',
    description: '生成文章大纲',
    icon: 'FileTextOutlined'
  },
  {
    type: 'ai_collaborative',
    name: '协作写作',
    description: '多智能体协作创作',
    icon: 'TeamOutlined'
  },
  {
    type: 'ai_review',
    name: '专家评审',
    description: '内容质量评估',
    icon: 'CheckCircleOutlined'
  },
  {
    type: 'deepseek',
    name: 'AI研究',
    description: '深度研究分析',
    icon: 'RobotOutlined'
  }
];

const AIPanel: React.FC<AIPanelProps> = ({
  documentId,
  selectedText,
  onAIResponse
}) => {
  const [selectedTool, setSelectedTool] = useState<AIToolType | null>(null);
  const [prompt, setPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentResponse, setCurrentResponse] = useState('');
  const [strategyInfo, setStrategyInfo] = useState<any>(null);
  const [showStrategy, setShowStrategy] = useState(false);

  const getIconComponent = (iconName: string) => {
    const icons = {
      EditOutlined: <EditOutlined />,
      BulbOutlined: <BulbOutlined />,
      RobotOutlined: <RobotOutlined />,
      FileTextOutlined: <FileTextOutlined />,
      TeamOutlined: <TeamOutlined />,
      CheckCircleOutlined: <CheckCircleOutlined />
    };
    return icons[iconName as keyof typeof icons] || <RobotOutlined />;
  };

  const handleToolSelect = (toolType: AIToolType) => {
    setSelectedTool(toolType);
    setCurrentResponse('');

    // 根据工具类型设置默认提示
    const tool = aiTools.find(t => t.type === toolType);
    if (tool && selectedText) {
      switch (toolType) {
        case 'ai_polish':
          setPrompt(`请润色以下文本：\n${selectedText}`);
          break;
        case 'ai_review':
          setPrompt(`请对以下内容进行专业评审：\n${selectedText}`);
          break;
        case 'ai_collaborative':
          setPrompt(`请多位专家协作改进以下内容：\n${selectedText}`);
          break;
        default:
          setPrompt('');
      }
    } else {
      // 为不同工具类型设置默认提示
      switch (toolType) {
        case 'ai_collaborative':
          setPrompt('请描述您希望多位AI专家协作完成的写作任务...');
          break;
        case 'ai_review':
          setPrompt('请提供需要评审的内容...');
          break;
        case 'ai_outline':
          setPrompt('请输入文章主题，我将为您生成详细大纲...');
          break;
        default:
          setPrompt('');
      }
    }
  };

  // 获取策略建议
  const handleGetStrategy = async () => {
    if (!selectedTool || !prompt.trim()) {
      message.warning('请选择AI工具并输入提示');
      return;
    }

    try {
      const strategy = await aiService.suggestStrategy({
        prompt: prompt.trim(),
        ai_type: selectedTool,
        context: selectedText
      });

      setStrategyInfo(strategy);
      setShowStrategy(true);

      message.success('策略建议已生成');
    } catch (error) {
      message.error('获取策略建议失败');
    }
  };

  const handleGenerate = async () => {
    if (!selectedTool || !prompt.trim()) {
      message.warning('请选择AI工具并输入提示');
      return;
    }

    setIsGenerating(true);
    setCurrentResponse('');

    try {
      // 创建AI会话
      const session = await aiService.createSession({
        ai_type: selectedTool,
        prompt: prompt.trim(),
        document_id: documentId,
        context: selectedText,
        metadata: {
          context: selectedText
        }
      });

      // 创建SSE连接
      const token = localStorage.getItem('token');
      const eventSource = new EventSource(`/api/ai/stream/${session.session_id}?token=${token}`);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.error) {
            message.error(data.error);
            setIsGenerating(false);
            eventSource.close();
            return;
          }

          if (data.content) {
            setCurrentResponse(prev => prev + data.content);
          }

          if (data.is_complete) {
            setIsGenerating(false);
            eventSource.close();

            // 使用最新的响应内容
            const finalResponse = currentResponse + (data.content || '');
            if (finalResponse) {
              onAIResponse(finalResponse);
            }
          }
        } catch (error) {
          console.error('Error parsing SSE data:', error);
        }
      };

      eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        message.error('连接错误，请重试');
        setIsGenerating(false);
        eventSource.close();
      };

    } catch (error) {
      setIsGenerating(false);
      message.error('生成失败，请重试');
    }
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: 16, borderBottom: '1px solid #f0f0f0' }}>
        <Title level={5} style={{ margin: 0 }}>AI妙想AI</Title>
      </div>

      <div style={{ padding: 16, flex: 1, overflow: 'auto' }}>
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          {/* AI工具选择 */}
          <div>
            <Text strong style={{ marginBottom: 8, display: 'block' }}>
              选择AI工具
            </Text>
            <Space wrap>
              {aiTools.map((tool) => (
                <Button
                  key={tool.type}
                  type={selectedTool === tool.type ? 'primary' : 'default'}
                  size="small"
                  icon={getIconComponent(tool.icon)}
                  onClick={() => handleToolSelect(tool.type)}
                  className="ai-tool-button"
                >
                  {tool.name}
                </Button>
              ))}
            </Space>
          </div>

          <Divider style={{ margin: '12px 0' }} />

          {/* 输入区域 */}
          {selectedTool && (
            <div>
              <Text strong style={{ marginBottom: 8, display: 'block' }}>
                输入提示
              </Text>
              <TextArea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="请输入您的需求..."
                rows={4}
                style={{ marginBottom: 12 }}
              />
              
              {selectedText && (
                <div style={{ marginBottom: 12 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    选中文本：
                  </Text>
                  <div style={{ 
                    background: '#f5f5f5', 
                    padding: 8, 
                    borderRadius: 4,
                    fontSize: 12,
                    maxHeight: 100,
                    overflow: 'auto'
                  }}>
                    {selectedText}
                  </div>
                </div>
              )}

              <Space direction="vertical" style={{ width: '100%' }}>
                <Button
                  icon={<ThunderboltOutlined />}
                  onClick={handleGetStrategy}
                  disabled={!prompt.trim()}
                  style={{ width: '100%' }}
                >
                  获取AI策略建议
                </Button>

                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  onClick={handleGenerate}
                  loading={isGenerating}
                  disabled={!prompt.trim()}
                  style={{ width: '100%' }}
                >
                  {isGenerating ? '生成中...' : '生成'}
                </Button>
              </Space>
            </div>
          )}

          {/* 策略建议 */}
          {showStrategy && strategyInfo && (
            <>
              <Divider style={{ margin: '12px 0' }} />
              <div>
                <Text strong style={{ marginBottom: 8, display: 'block' }}>
                  <InfoCircleOutlined style={{ marginRight: 4 }} />
                  AI策略建议
                </Text>
                <Collapse size="small">
                  <Panel header="协作策略详情" key="strategy">
                    <Space direction="vertical" style={{ width: '100%' }} size="small">
                      <div>
                        <Text strong>协作模式：</Text>
                        <Tag color="blue" style={{ marginLeft: 8 }}>
                          {strategyInfo.strategy?.description}
                        </Tag>
                      </div>

                      <div>
                        <Text strong>参与智能体：</Text>
                        <div style={{ marginTop: 4 }}>
                          {strategyInfo.strategy?.agents?.map((agent: string) => (
                            <Tag key={agent} color="green" style={{ margin: '2px' }}>
                              {agent}
                            </Tag>
                          ))}
                        </div>
                      </div>

                      <div>
                        <Text strong>复杂度评分：</Text>
                        <Tag color={strategyInfo.complexity_score >= 4 ? 'red' :
                                   strategyInfo.complexity_score >= 3 ? 'orange' : 'green'}>
                          {strategyInfo.complexity_score}/5
                        </Tag>
                      </div>

                      <div>
                        <Text strong>预估时间：</Text>
                        <Text type="secondary" style={{ marginLeft: 8 }}>
                          约 {Math.round(strategyInfo.strategy?.estimated_time / 60)} 分钟
                        </Text>
                      </div>

                      {strategyInfo.recommended_agents && (
                        <div>
                          <Text strong>推荐智能体：</Text>
                          <div style={{ marginTop: 4 }}>
                            {strategyInfo.recommended_agents.map((agent: string) => (
                              <Tag key={agent} color="purple" style={{ margin: '2px' }}>
                                {agent}
                              </Tag>
                            ))}
                          </div>
                        </div>
                      )}
                    </Space>
                  </Panel>
                </Collapse>
              </div>
            </>
          )}

          {/* 响应区域 */}
          {(isGenerating || currentResponse) && (
            <>
              <Divider style={{ margin: '12px 0' }} />
              <div>
                <Text strong style={{ marginBottom: 8, display: 'block' }}>
                  AI响应
                </Text>
                <Card 
                  size="small" 
                  style={{ 
                    minHeight: 100,
                    maxHeight: 300,
                    overflow: 'auto'
                  }}
                >
                  {isGenerating && !currentResponse && (
                    <div style={{ textAlign: 'center', padding: 20 }}>
                      <Spin />
                      <div style={{ marginTop: 8 }}>
                        <Text type="secondary">AI正在思考中...</Text>
                      </div>
                    </div>
                  )}
                  
                  {currentResponse && (
                    <div style={{ whiteSpace: 'pre-wrap', fontSize: 14 }}>
                      {currentResponse}
                      {isGenerating && <span className="cursor">|</span>}
                    </div>
                  )}
                </Card>
              </div>
            </>
          )}
        </Space>
      </div>
    </div>
  );
};

export default AIPanel;
