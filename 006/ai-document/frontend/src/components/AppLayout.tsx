import React from 'react';
import { Layout } from 'antd';
import GlobalNavigation from './GlobalNavigation';

const { Content } = Layout;

interface AppLayoutProps {
  children: React.ReactNode;
  showNavigation?: boolean;
}

const AppLayout: React.FC<AppLayoutProps> = ({ 
  children, 
  showNavigation = true 
}) => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      {showNavigation && <GlobalNavigation />}
      <Content style={{ 
        flex: 1,
        display: 'flex',
        flexDirection: 'column'
      }}>
        {children}
      </Content>
    </Layout>
  );
};

export default AppLayout;
