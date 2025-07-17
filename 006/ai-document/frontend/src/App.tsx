import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuthStore } from '@/stores/useAuthStore';
import AppLayout from '@/components/AppLayout';
import LoginPage from '@/pages/LoginPage';
import RegisterPage from '@/pages/RegisterPage';
import HomePage from '@/pages/HomePage';
import EditorPage from '@/pages/EditorPage';
import AIWritingWizard from '@/pages/AIWritingWizard';
import SimpleAIWritingWizard from '@/pages/SimpleAIWritingWizard';
import TemplateManagement from '@/pages/TemplateManagement';
import AgentManagement from '@/pages/AgentManagement';
import AIToolsPage from '@/pages/AIToolsPage';
import EditorWithAITools from '@/pages/EditorWithAITools';
import SimpleEditorPage from '@/pages/SimpleEditorPage';
import StandardEditorPage from '@/pages/StandardEditorPage';
import AIWritingEditorPage from '@/pages/AIWritingEditorPage';
import WritingThemeManagementPage from './pages/WritingThemeManagementPage';
import ThemeFieldConfigPage from './pages/ThemeFieldConfigPage';
import TemplateManagementPage from './pages/TemplateManagementPage';
import DebugPage from './pages/DebugPage';

const App: React.FC = () => {
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

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
    <Routes>
      <Route 
        path="/login" 
        element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />} 
      />
      <Route 
        path="/register" 
        element={isAuthenticated ? <Navigate to="/" replace /> : <RegisterPage />} 
      />
      <Route
        path="/"
        element={isAuthenticated ? (
          <AppLayout>
            <HomePage />
          </AppLayout>
        ) : <Navigate to="/login" replace />}
      />
      <Route
        path="/editor/:id?"
        element={isAuthenticated ? (
          <AppLayout>
            <EditorPage />
          </AppLayout>
        ) : <Navigate to="/login" replace />}
      />
      <Route
        path="/ai-tools"
        element={isAuthenticated ? (
          <AppLayout>
            <AIToolsPage />
          </AppLayout>
        ) : <Navigate to="/login" replace />}
      />
      <Route
        path="/editor-with-ai"
        element={isAuthenticated ? (
          <AppLayout>
            <EditorWithAITools />
          </AppLayout>
        ) : <Navigate to="/login" replace />}
      />
      <Route
        path="/simple-editor"
        element={isAuthenticated ? (
          <AppLayout>
            <SimpleEditorPage />
          </AppLayout>
        ) : <Navigate to="/login" replace />}
      />
      <Route
        path="/standard-editor"
        element={isAuthenticated ? (
          <AppLayout>
            <StandardEditorPage />
          </AppLayout>
        ) : <Navigate to="/login" replace />}
      />
      <Route
        path="/ai-writing-editor"
        element={isAuthenticated ? (
          <AppLayout>
            <AIWritingEditorPage />
          </AppLayout>
        ) : <Navigate to="/login" replace />}
      />
      <Route
        path="/ai-writing"
        element={isAuthenticated ? (
          <AppLayout>
            <AIWritingWizard />
          </AppLayout>
        ) : <Navigate to="/login" replace />}
      />
      <Route
        path="/ai-writing-simple"
        element={isAuthenticated ? (
          <AppLayout>
            <SimpleAIWritingWizard />
          </AppLayout>
        ) : <Navigate to="/login" replace />}
      />
      <Route
        path="/templates"
        element={isAuthenticated ? (
          <AppLayout>
            <TemplateManagement />
          </AppLayout>
        ) : <Navigate to="/login" replace />}
      />
      <Route
        path="/agents"
        element={isAuthenticated ? (
          <AppLayout>
            <AgentManagement />
          </AppLayout>
        ) : <Navigate to="/login" replace />}
      />
      <Route
        path="/writing-themes"
        element={isAuthenticated ? (
          <AppLayout>
            <WritingThemeManagementPage />
          </AppLayout>
        ) : <Navigate to="/login" replace />}
      />
      <Route
        path="/writing-themes/:themeId/fields"
        element={isAuthenticated ? (
          <AppLayout>
            <ThemeFieldConfigPage />
          </AppLayout>
        ) : <Navigate to="/login" replace />}
      />
      <Route
        path="/writing-themes/:themeId/templates"
        element={isAuthenticated ? (
          <AppLayout>
            <TemplateManagementPage />
          </AppLayout>
        ) : <Navigate to="/login" replace />}
      />
      <Route
        path="/debug"
        element={isAuthenticated ? (
          <AppLayout>
            <DebugPage />
          </AppLayout>
        ) : <Navigate to="/login" replace />}
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
