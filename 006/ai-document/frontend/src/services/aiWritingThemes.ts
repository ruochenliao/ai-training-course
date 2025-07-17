import api from './api';

// AI写作主题接口定义
export interface AIWritingTheme {
  id: string;
  name: string;
  description: string;
  category: string;
  icon?: string;
  prompts?: {
    system?: string;
    user?: string;
  };
  fields?: AIWritingField[];
}

export interface AIWritingField {
  key: string;
  label: string;
  type: 'text' | 'textarea' | 'select' | 'number';
  required?: boolean;
  placeholder?: string;
  options?: string[];
  defaultValue?: string;
}

export interface AIGenerationRequest {
  theme_id: string;
  fields: Record<string, any>;
  additional_context?: string;
}

export interface AIGenerationResponse {
  session_id: string;
  status: 'processing' | 'completed' | 'failed';
  content?: string;
  error?: string;
}

// 预定义的AI写作主题
const DEFAULT_THEMES: AIWritingTheme[] = [
  {
    id: 'commendation',
    name: '表彰通报',
    description: '用于表彰先进个人或集体的通报文件',
    category: '通报',
    icon: '🏆',
    fields: [
      {
        key: 'title',
        label: '标题',
        type: 'text',
        required: true,
        placeholder: '请输入表彰通报标题'
      },
      {
        key: 'recipient',
        label: '表彰对象',
        type: 'text',
        required: true,
        placeholder: '请输入被表彰的个人或集体名称'
      },
      {
        key: 'reason',
        label: '表彰原因',
        type: 'textarea',
        required: true,
        placeholder: '请详细描述表彰的具体原因和事迹'
      },
      {
        key: 'achievement',
        label: '主要成就',
        type: 'textarea',
        required: true,
        placeholder: '请描述主要成就和贡献'
      }
    ]
  },
  {
    id: 'criticism',
    name: '批评通报',
    description: '用于批评违规行为的通报文件',
    category: '通报',
    icon: '⚠️',
    fields: [
      {
        key: 'title',
        label: '标题',
        type: 'text',
        required: true,
        placeholder: '请输入批评通报标题'
      },
      {
        key: 'target',
        label: '批评对象',
        type: 'text',
        required: true,
        placeholder: '请输入被批评的个人或集体名称'
      },
      {
        key: 'violation',
        label: '违规行为',
        type: 'textarea',
        required: true,
        placeholder: '请详细描述违规行为和具体情况'
      },
      {
        key: 'consequence',
        label: '处理结果',
        type: 'textarea',
        required: false,
        placeholder: '请描述相应的处理措施'
      }
    ]
  },
  {
    id: 'meeting_notice',
    name: '会议通知',
    description: '用于发布会议安排的通知文件',
    category: '会务',
    icon: '📅',
    fields: [
      {
        key: 'title',
        label: '会议主题',
        type: 'text',
        required: true,
        placeholder: '请输入会议主题'
      },
      {
        key: 'time',
        label: '会议时间',
        type: 'text',
        required: true,
        placeholder: '请输入会议时间'
      },
      {
        key: 'location',
        label: '会议地点',
        type: 'text',
        required: true,
        placeholder: '请输入会议地点'
      },
      {
        key: 'agenda',
        label: '会议议程',
        type: 'textarea',
        required: true,
        placeholder: '请输入会议议程和主要内容'
      },
      {
        key: 'participants',
        label: '参会人员',
        type: 'textarea',
        required: true,
        placeholder: '请输入参会人员范围'
      }
    ]
  },
  {
    id: 'work_report',
    name: '工作汇报',
    description: '用于汇报工作进展和成果',
    category: '汇报',
    icon: '📊',
    fields: [
      {
        key: 'title',
        label: '汇报标题',
        type: 'text',
        required: true,
        placeholder: '请输入汇报标题'
      },
      {
        key: 'period',
        label: '汇报期间',
        type: 'text',
        required: true,
        placeholder: '请输入汇报的时间期间'
      },
      {
        key: 'achievements',
        label: '主要成果',
        type: 'textarea',
        required: true,
        placeholder: '请描述主要工作成果和亮点'
      },
      {
        key: 'problems',
        label: '存在问题',
        type: 'textarea',
        required: false,
        placeholder: '请描述工作中遇到的问题和困难'
      },
      {
        key: 'next_plan',
        label: '下步计划',
        type: 'textarea',
        required: false,
        placeholder: '请描述下一步工作计划和安排'
      }
    ]
  },
  {
    id: 'proposal',
    name: '政协提案',
    description: '用于撰写政协提案建议',
    category: '会务',
    icon: '📝',
    fields: [
      {
        key: 'title',
        label: '提案标题',
        type: 'text',
        required: true,
        placeholder: '请输入提案标题'
      },
      {
        key: 'background',
        label: '背景情况',
        type: 'textarea',
        required: true,
        placeholder: '请描述提案的背景和现状'
      },
      {
        key: 'problem',
        label: '存在问题',
        type: 'textarea',
        required: true,
        placeholder: '请描述需要解决的主要问题'
      },
      {
        key: 'suggestion',
        label: '建议措施',
        type: 'textarea',
        required: true,
        placeholder: '请提出具体的建议和措施'
      }
    ]
  },
  {
    id: 'research_report',
    name: '调研报告',
    description: '用于撰写调研分析报告',
    category: '调研',
    icon: '🔍',
    fields: [
      {
        key: 'title',
        label: '调研主题',
        type: 'text',
        required: true,
        placeholder: '请输入调研主题'
      },
      {
        key: 'scope',
        label: '调研范围',
        type: 'text',
        required: true,
        placeholder: '请输入调研的范围和对象'
      },
      {
        key: 'method',
        label: '调研方法',
        type: 'textarea',
        required: true,
        placeholder: '请描述调研采用的方法和途径'
      },
      {
        key: 'findings',
        label: '主要发现',
        type: 'textarea',
        required: true,
        placeholder: '请描述调研的主要发现和结论'
      },
      {
        key: 'recommendations',
        label: '对策建议',
        type: 'textarea',
        required: true,
        placeholder: '请提出针对性的对策建议'
      }
    ]
  },
  {
    id: 'speech',
    name: '讲话稿',
    description: '用于撰写各类讲话稿',
    category: '讲话',
    icon: '🎤',
    fields: [
      {
        key: 'title',
        label: '讲话主题',
        type: 'text',
        required: true,
        placeholder: '请输入讲话主题'
      },
      {
        key: 'occasion',
        label: '讲话场合',
        type: 'text',
        required: true,
        placeholder: '请输入讲话的具体场合'
      },
      {
        key: 'audience',
        label: '听众对象',
        type: 'text',
        required: true,
        placeholder: '请输入主要听众对象'
      },
      {
        key: 'key_points',
        label: '核心要点',
        type: 'textarea',
        required: true,
        placeholder: '请输入讲话的核心要点和主要内容'
      },
      {
        key: 'tone',
        label: '讲话风格',
        type: 'select',
        required: false,
        options: ['正式严肃', '亲切温和', '激励鼓舞', '务实平和'],
        defaultValue: '正式严肃'
      }
    ]
  },
  {
    id: 'summary',
    name: '工作总结',
    description: '用于撰写各类工作总结',
    category: '总结',
    icon: '📋',
    fields: [
      {
        key: 'title',
        label: '总结标题',
        type: 'text',
        required: true,
        placeholder: '请输入总结标题'
      },
      {
        key: 'period',
        label: '总结期间',
        type: 'text',
        required: true,
        placeholder: '请输入总结的时间期间'
      },
      {
        key: 'overview',
        label: '工作概述',
        type: 'textarea',
        required: true,
        placeholder: '请概述这一期间的主要工作'
      },
      {
        key: 'achievements',
        label: '主要成绩',
        type: 'textarea',
        required: true,
        placeholder: '请详细描述取得的主要成绩和亮点'
      },
      {
        key: 'shortcomings',
        label: '不足之处',
        type: 'textarea',
        required: false,
        placeholder: '请客观分析存在的不足和问题'
      },
      {
        key: 'lessons',
        label: '经验教训',
        type: 'textarea',
        required: false,
        placeholder: '请总结经验教训和启示'
      }
    ]
  }
];

class AIWritingThemesService {
  /**
   * 获取所有可用的AI写作主题
   */
  async getThemes(): Promise<AIWritingTheme[]> {
    try {
      // 首先尝试从后端获取
      const response = await api.get('/ai-writing/themes');
      return response.data;
    } catch (error) {
      // 如果后端接口不可用，返回默认主题
      console.warn('无法从后端获取主题，使用默认主题:', error);
      return DEFAULT_THEMES;
    }
  }

  /**
   * 根据分类获取主题
   */
  async getThemesByCategory(category: string): Promise<AIWritingTheme[]> {
    const themes = await this.getThemes();
    return themes.filter(theme => theme.category === category);
  }

  /**
   * 根据ID获取特定主题
   */
  async getThemeById(id: string): Promise<AIWritingTheme | null> {
    const themes = await this.getThemes();
    return themes.find(theme => theme.id === id) || null;
  }

  /**
   * 获取所有分类
   */
  async getCategories(): Promise<string[]> {
    const themes = await this.getThemes();
    const categories = [...new Set(themes.map(theme => theme.category))];
    return categories;
  }

  /**
   * 生成AI内容
   */
  async generateContent(request: AIGenerationRequest): Promise<AIGenerationResponse> {
    try {
      const response = await api.post('/ai-writing/generate', request);
      return response.data;
    } catch (error) {
      console.error('AI内容生成失败，使用模拟数据:', error);
      // 如果后端不可用，返回模拟响应
      return this.generateMockContent(request);
    }
  }

  /**
   * 生成模拟内容（用于测试）
   */
  private async generateMockContent(request: AIGenerationRequest): Promise<AIGenerationResponse> {
    const sessionId = 'mock_' + Date.now();

    // 模拟异步处理
    setTimeout(() => {
      const mockContent = this.createMockContent(request);
      // 存储模拟结果
      localStorage.setItem(`mock_session_${sessionId}`, JSON.stringify({
        status: 'completed',
        content: mockContent
      }));
    }, 2000);

    return {
      session_id: sessionId,
      status: 'processing'
    };
  }

  /**
   * 创建模拟内容
   */
  private createMockContent(request: AIGenerationRequest): string {
    const theme = DEFAULT_THEMES.find(t => t.id === request.theme_id);
    if (!theme) return '生成的模拟内容';

    const fields = request.fields;
    let content = '';

    switch (request.theme_id) {
      case 'commendation':
        content = `# ${fields.title || '表彰通报'}

## 表彰决定

经研究决定，对${fields.recipient || '先进个人'}予以表彰。

## 表彰原因

${fields.reason || '在工作中表现突出，成绩显著。'}

## 主要成就

${fields.achievement || '取得了优异的成绩，为单位发展做出了重要贡献。'}

## 决定

希望受表彰的同志再接再厉，继续发挥模范带头作用。同时号召全体同志向先进学习，共同推进各项工作再上新台阶。

特此通报。`;
        break;

      case 'meeting_notice':
        content = `# ${fields.title || '会议通知'}

## 会议安排

**会议时间：** ${fields.time || '待定'}
**会议地点：** ${fields.location || '待定'}

## 会议议程

${fields.agenda || '1. 传达上级精神\n2. 讨论工作安排\n3. 其他事项'}

## 参会人员

${fields.participants || '全体工作人员'}

## 注意事项

请各位参会人员准时参加，不得无故缺席。

特此通知。`;
        break;

      default:
        content = `# ${fields.title || '文档标题'}

根据您提供的信息，生成以下内容：

${Object.entries(fields).map(([key, value]) =>
  value ? `**${key}：** ${value}` : ''
).filter(Boolean).join('\n\n')}

${request.additional_context ? `\n\n**补充说明：** ${request.additional_context}` : ''}

这是一份根据您的要求生成的专业文档，内容结构清晰，语言规范。`;
    }

    return content;
  }

  /**
   * 获取生成状态
   */
  async getGenerationStatus(sessionId: string): Promise<AIGenerationResponse> {
    try {
      const response = await api.get(`/ai-writing/status/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('获取生成状态失败，使用模拟数据:', error);
      // 如果后端不可用，检查模拟数据
      return this.getMockStatus(sessionId);
    }
  }

  /**
   * 获取模拟状态
   */
  private getMockStatus(sessionId: string): AIGenerationResponse {
    const mockData = localStorage.getItem(`mock_session_${sessionId}`);
    if (mockData) {
      const data = JSON.parse(mockData);
      return {
        session_id: sessionId,
        status: data.status,
        content: data.content,
        error: data.error
      };
    }

    return {
      session_id: sessionId,
      status: 'processing'
    };
  }
}

export const aiWritingThemesService = new AIWritingThemesService();
export default aiWritingThemesService;
