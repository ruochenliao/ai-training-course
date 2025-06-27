import type {Metadata} from 'next';
import {ConfigProvider} from 'antd';
import {ThemeProvider} from '@/contexts/ThemeContext';
import './globals.css';

export const metadata: Metadata = {
  title: '企业级RAG知识库系统',
  description: '基于AutoGen智能体协作的企业级知识库系统 - Gemini风格界面',
  keywords: ['RAG', '知识库', 'AI', '智能体', 'AutoGen', 'Gemini'],
  authors: [{ name: 'Enterprise RAG Team' }],
  viewport: 'width=device-width, initial-scale=1',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <head>
        <meta name="theme-color" content="#1a73e8" />
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body suppressHydrationWarning>
        <ThemeProvider>
          <ConfigProvider
            theme={{
              token: {
                fontFamily: '"Google Sans", "Roboto", -apple-system, BlinkMacSystemFont, sans-serif',
              },
            }}
          >
            {children}
          </ConfigProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
