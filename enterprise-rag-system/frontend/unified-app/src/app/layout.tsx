import type { Metadata } from 'next';
import { ConfigProvider } from 'antd';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { AuthProvider } from '@/contexts/AuthContext';
import { QueryProvider } from '@/contexts/QueryProvider';
import './globals.css';

export const metadata: Metadata = {
  title: '企业级RAG知识库系统',
  description: '基于AutoGen智能体协作的企业级知识库系统 - 现代化统一界面',
  keywords: ['RAG', '知识库', 'AI', '智能体', 'AutoGen', 'Gemini', '企业级'],
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
        <meta name="theme-color" content="#0ea5e9" />
        <link rel="icon" href="/favicon.ico" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body suppressHydrationWarning className="font-sans antialiased">
        <QueryProvider>
          <AuthProvider>
            <ThemeProvider>
              <ConfigProvider
                theme={{
                  token: {
                    fontFamily: '"Inter", "Google Sans", "Roboto", -apple-system, BlinkMacSystemFont, sans-serif',
                    colorPrimary: '#0ea5e9',
                    borderRadius: 8,
                  },
                }}
              >
                {children}
              </ConfigProvider>
            </ThemeProvider>
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
