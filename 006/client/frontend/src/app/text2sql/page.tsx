'use client'

import React, { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
  StreamResponseMessage,
  FinalVisualizationData,
  closeWebSocketConnection,
  Text2SQLWebSocket,
  getWebSocketInstance
} from './api'
import { Text2SQLResponse } from './types'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { nord as codeTheme } from 'react-syntax-highlighter/dist/esm/styles/prism'
import remarkGfm from 'remark-gfm'

// 内联定义图标组件
const Brain = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z" />
    <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z" />
  </svg>
)

const Database = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
    <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
    <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
  </svg>
)

const Search = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <circle cx="11" cy="11" r="8"></circle>
    <path d="m21 21-4.3-4.3"></path>
  </svg>
)

const BarChart = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <line x1="12" y1="20" x2="12" y2="10"></line>
    <line x1="18" y1="20" x2="18" y2="4"></line>
    <line x1="6" y1="20" x2="6" y2="16"></line>
  </svg>
)

const FileText = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
    <polyline points="14 2 14 8 20 8"></polyline>
    <line x1="16" y1="13" x2="8" y2="13"></line>
    <line x1="16" y1="17" x2="8" y2="17"></line>
    <line x1="10" y1="9" x2="8" y2="9"></line>
  </svg>
)

const Code = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <polyline points="16 18 22 12 16 6"></polyline>
    <polyline points="8 6 2 12 8 18"></polyline>
  </svg>
)

const CodeIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="m18 16 4-4-4-4"></path>
    <path d="m6 8-4 4 4 4"></path>
    <path d="m14.5 4-5 16"></path>
  </svg>
)

// 导入错误图标
const AlertCircle = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <circle cx="12" cy="12" r="10"></circle>
    <line x1="12" y1="8" x2="12" y2="12"></line>
    <line x1="12" y1="16" x2="12" y2="16"></line>
  </svg>
)

// 定义处理步骤类型
type ProcessingStep = {
  id: number;
  message: string;
  timestamp: Date;
  source: string;
};

// 定义用户反馈状态类型
type UserFeedbackState = {
  visible: boolean;
  message: string;
  promptMessage: string;
};

// 修改RegionOutput类型
type RegionOutputs = {
  analysis: {
    merged: string;
    messages: StreamResponseMessage[];
    hasContent: boolean;
    streaming: boolean;
  };
  sql: {
    merged: string;
    messages: StreamResponseMessage[];
    hasContent: boolean;
    streaming: boolean;
  };
  explanation: {
    merged: string;
    messages: StreamResponseMessage[];
    hasContent: boolean;
    streaming: boolean;
  };
  data: {
    merged: string;
    messages: StreamResponseMessage[];
    hasContent: boolean;
    streaming: boolean;
  };
  visualization: {
    merged: string;
    messages: StreamResponseMessage[];
    hasContent: boolean;
    streaming: boolean;
  };
  process: {
    merged: string;
    messages: StreamResponseMessage[];
    hasContent: boolean;
    streaming: boolean;
  };
};

// 格式化文本展示组件
const FormattedOutput = ({ content, type }: { content: string, type: 'sql' | 'json' | 'markdown' | 'text' }) => {
  if (!content) {
    console.log('FormattedOutput: 内容为空');
    return <div className="text-gray-400 italic text-center p-2">暂无内容</div>;
  }

  console.log(`FormattedOutput: 渲染类型=${type}, 内容长度=${content?.length}, 内容预览=${content?.substring(0, 50)}...`);

  const code = (props: any) => {
    // 检查语言类型
    const language = props.className ? props.className.replace('language-', '') : 'text';

    return (
      <SyntaxHighlighter
        language={language}
        style={codeTheme}
        showLineNumbers={true}
        startingLineNumber={1}
        PreTag="div"
      >
        {props.children}
      </SyntaxHighlighter>
    );
  };

  try {
    switch (type) {
      case 'json':
        try {
          // 尝试解析JSON
          const parsedJson = JSON.parse(content);
          return (
            <SyntaxHighlighter language="json" style={codeTheme} showLineNumbers={true} startingLineNumber={1}>
              {JSON.stringify(parsedJson, null, 2)}
            </SyntaxHighlighter>
          );
        } catch (e) {
          // 如果解析失败，作为普通文本显示
          console.error('JSON解析失败:', e);
          return <div className="whitespace-pre-wrap">{content}</div>;
        }

      case 'sql':
        return (
          <SyntaxHighlighter language="sql" style={codeTheme} showLineNumbers={true} startingLineNumber={1}>
            {content}
          </SyntaxHighlighter>
        );

      case 'markdown':
        try {
          return (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                pre({ node, ...props }) {
                  return <pre className="rounded-md bg-gray-100 dark:bg-gray-800/70 p-2 my-2 overflow-auto" {...props} />;
                },
                code({ node, className, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !props.inline && match ? (
                    <SyntaxHighlighter
                      language={match[1]}
                      style={codeTheme}
                      showLineNumbers={true}
                      startingLineNumber={1}
                      PreTag="div"
                    >
                      {String(props.children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={className} {...props} />
                  );
                },
                table({ node, ...props }) {
                  return (
                    <div className="overflow-x-auto my-4">
                      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 border border-gray-200 dark:border-gray-700 rounded-md" {...props} />
                    </div>
                  );
                },
                thead({ node, ...props }) {
                  return <thead className="bg-gray-50 dark:bg-gray-800" {...props} />;
                },
                th({ node, ...props }) {
                  return <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider" {...props} />;
                },
                td({ node, ...props }) {
                  return <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400 border-t border-gray-200 dark:border-gray-700" {...props} />;
                },
                h1({ node, ...props }) {
                  return <h1 className="text-2xl font-bold mt-4 mb-2" {...props} />;
                },
                h2({ node, ...props }) {
                  return <h2 className="text-xl font-bold mt-3 mb-2" {...props} />;
                },
                h3({ node, ...props }) {
                  return <h3 className="text-lg font-bold mt-3 mb-1" {...props} />;
                },
                ul({ node, ...props }) {
                  return <ul className="list-disc pl-5 my-2" {...props} />;
                },
                ol({ node, ordered, start, ...props }) {
                  return <ol className="list-decimal pl-5 my-2" start={start || 1} {...props} />;
                },
                li({ node, ...props }) {
                  return <li className="my-1" {...props} />;
                },
                p({ node, ...props }) {
                  return <p className="my-2" {...props} />;
                },
              }}
            >
              {content}
            </ReactMarkdown>
          );
        } catch (error) {
          console.error('Markdown渲染错误:', error);
          return (
            <div className="whitespace-pre-wrap p-3 border border-red-200 bg-red-50 rounded-md">
              <p className="text-red-500 font-bold mb-2">Markdown渲染错误</p>
              <div className="overflow-auto max-h-[300px]">{content}</div>
            </div>
          );
        }

      default:
        return <div className="whitespace-pre-wrap">{content}</div>;
    }
  } catch (error) {
    console.error('格式化输出错误:', error);
    return <div className="whitespace-pre-wrap text-red-500 p-3 border border-red-200 bg-red-50 rounded-md">
      <p className="font-bold mb-2">渲染错误: {String(error)}</p>
      <div className="overflow-auto max-h-[300px]">{content}</div>
    </div>;
  }
};

export default function Text2SQL() {
  const [query, setQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [processingSteps, setProcessingSteps] = useState<ProcessingStep[]>([]);

  // 添加分页状态
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  // 按区域分类的流式输出
  const [regionOutputs, setRegionOutputs] = useState<RegionOutputs>({
    analysis: {
      merged: '',
      messages: [],
      hasContent: false,
      streaming: false
    },
    sql: {
      merged: '',
      messages: [],
      hasContent: false,
      streaming: false
    },
    explanation: {
      merged: '',
      messages: [],
      hasContent: false,
      streaming: false
    },
    data: {
      merged: '',
      messages: [],
      hasContent: false,
      streaming: false
    },
    visualization: {
      merged: '',
      messages: [],
      hasContent: false,
      streaming: false
    },
    process: {
      merged: '',
      messages: [],
      hasContent: false,
      streaming: false
    }
  })

  // 最终结果的状态
  const [sqlResult, setSqlResult] = useState<string | null>(null)
  const [explanationResult, setExplanationResult] = useState<string | null>(null)
  const [dataResult, setDataResult] = useState<any[] | null>(null)
  const [visualizationResult, setVisualizationResult] = useState<{
    type: string;
    config: any;
  } | null>(null)

  // 区域折叠状态
  const [collapsedSections, setCollapsedSections] = useState({
    analysis: false,
    sql: false,
    explanation: false,
    data: false,
    visualization: false,
    process: true // 默认折叠处理过程
  })

  // 添加用户反馈状态
  const [userFeedback, setUserFeedback] = useState<UserFeedbackState>({
    visible: false,
    message: '',
    promptMessage: ''
  });

  // 图表引用
  const chartRef = useRef<HTMLCanvasElement>(null)
  // 存储EventSource实例以便在需要时关闭
  const eventSourceRef = useRef<EventSource | null>(null)

  // 在组件顶部添加计数器引用
  const processingStepIdRef = useRef(1)

  // 切换折叠状态
  const toggleCollapse = (section: string) => {
    setCollapsedSections(prev => ({
      ...prev,
      [section]: !prev[section as keyof typeof prev]
    }));
  }

  // 处理最终SQL结果
  const handleFinalSql = (sql: string) => {
    console.log('收到最终SQL结果，关闭流式状态', sql);
    // 标记SQL区域流式输出结束
    setRegionOutputs(prev => ({
      ...prev,
      sql: {
        ...prev.sql,
        streaming: false,
        finalResult: sql,
        hasContent: true
      }
    }));
    setSqlResult(sql);
  };

  // 处理最终解释结果
  const handleFinalExplanation = (explanation: string) => {
    console.log('收到最终解释结果，关闭流式状态');
    // 标记解释区域流式输出结束
    setRegionOutputs(prev => ({
      ...prev,
      explanation: {
        ...prev.explanation,
        streaming: false,
        hasContent: true  // 确保区域被标记为有内容
      }
    }));
    setExplanationResult(explanation);
  }

  // 处理最终数据结果
  const handleFinalData = (data: any[]) => {
    console.log('收到最终数据结果，关闭流式状态');
    // 标记数据区域流式输出结束
    setRegionOutputs(prev => ({
      ...prev,
      data: {
        ...prev.data,
        streaming: false,
        hasContent: true  // 确保区域被标记为有内容
      }
    }));
    setDataResult(data);
  }

  // 处理最终可视化结果
  const handleFinalVisualization = (visualization: FinalVisualizationData) => {
    console.log('收到最终可视化结果，关闭流式状态');
    // 标记可视化区域流式输出结束
    setRegionOutputs(prev => ({
      ...prev,
      visualization: {
        ...prev.visualization,
        streaming: false,
        hasContent: true  // 确保区域被标记为有内容
      }
    }));
    setVisualizationResult(visualization);
  }

  // 处理最终分析结果
  const handleFinalAnalysis = (analysis: string) => {
    console.log('收到最终分析结果，关闭流式状态');
    // 标记分析区域流式输出结束
    setRegionOutputs(prev => ({
      ...prev,
      analysis: {
        ...prev.analysis,
        streaming: false,
        hasContent: true
      }
    }));
  }

  // 处理最终结果
  const handleResult = (finalResult: Text2SQLResponse) => {
    setError(null); // 清除错误

    // 检查所有区域的流式输出是否都已结束
    const allRegionsCompleted = Object.values(regionOutputs).every(region => !region.streaming);

    // 标记所有区域流式输出结束
    setRegionOutputs(prev => {
      const updated = { ...prev };
      Object.keys(updated).forEach(key => {
        const region = updated[key as keyof typeof updated];
        region.streaming = false;
      });
      return updated;
    });

    // 设置最终结果的所有部分
    setSqlResult(finalResult.sql);
    setExplanationResult(finalResult.explanation);
    setDataResult(finalResult.results);
    setVisualizationResult({
      type: finalResult.visualization_type,
      config: finalResult.visualization_config
    });

    // 只有当所有区域都不在流式处理中时，才设置 loading 为 false
    if (allRegionsCompleted) {
      setLoading(false);
      console.log('所有处理已完成，分析按钮恢复');
    }
  }

  // 处理错误
  const handleError = (error: Error) => {
    console.error('处理出错:', error);
    setError(error.message || '请求处理过程中发生错误');
    setLoading(false); // 发生错误时一定要停止加载状态

    // 重置所有区域的流式状态
    setRegionOutputs(prev => {
      const updated = { ...prev };
      Object.keys(updated).forEach(key => {
        const region = updated[key as keyof typeof updated];
        region.streaming = false;
      });
      return updated;
    });
  }

  // 添加页面切换函数
  const handlePageChange = (pageNumber: number) => {
    setCurrentPage(pageNumber);
  };

  // 添加计算总页数的函数
  const getTotalPages = () => {
    if (!dataResult) return 1;
    return Math.ceil(dataResult.length / pageSize);
  };

  // 获取当前页的数据
  const getCurrentPageData = () => {
    if (!dataResult) return [];
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return dataResult.slice(startIndex, endIndex);
  };

  // 重置处理状态
  const resetProcessingState = () => {
    setError(null);
    setLoading(false);
    setProcessingSteps([]);
    setCurrentPage(1); // 重置分页状态
    setRegionOutputs({
      analysis: {
        merged: '',
        messages: [],
        hasContent: false,
        streaming: false
      },
      sql: {
        merged: '',
        messages: [],
        hasContent: false,
        streaming: false
      },
      explanation: {
        merged: '',
        messages: [],
        hasContent: false,
        streaming: false
      },
      data: {
        merged: '',
        messages: [],
        hasContent: false,
        streaming: false
      },
      visualization: {
        merged: '',
        messages: [],
        hasContent: false,
        streaming: false
      },
      process: {
        merged: '',
        messages: [],
        hasContent: false,
        streaming: false
      }
    });
    setSqlResult(null);
    setExplanationResult(null);
    setDataResult(null);
    setVisualizationResult(null);

    // 关闭之前的EventSource连接
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }

  // 流式查询处理
  const handleStreamSearch = () => {
    if (loading) return;

    setError(null);
    setLoading(true);
    resetProcessingState();

    if (!query.trim()) {
      setError('请输入有效的查询');
      setLoading(false);
      return;
    }

    // 初始化UI状态，确保分析区域可见
    console.log('初始化分析区域');
    setRegionOutputs(prev => ({
      ...prev,
      analysis: {
        ...prev.analysis,
        hasContent: true,
        streaming: true,
        merged: '正在分析您的问题，请稍候...\n\n',
        messages: [{
          source: '系统',
          content: '正在分析您的问题，请稍候...\n\n',
          region: 'analysis'
        }]
      }
    }));

    // 强制设置分析区域为展开状态
    setCollapsedSections(prev => ({
      ...prev,
      analysis: false
    }));

    // 直接在DOM上更新样式以确保分析区域可见
    setTimeout(() => {
      const analysisContainer = document.querySelector('.analysis-output-container');
      if (analysisContainer) {
        // 确保容器可见
        (analysisContainer as HTMLElement).style.display = 'block';
        (analysisContainer as HTMLElement).style.minHeight = '200px';

        // 滚动到分析区域
        analysisContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        console.log('滚动到analysis-output-container');
      } else {
        console.warn('找不到分析区域容器');
      }

      // 确保内容区域可见
      const contentArea = document.querySelector('.analysis-content');
      if (contentArea) {
        (contentArea as HTMLElement).style.minHeight = '100px';
        (contentArea as HTMLElement).style.display = 'block';
        console.log('设置analysis-content样式');
      } else {
        console.warn('找不到分析内容区域');
      }
    }, 100);

    // 使用WebSocket进行流式通信
    const socket = new Text2SQLWebSocket();

    socket.setCallbacks(
      handleMessage,
      handleResult,
      handleError,
      handleFinalSql,
      handleFinalExplanation,
      handleFinalData,
      handleFinalVisualization,
      handleFinalAnalysis
    );

    socket.connect();

    // 连接后等待一秒再发送，确保连接已建立
    setTimeout(() => {
      socket.sendQuery(query);
    }, 500);
  };

  // 组件卸载时关闭连接
  useEffect(() => {
    return () => {
      // 关闭EventSource连接
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }

      // 关闭WebSocket连接
      closeWebSocketConnection();
    };
  }, []);

  // 修改图表相关逻辑，减少页面抖动
  useEffect(() => {
    if (visualizationResult && dataResult && dataResult.length > 0 && chartRef.current) {
      // 添加一个标记，避免重复渲染
      if (chartRef.current.dataset.rendered === 'true') {
        return;
      }

      // 如果可视化类型是表格，跳过图表渲染
      if (visualizationResult.type === 'table') {
        console.log('表格类型可视化，跳过图表渲染');
        // 标记为已渲染，避免重复处理
        chartRef.current.dataset.rendered = 'true';
        return;
      }

      // 使用动态导入引入Chart.js
      import('chart.js/auto').then((ChartModule) => {
        const Chart = ChartModule.default;

        // 获取画布上下文
        const canvas = chartRef.current;
        if (!canvas) return;

        // 销毁现有图表
        try {
          const chartInstance = Chart.getChart(canvas);
          if (chartInstance) {
            chartInstance.destroy();
          }
        } catch (e) {
          console.log('No existing chart to destroy');
        }

        // 准备图表数据
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        try {
          // 标记为已渲染，避免重复渲染
          canvas.dataset.rendered = 'true';

          const chartType = visualizationResult.type as 'bar' | 'line' | 'pie' | 'scatter';
          const config = prepareChartConfig(chartType, visualizationResult.config, dataResult);
          new Chart(ctx, config);
        } catch (error) {
          console.error('图表渲染错误:', error);
        }
      });
    }

    // 清理函数
    return () => {
      if (chartRef.current) {
        // 重置已渲染标记
        chartRef.current.dataset.rendered = 'false';

        // 动态导入Chart.js并清理图表
        import('chart.js/auto').then((ChartModule) => {
          const Chart = ChartModule.default;
          try {
            const chartInstance = Chart.getChart(chartRef.current!);
            if (chartInstance) {
              chartInstance.destroy();
            }
          } catch (e) {
            console.log('Error cleaning up chart:', e);
          }
        }).catch(err => {
          console.error('清理图表时出错:', err);
        });
      }
    };
  }, [visualizationResult, dataResult]);

  // 添加图表配置准备函数
  const prepareChartConfig = (
    type: 'bar' | 'line' | 'pie' | 'scatter',
    config: any,
    data: any[]
  ) => {
    // 提取数据点
    const labels = data.map(item => {
      // 尝试获取X轴字段值
      const xField = config.xAxis || Object.keys(item)[0];
      return item[xField];
    });

    // 提取数据系列
    const yField = config.yAxis || Object.keys(data[0])[1];
    const dataPoints = data.map(item => item[yField]);

    // 生成配置
    return {
      type, // 使用正确的类型
      data: {
        labels: labels,
        datasets: [{
          label: config.title || '数据系列',
          data: dataPoints,
          backgroundColor: type === 'pie' ?
            ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'] :
            'rgba(54, 162, 235, 0.5)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: !!config.title,
            text: config.title || ''
          },
          tooltip: {
            enabled: true
          },
          legend: {
            display: type === 'pie'
          }
        }
      }
    };
  };

  // 修改处理消息的函数，改进格式检测
  const handleMessage = (message: StreamResponseMessage) => {
    // 清除错误状态
    setError(null);

    console.log('收到消息:', message);

    // 确定消息区域
    let region = message.region || 'process';
    const source = message.source || '系统';
    let content = message.content || '';

    // 检查是否包含已经添加过的用户反馈
    if (source.toString() === 'user_proxy' && region.toString() === 'analysis' && content.includes("用户反馈：")) {
      // 从内容中提取反馈文本
      const feedbackMatch = content.match(/用户反馈：(.*?)(?:\n|$)/);
      if (feedbackMatch && feedbackMatch[1]) {
        const feedbackText = feedbackMatch[1].trim();

        // 检查分析区域是否已包含相同反馈
        if (regionOutputs.analysis.merged.includes(`用户反馈：${feedbackText}`)) {
          console.log('检测到重复的用户反馈，跳过处理');
          return; // 直接返回，不处理重复的反馈
        }
      }
    }

    // 过滤掉后端返回的重复分隔符
    if (source === 'user_proxy' ||
        (region === 'analysis' && content.includes("----------------------------"))) {
      // 检查内容中是否包含分隔符
      if (content.includes("----------------------------")) {
        // 检查当前分析区域内容中是否已经包含了分隔符
        if (regionOutputs.analysis.merged.includes("----------------------------")) {
          // 已包含分隔符，去除消息中的分隔符以避免重复
          // 匹配用户反馈和用户同意操作两种情况的分隔符
          const userFeedbackRegex = /\n\n---+\n### 用户反馈：[^\n]*\n---+\n\n/g;
          const userApproveRegex = /\n\n---+\n### 用户已同意操作\n---+\n\n/g;

          // 尝试用两种正则表达式替换
          content = content.replace(userFeedbackRegex, "\n\n").replace(userApproveRegex, "\n\n");
          console.log('检测到重复分隔符，已移除');
        }
      }
    }

    // 如果是最终消息且来自"可视化推荐智能体"，则可能是完成信号
    const isFinalMessage = message.is_final === true && source === '可视化推荐智能体' && content.includes('处理完成');

    // 添加消息到对应区域，并优化合并逻辑
    setRegionOutputs(prev => {
      const updatedRegions = { ...prev };
      const regionData = updatedRegions[region as keyof typeof updatedRegions];

      if (!regionData) {
        console.error(`未知区域: ${region}`);
        return prev;
      }

      // 添加新消息到列表，使用处理后的内容
      regionData.messages = [...regionData.messages, {...message, content}];

      // 标记该区域已有内容
      regionData.hasContent = true;

      // 判断streaming状态
      regionData.streaming = message.is_final !== true;

      // 检查新消息的内容是否与已有内容的末尾重叠
      let newContent = content;
      const currentContent = regionData.merged;


      // 检查重叠，避免重复文本
      if (currentContent && newContent && currentContent.length > 0 && newContent.length > 0) {
        // 查找最长的重叠部分(从后向前最多检查100个字符，避免性能问题)
        const checkLength = Math.min(100, currentContent.length);
        let overlapLength = 0;

        for (let i = 1; i <= Math.min(checkLength, newContent.length); i++) {
          const endPart = currentContent.slice(currentContent.length - i);
          const startPart = newContent.slice(0, i);

          if (endPart === startPart) {
            overlapLength = i;
          }
        }

        // 如果有重叠，只添加非重叠部分
        if (overlapLength > 0) {
          newContent = newContent.slice(overlapLength);
        }
      }

      // 优化合并逻辑，按顺序累加内容
      // 如果是第一条消息且当前文本是占位符，则替换掉占位符
      if (regionData.messages.length === 1 &&
          (regionData.merged === '正在分析您的问题，生成SQL中...' ||
           regionData.merged === '' ||
           regionData.merged === '正在分析您的问题，请稍候...')) {
        regionData.merged = content;
        console.log(`区域 ${region} 初始化内容: ${content.substring(0, 50)}...`);
      } else {
        regionData.merged += newContent;
      }

      return updatedRegions;
    });

    // 更新处理步骤
    if (content && region === 'process') {
      const step: ProcessingStep = {
        id: processingStepIdRef.current++,
        message: content,
        timestamp: new Date(),
        source: source
      };

      setProcessingSteps(prev => [...prev, step]);
    }

    // 确保analysis区域不会被折叠
    if (region === 'analysis') {
      setCollapsedSections(prev => {
        // 只有当前是折叠状态时才需要更新
        if (prev.analysis) {
          console.log('展开analysis区域');
          return { ...prev, analysis: false };
        }
        return prev;
      });
    }

    // 自动滚动到当前活跃区域并确保内容可见
    setTimeout(() => {
      // 滚动到区域容器
      const regionContainer = document.querySelector(`.${region}-output-container`);
      if (regionContainer) {
        regionContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        console.log(`滚动到 ${region}-output-container`);
      } else {
        console.warn(`找不到区域容器: .${region}-output-container`);
      }

      // 确保内容区域内的滚动条也滚动到底部
      const contentContainer = document.querySelector(`.${region}-output-container .overflow-y-auto`);
      if (contentContainer) {
        contentContainer.scrollTop = contentContainer.scrollHeight;
      }

      // 特别处理查询分析区域，确保滚动正常
      if (region === 'analysis') {
        // 直接调用专门的分析区域滚动函数
        scrollAnalysisAreaToBottom();
      }
    }, 100); // 增加延迟时间，确保DOM已更新

    // 检查是否是用户代理消息，显示反馈区
    if (message.source === 'user_proxy' && message.content) {
      setUserFeedback({
        visible: true,
        message: '',
        promptMessage: message.content
      });
    }
  };

  // 在组件内添加useEffect来监控SQL区域的显示条件
  useEffect(() => {

  }, [sqlResult, regionOutputs.sql.hasContent, regionOutputs.analysis.streaming, regionOutputs.analysis.hasContent]);

  // 在 Text2SQL 组件内添加一个处理回车键的函数
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !loading && query.trim() !== '') {
      e.preventDefault();
      handleStreamSearch();
    }
  };

  // 处理用户反馈提交
  const handleFeedbackSubmit = () => {
    if (!userFeedback.message.trim()) return;

    try {
      console.log('发送用户反馈:', userFeedback.message);
      const ws = getWebSocketInstance();

      // 获取当前反馈消息
      const currentFeedback = userFeedback.message;

      // 在前端添加分隔符
      setRegionOutputs(prev => {
        const updatedRegions = { ...prev };
        const analysisRegion = updatedRegions.analysis;

        // 构建分隔符标记
        const separator = "\n\n----------------------------\n### 用户反馈：" + currentFeedback + "\n----------------------------\n\n";

        // 检查是否已经存在相同的反馈内容
        if (!analysisRegion.merged.includes(`用户反馈：${currentFeedback}`)) {
          analysisRegion.merged += separator;
        } else {
          console.log('该反馈已存在，不重复添加');
        }

        return updatedRegions;
      });

      ws.sendMessage(currentFeedback);

      // 清空并隐藏反馈区
      setUserFeedback({
        visible: false,
        message: '',
        promptMessage: ''
      });

      // 确保内容滚动到底部
      setTimeout(() => {
        scrollAnalysisAreaToBottom();
      }, 200);
    } catch (err) {
      console.error('发送用户反馈出错:', err);
      setError(`发送反馈失败: ${err}`);
    }
  };

  // 处理用户反馈取消
  const handleFeedbackCancel = () => {
    try {
      console.log('用户取消反馈');
      const ws = getWebSocketInstance();
      ws.sendMessage('取消操作');

      // 清空并隐藏反馈区
      setUserFeedback({
        visible: false,
        message: '',
        promptMessage: ''
      });
    } catch (err) {
      console.error('取消用户反馈出错:', err);
      setError(`取消反馈失败: ${err}`);
    }
  };

  // 处理用户同意操作
  const handleFeedbackApprove = () => {
    try {
      console.log('发送用户同意反馈: APPROVE');
      const ws = getWebSocketInstance();

      // 在前端添加分隔符 - 确保只添加一次
      setRegionOutputs(prev => {
        const updatedRegions = { ...prev };
        const analysisRegion = updatedRegions.analysis;

        // 只有在当前内容中不包含分隔符时才添加
        if (!analysisRegion.merged.includes("用户已同意操作") &&
            !analysisRegion.merged.includes("----------------------------")) {
          const separator = "\n\n----------------------------\n### 用户已同意操作\n----------------------------\n\n";
          analysisRegion.merged += separator;
        }

        return updatedRegions;
      });

      ws.sendMessage("APPROVE");

      // 清空并隐藏反馈区
      setUserFeedback({
        visible: false,
        message: '',
        promptMessage: ''
      });

      // 确保内容滚动到底部
      setTimeout(() => {
        scrollAnalysisAreaToBottom();
      }, 200);
    } catch (err) {
      console.error('发送同意反馈出错:', err);
      setError(`发送同意反馈失败: ${err}`);
    }
  };

  // 添加一个专门处理分析区域滚动的函数
  const scrollAnalysisAreaToBottom = () => {
    // 首先尝试滚动分析区域容器
    const analysisContainer = document.querySelector('.analysis-output-container');
    if (analysisContainer) {
      // 修改滚动视图策略 - 使用start而不是nearest
      analysisContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });

      // 尝试常见的内容容器选择器
      const selectors = [
        '.analysis-output-container .overflow-y-auto',
        '.analysis-output-container .prose',
        '.analysis-content',
        '.analysis-output-container div[class*="overflow"]',
        '.analysis-output-container > div > div',
        '.analysis-output-container .border.rounded-md',
        '.analysis-output-container .prose.prose-sm'
      ];

      let scrolled = false;

      // 尝试找到可滚动的容器并滚动到底部
      for (const selector of selectors) {
        const container = document.querySelector(selector);
        if (container && container instanceof HTMLElement) {
          try {
            // 强制设置overflow属性确保可滚动
            if (!scrolled && window.getComputedStyle(container).overflow === 'visible') {
              container.style.overflowY = 'auto';
            }

            container.scrollTop = container.scrollHeight;
            console.log(`已通过${selector}滚动到底部`);
            scrolled = true;
          } catch (e) {
            console.warn(`无法滚动元素 ${selector}:`, e);
          }
        }
      }

      // 如果上述方法都失败，使用更强制的方法滚动
      if (!scrolled) {
        // 查找分析区域内所有可能的滚动容器
        const scrollableElements = analysisContainer.querySelectorAll('div');

        scrollableElements.forEach(el => {
          if (el instanceof HTMLElement) {
            // 检查是否可滚动或可能成为滚动容器
            const style = window.getComputedStyle(el);
            const hasScroll = el.scrollHeight > el.clientHeight;
            const isScrollable = style.overflowY === 'auto' || style.overflowY === 'scroll';

            if (hasScroll || el.classList.contains('prose') || el.classList.contains('overflow-auto')) {
              try {
                // 强制设置滚动属性
                if (!isScrollable) {
                  el.style.overflowY = 'auto';
                  el.style.maxHeight = `${Math.max(300, window.innerHeight * 0.5)}px`;
                }

                el.scrollTop = el.scrollHeight;
                console.log('通过强制设置overflow属性滚动容器');
                scrolled = true;
              } catch (e) {
                console.warn('尝试滚动元素失败:', e);
              }
            }
          }
        });

        // 最后的备用方案：尝试使用window滚动
        if (!scrolled) {
          const contentElement = document.querySelector('.analysis-output-container .prose') ||
                                document.querySelector('.analysis-output-container div[class*="overflow"]');
          if (contentElement) {
            contentElement.scrollIntoView({ behavior: 'smooth', block: 'end' });
            console.log('使用最终备用方案滚动');
          }
        }
      }
    }
  };

  return (
    <div className="flex min-h-screen flex-col relative">
      <div className="wave-bg"></div>
      <div className="gemini-bg-dots absolute inset-0 opacity-10 z-0"></div>

      {/* 导航栏 */}
      <nav className="gemini-navbar">
        <div className="container mx-auto flex items-center justify-between py-3 px-4">
          <Link href="/" className="flex items-center space-x-2">
            <div className="h-9 w-9 relative overflow-hidden rounded-full bg-gradient-to-r from-blue-500 to-purple-600 p-2 shadow-md">
              <Brain className="h-full w-full text-white" />
            </div>
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">但问智能体平台</h1>
          </Link>
          <div className="hidden md:flex gap-6">
            <Link href="/customer-service" className="text-sm font-medium text-neutral-600 hover:text-blue-600 dark:text-neutral-300 dark:hover:text-blue-400 transition-colors">
              智能客服
            </Link>
            <Link href="/text2sql" className="text-sm font-medium text-blue-600 dark:text-blue-400 relative after:content-[''] after:absolute after:left-0 after:bottom-[-4px] after:w-full after:h-[2px] after:bg-blue-600 dark:after:bg-blue-400">
              Text2SQL
            </Link>
            <Link href="/knowledge-base" className="text-sm font-medium text-neutral-600 hover:text-blue-600 dark:text-neutral-300 dark:hover:text-blue-400 transition-colors">
              知识库问答
            </Link>
            <Link href="/copywriting" className="text-sm font-medium text-neutral-600 hover:text-blue-600 dark:text-neutral-300 dark:hover:text-blue-400 transition-colors">
              文案创作
            </Link>
          </div>
          <Link
            href="/dashboard"
            className="gemini-button-primary"
          >
            控制台
          </Link>
        </div>
      </nav>

      <main className="flex flex-1 flex-col pt-24 z-10">
        <div className="container mx-auto px-4">
          {/* 顶部标题部分 */}
          <div className="mb-12 text-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
              className="inline-block p-1.5 px-4 mb-6 rounded-full text-sm font-medium bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-300 border border-blue-100 dark:border-blue-800"
            >
              <span className="mr-2">✨</span> 自然语言转SQL解决方案（100% 自研）
            </motion.div>
            <motion.h1
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 text-3xl font-bold md:text-4xl bg-clip-text text-transparent bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600"
            >
              高性能Text2SQL数据分析智能体
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="mx-auto mb-8 max-w-2xl text-lg text-muted-foreground"
            >
              支持数据库：MySQL, PostgreSQL, SQLite, SQL Server, Oracle, ClickHouse, Snowflake, BigQuery, Presto, Hive, DuckDB
            </motion.p>
          </div>

          {/* 查询输入部分 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mx-auto mb-12 max-w-3xl"
          >
            <div className="mb-6 flex items-center">
              <div className="relative flex-1 shadow-md rounded-full">
                <Database className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-blue-500" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="例如：查询东部地区2023年销售额最高的5种产品"
                  className="w-full rounded-full border border-[var(--border)] bg-white py-4 pl-12 pr-24 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-30 transition-all dark:bg-neutral-900 dark:focus:ring-blue-400 dark:border-neutral-700"
                />
                <div className="absolute right-3 top-1/2 -translate-y-1/2 flex gap-2">
                  <button
                    onClick={handleStreamSearch} // 改用流式处理函数
                    disabled={loading || query.trim() === ''}
                    className={`flex items-center justify-center h-9 z-10 transition-all ${
                      loading
                        ? "px-4 rounded-full bg-blue-400 text-white dark:bg-blue-700 dark:text-white cursor-not-allowed"
                        : query.trim() === ''
                          ? "px-4 rounded-full bg-neutral-200 text-neutral-500 dark:bg-neutral-800 dark:text-neutral-400 cursor-not-allowed"
                          : "px-5 tech-button text-white rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700"
                    }`}
                  >
                    {loading ? (
                      <span className="flex items-center">
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        分析中
                      </span>
                    ) : (
                      <span className="flex items-center">
                        <Search className="mr-1 h-4 w-4" />
                        分析
                      </span>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* 错误消息 */}
            {error && (
              <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 dark:bg-red-900/20 dark:border-red-800">
                <div className="flex items-start">
                  <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5 mr-2" />
                  <div>
                    <h3 className="text-sm font-medium text-red-800 dark:text-red-300">
                      请求处理出错
                    </h3>
                    <p className="mt-1 text-sm text-red-700 dark:text-red-400">
                      {error}
                    </p>
                    <p className="mt-2 text-xs text-red-600 dark:text-red-500">
                      请检查网络连接或稍后再试。如果问题持续存在，请联系管理员。
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* 流式处理进度指示器 */}
            {loading && (
              <div className="mb-6">
                <div className="flex justify-between mb-2">
                  <div className={`text-sm ${processingSteps.some(step => step.source === '系统') ? 'text-blue-600' : 'text-gray-400'}`}>查询分析</div>
                  <div className={`text-sm ${processingSteps.some(step => step.source === 'SQL生成') ? 'text-blue-600' : 'text-gray-400'}`}>SQL生成</div>
                  <div className={`text-sm ${processingSteps.some(step => step.source === 'SQL解释') ? 'text-blue-600' : 'text-gray-400'}`}>SQL解释</div>
                  <div className={`text-sm ${processingSteps.some(step => step.source === '执行查询') ? 'text-blue-600' : 'text-gray-400'}`}>执行查询</div>
                  <div className={`text-sm ${processingSteps.some(step => step.source === '可视化生成') ? 'text-blue-600' : 'text-gray-400'}`}>可视化生成</div>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700">
                  <div className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{
                      width: `${(
                        processingSteps.filter(step => step.source === '系统').length * 20 +
                        processingSteps.filter(step => step.source === 'SQL生成').length * 20 +
                        processingSteps.filter(step => step.source === 'SQL解释').length * 20 +
                        processingSteps.filter(step => step.source === '执行查询').length * 20 +
                        processingSteps.filter(step => step.source === '可视化生成').length * 20
                      )}%`
                    }}></div>
                </div>
              </div>
            )}

            {/* 流式输出显示 */}
            {loading && regionOutputs.process.messages.length > 0 && (
              <div className="mb-6 max-h-40 overflow-y-auto p-4 rounded-lg bg-gray-50 dark:bg-gray-800 text-sm process-output-container">
                <FormattedOutput content={regionOutputs.process.merged} type="text" />
              </div>
            )}

            {/* 处理过程日志区域 */}
            {!collapsedSections.process && (
              <div className="p-4">
                <div className="max-h-60 overflow-y-auto text-sm text-gray-600 dark:text-gray-400 border rounded-lg p-3 bg-gray-50 dark:bg-gray-800/30">
                  <FormattedOutput content={regionOutputs.process.merged} type="text" />
                </div>
              </div>
            )}
          </motion.div>

          {/* 查询分析 */}
          {(loading || regionOutputs.analysis.hasContent) && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
              className="mx-auto rounded-xl border bg-white/90 backdrop-blur-sm shadow-md dark:bg-neutral-900/90 dark:border-neutral-800 overflow-hidden analysis-output-container mb-6"
              style={{
                display: 'block',
                minHeight: collapsedSections.analysis ? 'auto' : '100px'
              }}
            >
              <div className="flex items-center justify-between border-b p-4 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-950/30 dark:to-purple-950/30">
                <div className="flex items-center space-x-2">
                  <div className="rounded-full p-1.5 bg-gradient-to-r from-indigo-500 to-purple-600 text-white">
                    <Brain className="h-5 w-5" />
                  </div>
                  <h3 className="font-semibold text-gray-800 dark:text-gray-200">
                    查询分析
                    {regionOutputs.analysis.streaming ?
                      <span className="ml-2 text-xs text-indigo-500 animate-pulse">分析中...</span> :
                      regionOutputs.analysis.hasContent ? <span className="ml-2 text-xs text-green-500">已完成</span> : null
                    }
                  </h3>
                </div>
                <div className="flex items-center space-x-2">
                  {/* 折叠/展开按钮 */}
                  {regionOutputs.analysis.messages.length > 0 && (
                    <button
                      onClick={() => toggleCollapse('analysis')}
                      className="text-sm text-blue-600 hover:underline flex items-center"
                    >
                      {collapsedSections.analysis ? '展开分析' : '折叠分析'}
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className={`ml-1 transition-transform ${collapsedSections.analysis ? 'rotate-0' : 'rotate-180'}`}
                      >
                        <polyline points="6 9 12 15 18 9"></polyline>
                      </svg>
                    </button>
                  )}
                </div>
              </div>

              {/* 分析内容显示 - 简化版本 */}
              {!collapsedSections.analysis && (
                <div className="p-4">
                  <div className="min-h-[100px]" style={{ display: 'block' }}>
                    {!regionOutputs.analysis.merged || regionOutputs.analysis.merged === '正在分析您的问题，请稍候...\n\n' ? (
                      <div className="flex items-center justify-center min-h-[100px] text-gray-500 italic">
                        <div className="flex items-center">
                          <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          服务器响应中，请稍候...
                        </div>
                      </div>
                    ) : (
                      <div className="border border-gray-200 dark:border-gray-700 rounded-md p-3 bg-gray-50 dark:bg-gray-800/30 min-h-[100px] overflow-auto" style={{ maxHeight: 'calc(70vh - 100px)' }}>
                        {/* 使用FormattedOutput组件显示Markdown内容 */}
                        <div className="prose prose-sm max-w-none dark:prose-invert overflow-y-auto">
                          <FormattedOutput content={regionOutputs.analysis.merged} type="markdown" />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* 用户反馈区域 */}
              {userFeedback.visible && (
                <div className="p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/30">
                  <div className="mb-3 text-base font-medium text-gray-800 dark:text-gray-200 flex items-center">
                    <svg className="w-5 h-5 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    {userFeedback.promptMessage || '请提供您的反馈:'}
                  </div>
                  <div className="bg-white dark:bg-gray-900 shadow-md rounded-lg p-5 border border-gray-200 dark:border-gray-700">
                    <div className="text-sm text-gray-600 dark:text-gray-400 mb-3 border-l-4 border-blue-500 pl-3 py-1">
                      您的输入将发送到智能体进行处理。点击<strong className="text-blue-600 dark:text-blue-400">发送</strong>提交您的自定义反馈，点击<strong className="text-green-600 dark:text-green-400">同意</strong>快速批准操作。
                    </div>
                    <div className="mb-4 relative">
                      <input
                        type="text"
                        value={userFeedback.message}
                        onChange={(e) => setUserFeedback(prev => ({ ...prev, message: e.target.value }))}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleFeedbackSubmit();
                          }
                        }}
                        placeholder="输入您的反馈..."
                        className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 py-3 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 dark:text-white shadow-inner transition-all pl-10"
                        autoFocus
                      />
                      <svg className="absolute left-3 top-3 h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"></path>
                      </svg>
                    </div>
                    <div className="flex justify-end space-x-3">
                      <button
                        onClick={handleFeedbackApprove}
                        className="rounded-md px-4 py-2.5 text-sm font-medium text-green-800 bg-green-100 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-300 dark:hover:bg-green-800/40 transition-colors shadow-sm border border-green-200 dark:border-green-800/50 flex items-center"
                      >
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                        同意
                      </button>
                      <button
                        onClick={handleFeedbackSubmit}
                        disabled={!userFeedback.message.trim()}
                        className={`rounded-md px-4 py-2.5 text-sm font-medium transition-colors shadow-sm flex items-center ${
                          !userFeedback.message.trim()
                            ? 'bg-gray-100 text-gray-400 dark:bg-gray-800 dark:text-gray-500 cursor-not-allowed border border-gray-200 dark:border-gray-700'
                            : 'bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700 border border-blue-700 dark:border-blue-500'
                        }`}
                      >
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
                        </svg>
                        发送
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {/* SQL语句 - 只在收到SQL结果时显示 */}
          {(sqlResult && regionOutputs.sql.hasContent) && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="mx-auto rounded-xl border bg-white/90 backdrop-blur-sm shadow-md dark:bg-neutral-900/90 dark:border-neutral-800 overflow-hidden sql-output-container"
            >
              <div className="flex items-center justify-between border-b p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30">
                <div className="flex items-center space-x-2">
                  <div className="rounded-full p-1.5 bg-gradient-to-r from-blue-500 to-indigo-600 text-white">
                    <CodeIcon className="h-5 w-5" />
                  </div>
                  <h3 className="font-semibold text-gray-800 dark:text-gray-200">
                    SQL语句
                    {sqlResult ? <span className="ml-2 text-xs text-green-500">已完成</span> : null}
                  </h3>
                </div>
                <div className="flex items-center space-x-2">
                  {/* 复制按钮 */}
                  <button
                    className="rounded-full p-1.5 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
                    onClick={() => {
                      if (sqlResult) {
                        navigator.clipboard.writeText(sqlResult);
                      }
                    }}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* 最终SQL结果区域 - 只显示最终结果，修正SQL格式显示 */}
              <div className="overflow-x-auto p-4">
                <pre className="whitespace-pre-wrap rounded-lg bg-gray-50 p-4 text-sm dark:bg-gray-800 border border-gray-100 dark:border-gray-700 overflow-hidden relative shine-effect">
                  <FormattedOutput content={sqlResult} type="sql" />
                </pre>
              </div>
            </motion.div>
          )}

          {/* 解释 - 只在收到解释结果时显示 */}
          {(regionOutputs.explanation.hasContent) && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="mx-auto rounded-xl border bg-white/90 backdrop-blur-sm shadow-md dark:bg-neutral-900/90 dark:border-neutral-800 overflow-hidden explanation-output-container"
            >
              <div className="flex items-center justify-between border-b p-4 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-950/30 dark:to-purple-950/30">
                <div className="flex items-center space-x-2">
                  <div className="rounded-full p-1.5 bg-gradient-to-r from-indigo-500 to-purple-600 text-white">
                    <FileText className="h-5 w-5" />
                  </div>
                  <h3 className="font-semibold text-gray-800 dark:text-gray-200">
                    SQL解释
                    {regionOutputs.explanation.streaming ?
                      <span className="ml-2 text-xs text-indigo-500 animate-pulse">生成中...</span> :
                      regionOutputs.explanation.hasContent ? <span className="ml-2 text-xs text-green-500">已完成</span> : null
                    }
                  </h3>
                </div>
                {/* 折叠/展开按钮 */}
                {regionOutputs.explanation.messages.length > 0 && (
                  <button
                    onClick={() => toggleCollapse('explanation')}
                    className="text-sm text-blue-600 hover:underline flex items-center"
                  >
                    {collapsedSections.explanation ? '展开解释' : '折叠解释'}
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className={`ml-1 transition-transform ${collapsedSections.explanation ? 'rotate-0' : 'rotate-180'}`}
                    >
                      <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                  </button>
                )}
              </div>

              {/* 流式输出过程 - 始终显示流式内容 */}
              {!collapsedSections.explanation && (
                <div className="p-4">
                  <div className="prose prose-sm max-w-none dark:prose-invert">
                    <FormattedOutput content={regionOutputs.explanation.merged} type="markdown" />
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {/* 数据表格 - 只在收到数据结果时显示 */}
          {(dataResult && regionOutputs.data.hasContent) && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="mx-auto rounded-xl border bg-white/90 backdrop-blur-sm shadow-md dark:bg-neutral-900/90 dark:border-neutral-800 overflow-hidden data-output-container"
            >
              <div className="flex items-center justify-between border-b p-4 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-950/30 dark:to-blue-950/30">
                <div className="flex items-center space-x-2">
                  <div className="rounded-full p-1.5 bg-gradient-to-r from-purple-500 to-blue-600 text-white">
                    <Database className="h-5 w-5" />
                  </div>
                  <h3 className="font-semibold text-gray-800 dark:text-gray-200">
                    查询结果
                    {regionOutputs.data.streaming ?
                      <span className="ml-2 text-xs text-purple-500 animate-pulse">查询中...</span> :
                      dataResult ? <span className="ml-2 text-xs text-green-500">已完成</span> : null
                    }
                  </h3>
                  {dataResult && (
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      共 {dataResult.length} 条记录
                    </span>
                  )}
                </div>
                {/* 折叠/展开按钮 */}
                {regionOutputs.data.messages.length > 0 && (
                  <button
                    onClick={() => toggleCollapse('data')}
                    className="text-sm text-blue-600 hover:underline flex items-center"
                  >
                    {collapsedSections.data ? '展开结果' : '折叠结果'}
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className={`ml-1 transition-transform ${collapsedSections.data ? 'rotate-0' : 'rotate-180'}`}
                    >
                      <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                  </button>
                )}
              </div>

              {/* 流式输出过程 */}
              {regionOutputs.data.hasContent && !collapsedSections.data && (
                <div className="border-b p-3 bg-gray-50 dark:bg-gray-800/30">
                  <div className="max-h-60 overflow-y-auto text-sm text-gray-600 dark:text-gray-400">
                    <FormattedOutput content={regionOutputs.data.merged} type="json" />
                  </div>
                </div>
              )}

              {/* 最终结果，仅在流式输出完成后显示 */}
              {(dataResult || !regionOutputs.data.streaming) && (
                <div className="overflow-x-auto p-4">
                  {dataResult && dataResult.length > 0 ? (
                    <>
                      <table className="w-full">
                        <thead>
                          <tr className="bg-gray-50 dark:bg-gray-800">
                            {Object.keys(dataResult[0]).map((key) => (
                              <th key={key} className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                                {key.replace(/_/g, ' ')}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {getCurrentPageData().map((row, i) => (
                            <tr key={i} className={`border-t border-gray-100 dark:border-gray-800 ${i % 2 === 0 ? 'bg-white dark:bg-neutral-900' : 'bg-gray-50/50 dark:bg-gray-800/50'}`}>
                              {Object.values(row).map((value, j) => (
                                <td key={j} className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                                  {typeof value === 'number'
                                    ? value.toLocaleString('zh-CN')
                                    : String(value)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>

                      {/* 分页控件 */}
                      {dataResult.length > pageSize && (
                        <div className="flex items-center justify-between border-t border-gray-200 dark:border-gray-700 px-4 py-3 sm:px-6 mt-4">
                          <div className="flex flex-1 justify-between sm:hidden">
                            <button
                              onClick={() => handlePageChange(currentPage > 1 ? currentPage - 1 : 1)}
                              disabled={currentPage === 1}
                              className={`relative inline-flex items-center rounded-md border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium ${
                                currentPage === 1
                                  ? 'bg-gray-100 text-gray-400 dark:bg-gray-800'
                                  : 'bg-white text-gray-700 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700'
                              }`}
                            >
                              上一页
                            </button>
                            <button
                              onClick={() => handlePageChange(currentPage < getTotalPages() ? currentPage + 1 : getTotalPages())}
                              disabled={currentPage === getTotalPages()}
                              className={`ml-3 relative inline-flex items-center rounded-md border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm font-medium ${
                                currentPage === getTotalPages()
                                  ? 'bg-gray-100 dark:bg-gray-800'
                                  : 'bg-white text-gray-700 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700'
                              }`}
                            >
                              下一页
                            </button>
                          </div>
                          <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                            <div>
                              <p className="text-sm text-gray-700 dark:text-gray-300">
                                显示第 <span className="font-medium">{(currentPage - 1) * pageSize + 1}</span> 至 <span className="font-medium">{Math.min(currentPage * pageSize, dataResult.length)}</span> 条，共 <span className="font-medium">{dataResult.length}</span> 条
                              </p>
                            </div>
                            <div>
                              <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                                <button
                                  onClick={() => handlePageChange(1)}
                                  disabled={currentPage === 1}
                                  className={`relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 dark:text-gray-500 ${
                                    currentPage === 1
                                      ? 'bg-gray-100 dark:bg-gray-800'
                                      : 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700'
                                  }`}
                                >
                                  <span className="sr-only">首页</span>
                                  <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                    <path fillRule="evenodd" d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z" clipRule="evenodd" />
                                  </svg>
                                  <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                    <path fillRule="evenodd" d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z" clipRule="evenodd" />
                                  </svg>
                                </button>
                                <button
                                  onClick={() => handlePageChange(currentPage > 1 ? currentPage - 1 : 1)}
                                  disabled={currentPage === 1}
                                  className={`relative inline-flex items-center px-2 py-2 text-gray-400 dark:text-gray-500 ${
                                    currentPage === 1
                                      ? 'bg-gray-100 dark:bg-gray-800'
                                      : 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700'
                                  }`}
                                >
                                  <span className="sr-only">上一页</span>
                                  <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                    <path fillRule="evenodd" d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z" clipRule="evenodd" />
                                  </svg>
                                </button>

                                {/* 页码按钮 */}
                                {Array.from({ length: getTotalPages() }).map((_, i) => {
                                  // 只显示当前页附近的页码
                                  if (
                                    i + 1 === 1 || // 首页
                                    i + 1 === getTotalPages() || // 尾页
                                    (i + 1 >= currentPage - 1 && i + 1 <= currentPage + 1) // 当前页及其前后页
                                  ) {
                                    return (
                                      <button
                                        key={i}
                                        onClick={() => handlePageChange(i + 1)}
                                        className={`relative inline-flex items-center px-4 py-2 text-sm font-medium ${
                                          currentPage === i + 1
                                            ? 'z-10 bg-blue-50 border-blue-500 text-blue-600 dark:bg-blue-900/30 dark:border-blue-500 dark:text-blue-400'
                                            : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700'
                                        } border`}
                                      >
                                        {i + 1}
                                      </button>
                                    );
                                  } else if (
                                    (i + 1 === 2 && currentPage > 3) ||
                                    (i + 1 === getTotalPages() - 1 && currentPage < getTotalPages() - 2)
                                  ) {
                                    // 显示省略号
                                    return (
                                      <span
                                        key={i}
                                        className="relative inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 bg-white dark:bg-gray-800 dark:border-gray-600 dark:text-gray-400"
                                      >
                                        ...
                                      </span>
                                    );
                                  }
                                  return null;
                                })}

                                <button
                                  onClick={() => handlePageChange(currentPage < getTotalPages() ? currentPage + 1 : getTotalPages())}
                                  disabled={currentPage === getTotalPages()}
                                  className={`relative inline-flex items-center px-2 py-2 text-gray-400 dark:text-gray-500 ${
                                    currentPage === getTotalPages()
                                      ? 'bg-gray-100 dark:bg-gray-800'
                                      : 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700'
                                  }`}
                                >
                                  <span className="sr-only">下一页</span>
                                  <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                    <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
                                  </svg>
                                </button>
                                <button
                                  onClick={() => handlePageChange(getTotalPages())}
                                  disabled={currentPage === getTotalPages()}
                                  className={`relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 dark:text-gray-500 ${
                                    currentPage === getTotalPages()
                                      ? 'bg-gray-100 dark:bg-gray-800'
                                      : 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700'
                                  }`}
                                >
                                  <span className="sr-only">尾页</span>
                                  <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                    <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
                                  </svg>
                                  <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                    <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
                                  </svg>
                                </button>
                              </nav>
                            </div>
                          </div>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="animate-pulse flex space-x-4">
                      <div className="flex-1 space-y-3 py-1">
                        <div className="h-4 bg-gray-200 rounded dark:bg-gray-700"></div>
                        <div className="h-4 bg-gray-200 rounded dark:bg-gray-700 w-5/6"></div>
                        <div className="h-4 bg-gray-200 rounded dark:bg-gray-700 w-4/6"></div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          )}

          {/* 图表 - 只在收到可视化结果时显示 */}
          {(visualizationResult && regionOutputs.visualization.hasContent) && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="mx-auto rounded-xl border bg-white/90 backdrop-blur-sm shadow-md dark:bg-neutral-900/90 dark:border-neutral-800 overflow-hidden visualization-output-container"
            >
              <div className="flex items-center justify-between border-b p-4 bg-gradient-to-r from-blue-50 to-green-50 dark:from-blue-950/30 dark:to-green-950/30">
                <div className="flex items-center space-x-2">
                  <div className="rounded-full p-1.5 bg-gradient-to-r from-blue-500 to-green-500 text-white">
                    <BarChart className="h-5 w-5" />
                  </div>
                  <h3 className="font-semibold text-gray-800 dark:text-gray-200">
                    数据可视化 {visualizationResult?.type ?
                      (visualizationResult.type === 'table' ? '- 表格' : `- ${visualizationResult.type}`) : ''}
                    {regionOutputs.visualization.streaming ?
                      <span className="ml-2 text-xs text-green-500 animate-pulse">生成中...</span> :
                      visualizationResult ? <span className="ml-2 text-xs text-green-500">已完成</span> : null
                    }
                  </h3>
                </div>
              </div>

              {/* 图表或表格显示 */}
              <div className="p-4">
                {/* 表格类型可视化 */}
                {visualizationResult && visualizationResult.type === 'table' ? (
                  <div className="rounded-lg border border-gray-200 dark:border-gray-700">
                    {visualizationResult.config && visualizationResult.config.title && (
                      <div className="p-3 border-b border-gray-200 dark:border-gray-700 text-center font-medium">
                        {visualizationResult.config.title}
                      </div>
                    )}
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="bg-gray-50 dark:bg-gray-800">
                            {visualizationResult.config && visualizationResult.config.columns ?
                              visualizationResult.config.columns.map((column: string) => (
                                <th key={column} className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                                  {column}
                                </th>
                              )) :
                              dataResult && dataResult.length > 0 && Object.keys(dataResult[0]).map((key) => (
                                <th key={key} className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                                  {key}
                                </th>
                              ))
                            }
                          </tr>
                        </thead>
                        <tbody>
                          {dataResult && dataResult.map((row, i) => (
                            <tr key={i} className={`border-t border-gray-100 dark:border-gray-800 ${i % 2 === 0 ? 'bg-white dark:bg-neutral-900' : 'bg-gray-50/50 dark:bg-gray-800/50'}`}>
                              {visualizationResult.config && visualizationResult.config.columns ?
                                visualizationResult.config.columns.map((column: string) => (
                                  <td key={`${i}-${column}`} className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                                    {typeof row[column] === 'number'
                                      ? row[column].toLocaleString('zh-CN')
                                      : String(row[column])}
                                  </td>
                                )) :
                                Object.values(row).map((value, j) => (
                                  <td key={j} className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                                    {typeof value === 'number'
                                      ? value.toLocaleString('zh-CN')
                                      : String(value)}
                                  </td>
                                ))
                              }
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <div className="h-80 rounded-lg border border-dashed flex items-center justify-center bg-gray-50/50 dark:bg-gray-800/50 relative overflow-hidden">
                    {/* 图表容器，将使用useRef引用 */}
                    <canvas
                      id="resultChart"
                      ref={chartRef}
                      className="w-full h-full z-10"
                    ></canvas>

                    {/* 加载指示器，只在生成中显示 */}
                    {!visualizationResult && (regionOutputs.visualization.streaming || loading) && (
                      <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-50/80 dark:bg-gray-800/80 z-20">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-2"></div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">生成可视化中...</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </div>
      </main>

      {/* 页脚 */}
      <footer className="relative z-10 border-t py-8 bg-white/80 backdrop-blur-sm dark:bg-neutral-900/80 dark:border-neutral-800">
        <div className="container mx-auto px-4 text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            © {new Date().getFullYear()} 但问智能体综合应用平台. 保留所有权利.
          </p>
        </div>
      </footer>
    </div>
  )
}