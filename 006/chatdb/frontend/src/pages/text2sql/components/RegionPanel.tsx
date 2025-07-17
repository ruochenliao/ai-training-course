import React, { useRef, useEffect } from 'react';
import { Collapse, Table, Button, Tooltip, Spin, Typography } from 'antd';
import {
  CopyOutlined,
  DownloadOutlined,
  DownOutlined,
  RightOutlined,
  SearchOutlined,
  CodeOutlined,
  BarChartOutlined,
  BulbOutlined,
  TableOutlined
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import StreamingMarkdown from './StreamingMarkdown';
import { FormattedOutput as OutputFormatter } from '../utils';

const { Panel } = Collapse;
const { Text } = Typography;

// 图表渲染组件
interface ChartRendererProps {
  visualizationResult: any;
  dataResult: any[];
}

const ChartRenderer: React.FC<ChartRendererProps> = ({ visualizationResult, dataResult }) => {
  const chartRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (visualizationResult && dataResult && dataResult.length > 0 && chartRef.current) {
      // 添加一个标记，避免重复渲染
      if (chartRef.current.dataset.rendered === 'true') {
        return;
      }

      // 如果可视化类型是表格，跳过图表渲染
      if (visualizationResult.type === 'table') {
        console.log('表格类型可视化，跳过图表渲染');
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
          console.log('✅ 图表渲染成功');
        } catch (error) {
          console.error('❌ 图表渲染错误:', error);
        }
      }).catch(err => {
        console.error('❌ Chart.js加载失败:', err);
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

  // 准备图表配置
  const prepareChartConfig = (
    type: 'bar' | 'line' | 'pie' | 'scatter',
    config: any,
    data: any[]
  ) => {
    console.log('📊 准备图表配置:', { type, config, dataLength: data.length });

    // 提取数据点
    const labels = data.map(item => {
      // 尝试获取X轴字段值
      const xField = config?.xAxis || config?.x || Object.keys(item)[0];
      return item[xField];
    });

    // 提取数据系列
    const yField = config?.yAxis || config?.y || Object.keys(data[0])[1];
    const dataPoints = data.map(item => item[yField]);

    console.log('📈 图表数据:', { labels, dataPoints, xField: config?.xAxis || config?.x, yField });

    // 生成配置
    return {
      type,
      data: {
        labels: labels,
        datasets: [{
          label: config?.title || config?.label || '数据系列',
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
            display: !!(config?.title),
            text: config?.title || ''
          },
          tooltip: {
            enabled: true
          },
          legend: {
            display: type === 'pie'
          }
        },
        scales: type !== 'pie' ? {
          y: {
            beginAtZero: true
          }
        } : undefined
      }
    };
  };

  return (
    <div style={{
      padding: '16px',
      backgroundColor: '#fff',
      borderRadius: '6px',
      minHeight: '400px',
      position: 'relative'
    }}>
      <div style={{
        marginBottom: '12px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <BarChartOutlined style={{ color: '#eb2f96' }} />
          <span style={{ fontWeight: 500 }}>
            {visualizationResult?.config?.title || '数据可视化'}
          </span>
          <span style={{ fontSize: '12px', color: '#8c8c8c' }}>
            ({visualizationResult?.type || '未知类型'})
          </span>
        </div>
      </div>

      <div style={{ height: '350px', position: 'relative' }}>
        <canvas ref={chartRef} style={{ width: '100%', height: '100%' }} />
      </div>

      {visualizationResult?.type === 'table' && (
        <div style={{
          textAlign: 'center',
          color: '#8c8c8c',
          fontSize: '14px',
          marginTop: '20px'
        }}>
          表格类型数据，请查看"查询结果"区域
        </div>
      )}
    </div>
  );
};

// 区域配置 - 与XStreamOutput完全一致
const REGION_CONFIG = {
  analysis: {
    title: '查询分析',
    icon: <SearchOutlined />,
    color: '#1890ff',
    contentType: 'markdown' as const
  },
  sql: {
    title: 'SQL语句',
    icon: <CodeOutlined />,
    color: '#52c41a',
    contentType: 'sql' as const
  },
  explanation: {
    title: '语句解释',
    icon: <BulbOutlined />,
    color: '#faad14',
    contentType: 'markdown' as const
  },
  data: {
    title: '查询结果',
    icon: <TableOutlined />,
    color: '#722ed1',
    contentType: 'table' as const
  },
  visualization: {
    title: '数据可视化',
    icon: <BarChartOutlined />,
    color: '#eb2f96',
    contentType: 'chart' as const
  }
};

// 内容渲染组件 - 与XStreamOutput完全一致
const ContentRenderer: React.FC<{
  content: string;
  type: 'markdown' | 'sql' | 'json' | 'text' | 'table' | 'chart';
  isStreaming: boolean;
  visualizationResult?: any;
  dataResult?: any[];
  region?: string; // 添加区域参数
}> = ({ content, type, isStreaming, visualizationResult, dataResult, region }) => {
  const renderContent = () => {
    if (!content) return null;

    switch (type) {
      case 'sql':
        return (
          <SyntaxHighlighter
            language="sql"
            style={tomorrow as any}
            showLineNumbers={true}
            wrapLines={true}
            customStyle={{
              margin: 0,
              borderRadius: '6px',
              fontSize: '14px'
            }}
          >
            {content}
          </SyntaxHighlighter>
        );

      case 'json':
        try {
          const parsed = JSON.parse(content);
          return (
            <SyntaxHighlighter
              language="json"
              style={tomorrow as any}
              showLineNumbers={true}
              wrapLines={true}
              customStyle={{
                margin: 0,
                borderRadius: '6px',
                fontSize: '14px'
              }}
            >
              {JSON.stringify(parsed, null, 2)}
            </SyntaxHighlighter>
          );
        } catch {
          return (
            <pre style={{
              margin: 0,
              padding: '12px',
              backgroundColor: '#f5f5f5',
              borderRadius: '6px',
              fontSize: '14px',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word'
            }}>
              {content}
            </pre>
          );
        }

      case 'table':
        try {
          const data = JSON.parse(content);
          if (Array.isArray(data) && data.length > 0) {
            // 自动生成表格列
            const columns = Object.keys(data[0]).map(key => ({
              title: key,
              dataIndex: key,
              key: key,
              ellipsis: true,
              width: 150
            }));

            // 添加行键
            const dataSource = data.map((row, index) => ({
              ...row,
              key: index
            }));

            return (
              <Table
                columns={columns}
                dataSource={dataSource}
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total) => `共 ${total} 条记录`
                }}
                scroll={undefined}
                size="small"
                style={{ fontSize: '14px' }}
              />
            );
          } else {
            return (
              <div style={{
                padding: '20px',
                textAlign: 'center',
                color: '#8c8c8c',
                backgroundColor: '#f5f5f5',
                borderRadius: '6px'
              }}>
                暂无数据
              </div>
            );
          }
        } catch {
          return (
            <pre style={{
              margin: 0,
              padding: '12px',
              backgroundColor: '#f5f5f5',
              borderRadius: '6px',
              fontSize: '14px',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word'
            }}>
              {content}
            </pre>
          );
        }

      case 'chart':
        // 如果有visualizationResult和dataResult，渲染实际图表
        if (visualizationResult && dataResult && dataResult.length > 0) {
          return <ChartRenderer visualizationResult={visualizationResult} dataResult={dataResult} />;
        }

        // 否则显示可视化信息
        try {
          const chartData = JSON.parse(content);
          return (
            <div style={{
              padding: '16px',
              backgroundColor: '#f9f9f9',
              borderRadius: '6px',
              minHeight: '200px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column',
              gap: '12px'
            }}>
              <BarChartOutlined style={{ fontSize: '32px', color: '#eb2f96' }} />
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '16px', fontWeight: 500, marginBottom: '8px' }}>
                  数据可视化
                </div>
                <div style={{ fontSize: '14px', color: '#8c8c8c' }}>
                  图表类型: {chartData.type || '未知'}
                </div>
                {chartData.title && (
                  <div style={{ fontSize: '14px', color: '#8c8c8c' }}>
                    标题: {chartData.title}
                  </div>
                )}
              </div>
              <details style={{ width: '100%', marginTop: '12px' }}>
                <summary style={{ cursor: 'pointer', fontSize: '12px', color: '#666' }}>
                  查看原始数据
                </summary>
                <pre style={{
                  margin: '8px 0 0 0',
                  padding: '8px',
                  backgroundColor: '#fff',
                  borderRadius: '4px',
                  fontSize: '12px',
                  overflow: 'auto',
                  maxHeight: '200px'
                }}>
                  {JSON.stringify(chartData, null, 2)}
                </pre>
              </details>
            </div>
          );
        } catch {
          return (
            <div style={{
              padding: '16px',
              backgroundColor: '#f9f9f9',
              borderRadius: '6px',
              textAlign: 'center'
            }}>
              <BarChartOutlined style={{ fontSize: '24px', color: '#eb2f96', marginBottom: '8px' }} />
              <div style={{ fontSize: '14px', color: '#8c8c8c' }}>
                可视化数据格式错误
              </div>
              <pre style={{
                margin: '8px 0 0 0',
                padding: '8px',
                backgroundColor: '#fff',
                borderRadius: '4px',
                fontSize: '12px',
                textAlign: 'left'
              }}>
                {content}
              </pre>
            </div>
          );
        }

      case 'markdown':
        // 调试信息
        if (process.env.NODE_ENV === 'development') {
          console.log('🔍 使用OutputFormatter渲染:', {
            region,
            contentLength: content.length,
            contentPreview: content.substring(0, 100),
            isStreaming
          });
        }

        // 对于分析和解释区域，使用OutputFormatter以获得完全一致的格式效果
        if (region === 'analysis' || region === 'explanation') {
          return (
            <div className="prose prose-sm max-w-none analysis-content overflow-auto" style={{ maxHeight: 'none', overflowY: 'auto' }}>
              <div className="analysis-formatted-content">
                <OutputFormatter content={content} type="markdown" region={region} />
              </div>
            </div>
          );
        }

        // 其他区域使用StreamingMarkdown
        return (
          <StreamingMarkdown
            content={content}
            isStreaming={isStreaming}
            className="markdown-content"
          />
        );

      default:
        // 对于默认文本，尝试检测是否包含markdown格式
        if (content.includes('#') || content.includes('*') || content.includes('`') || content.includes('-')) {
          return (
            <div style={{ fontSize: '14px', lineHeight: '1.6' }} className="markdown-content">
              <ReactMarkdown
                components={{
                  // 使用相同的markdown组件配置
                  code: ({ node, inline, className, children, ...props }: any) => {
                    const match = /language-(\w+)/.exec(className || '');
                    const language = match ? match[1] : '';

                    return !inline && language ? (
                      <SyntaxHighlighter
                        style={tomorrow as any}
                        language={language}
                        PreTag="div"
                        className="code-block"
                        showLineNumbers={true}
                        wrapLines={true}
                        customStyle={{
                          margin: '16px 0',
                          borderRadius: '6px',
                          fontSize: '14px'
                        }}
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code
                        className={`inline-code ${className || ''}`}
                        style={{
                          backgroundColor: '#f5f5f5',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          fontSize: '13px',
                          fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace'
                        }}
                        {...props}
                      >
                        {children}
                      </code>
                    );
                  },
                  p: ({ children }: any) => (
                    <div style={{ marginBottom: '12px', lineHeight: '1.6' }}>
                      {children}
                    </div>
                  ),
                  ul: ({ children }: any) => (
                    <ul style={{
                      marginLeft: '20px',
                      marginBottom: '12px',
                      listStyleType: 'disc'
                    }}>
                      {children}
                    </ul>
                  ),
                  ol: ({ children }: any) => (
                    <ol style={{
                      marginLeft: '20px',
                      marginBottom: '12px',
                      listStyleType: 'decimal'
                    }}>
                      {children}
                    </ol>
                  ),
                  li: ({ children }: any) => (
                    <li style={{ marginBottom: '4px', lineHeight: '1.5' }}>
                      {children}
                    </li>
                  ),
                  h1: ({ children }: any) => (
                    <h1 style={{
                      fontSize: '20px',
                      fontWeight: 600,
                      marginBottom: '12px',
                      marginTop: '16px',
                      color: '#1f2937'
                    }}>
                      {children}
                    </h1>
                  ),
                  h2: ({ children }: any) => (
                    <h2 style={{
                      fontSize: '18px',
                      fontWeight: 600,
                      marginBottom: '10px',
                      marginTop: '14px',
                      color: '#374151'
                    }}>
                      {children}
                    </h2>
                  ),
                  h3: ({ children }: any) => (
                    <h3 style={{
                      fontSize: '16px',
                      fontWeight: 600,
                      marginBottom: '8px',
                      marginTop: '12px',
                      color: '#4b5563'
                    }}>
                      {children}
                    </h3>
                  ),
                  strong: ({ children }: any) => (
                    <strong style={{ fontWeight: 600, color: '#1f2937' }}>
                      {children}
                    </strong>
                  ),
                  em: ({ children }: any) => (
                    <em style={{ fontStyle: 'italic', color: '#4b5563' }}>
                      {children}
                    </em>
                  )
                }}
              >
                {content}
              </ReactMarkdown>
            </div>
          );
        } else {
          // 纯文本显示
          return (
            <div style={{
              margin: 0,
              padding: '12px',
              backgroundColor: '#f9fafb',
              borderRadius: '6px',
              fontSize: '14px',
              lineHeight: '1.6',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              color: '#374151',
              border: '1px solid #e5e7eb'
            }}>
              {content}
            </div>
          );
        }
    }
  };

  return (
    <div style={{ position: 'relative' }}>
      {renderContent()}
      {isStreaming && (
        <div style={{
          position: 'absolute',
          bottom: '8px',
          right: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          padding: '4px 8px',
          backgroundColor: 'rgba(24, 144, 255, 0.1)',
          borderRadius: '4px',
          fontSize: '12px',
          color: '#1890ff'
        }}>
          <Spin size="small" />
          <Text type="secondary" style={{ fontSize: '12px' }}>正在生成...</Text>
        </div>
      )}
    </div>
  );
};

interface RegionPanelProps {
  title: string;
  content: string;
  isStreaming: boolean;
  hasContent: boolean;
  region: string;
  onCopyContent: (content: string, regionId: string) => void;
  dataResult?: any[] | null;
  visualizationResult?: any;
  currentPage?: number;
  pageSize?: number;
  handlePageChange?: (page: number) => void;
  getTotalPages?: () => number;
  getCurrentPageData?: () => any[];
  convertToCSV?: (data: any[]) => string;
}

const RegionPanel: React.FC<RegionPanelProps> = ({
  title,
  content,
  isStreaming,
  hasContent,
  region,
  onCopyContent,
  dataResult,
  visualizationResult,
  currentPage = 1,
  pageSize = 10,
  handlePageChange,
  getTotalPages,
  getCurrentPageData,
  convertToCSV
}) => {
  // 获取区域配置
  const config = REGION_CONFIG[region as keyof typeof REGION_CONFIG] || {
    title: title,
    icon: <SearchOutlined />,
    color: '#1890ff',
    contentType: 'text' as const
  };

  // 对于查询分析区域和语句解释区域，强制使用markdown格式
  const actualContentType = (region === 'analysis' || region === 'explanation') ? 'markdown' : config.contentType;

  // 调试信息（生产环境可移除）
  if (process.env.NODE_ENV === 'development') {
    console.log('RegionPanel 渲染:', {
      region,
      configContentType: config.contentType,
      actualContentType,
      contentLength: content.length,
      contentPreview: content.substring(0, 100)
    });
  }

  // 复制内容到剪贴板
  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(content);
      onCopyContent(content, region);
    } catch (err) {
      console.error('复制失败:', err);
    }
  };

  // 准备内容用于渲染
  const prepareContent = () => {
    if (region === 'data' && dataResult) {
      return JSON.stringify(dataResult, null, 2);
    }
    if (region === 'visualization' && visualizationResult) {
      return JSON.stringify(visualizationResult, null, 2);
    }
    return content;
  };

  return (
    <Collapse
      defaultActiveKey={[region]}
      expandIcon={({ isActive }) => isActive ? <DownOutlined /> : <RightOutlined />}
      style={{ backgroundColor: 'transparent', border: 'none', marginBottom: '16px' }}
    >
      <Panel
        key={region}
        header={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: config.color }}>{config.icon}</span>
            <span style={{ fontWeight: 500 }}>{config.title}</span>
            {isStreaming && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginLeft: 'auto', fontSize: '12px', color: '#1890ff' }}>
                <Spin size="small" />
                <Text type="secondary">正在生成...</Text>
              </div>
            )}
            {hasContent && !isStreaming && (
              <Tooltip title="复制内容">
                <Button
                  type="text"
                  size="small"
                  icon={<CopyOutlined />}
                  onClick={handleCopy}
                  style={{ marginLeft: 'auto' }}
                />
              </Tooltip>
            )}
          </div>
        }
        style={{
          borderLeft: isStreaming ? `3px solid ${config.color}` : undefined,
          backgroundColor: isStreaming ? `${config.color}08` : undefined
        }}
      >
        <ContentRenderer
          content={prepareContent()}
          type={actualContentType}
          isStreaming={isStreaming}
          visualizationResult={visualizationResult}
          dataResult={dataResult || undefined}
          region={region}
        />
      </Panel>
    </Collapse>
  );
};

export default RegionPanel;
