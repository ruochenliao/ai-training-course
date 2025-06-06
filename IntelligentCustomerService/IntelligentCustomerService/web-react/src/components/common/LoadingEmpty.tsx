import React from 'react';
import {Button, Empty, Result, Spin} from 'antd';
import {LoadingOutlined, ReloadOutlined} from '@ant-design/icons';
import {useTranslation} from 'react-i18next';

// Loading 组件
export interface LoadingProps {
  spinning?: boolean;
  size?: 'small' | 'default' | 'large';
  tip?: string;
  children?: React.ReactNode;
  indicator?: React.ReactNode;
  style?: React.CSSProperties;
  className?: string;
}

export const Loading: React.FC<LoadingProps> = ({
  spinning = true,
  size = 'default',
  tip,
  children,
  indicator,
  style,
  className,
}) => {
  const { t } = useTranslation();
  
  const defaultIndicator = <LoadingOutlined style={{ fontSize: 24 }} spin />;
  
  if (children) {
    return (
      <Spin
        spinning={spinning}
        size={size}
        tip={tip || t('loading')}
        indicator={indicator || defaultIndicator}
        style={style}
        className={className}
      >
        {children}
      </Spin>
    );
  }

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '200px',
        ...style,
      }}
      className={className}
    >
      <Spin
        spinning={spinning}
        size={size}
        tip={tip || t('loading')}
        indicator={indicator || defaultIndicator}
      >
        <div style={{ width: '100%', height: '100%', minHeight: '50px' }} />
      </Spin>
    </div>
  );
};

// Empty 组件
export interface EmptyStateProps {
  image?: React.ReactNode;
  imageStyle?: React.CSSProperties;
  description?: React.ReactNode;
  children?: React.ReactNode;
  style?: React.CSSProperties;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  image,
  imageStyle,
  description,
  children,
  style,
  className,
}) => {
  const { t } = useTranslation();
  
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '200px',
        ...style,
      }}
      className={className}
    >
      <Empty
        image={image}
        imageStyle={imageStyle}
        description={description || t('noData')}
      >
        {children}
      </Empty>
    </div>
  );
};

// Error 组件
export interface ErrorStateProps {
  title?: string;
  subTitle?: string;
  extra?: React.ReactNode;
  onRetry?: () => void;
  retryText?: string;
  style?: React.CSSProperties;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title,
  subTitle,
  extra,
  onRetry,
  retryText,
  style,
  className,
}) => {
  const { t } = useTranslation();
  
  const defaultExtra = onRetry ? (
    <Button
      type="primary"
      icon={<ReloadOutlined />}
      onClick={onRetry}
    >
      {retryText || t('retry')}
    </Button>
  ) : undefined;
  
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '300px',
        ...style,
      }}
      className={className}
    >
      <Result
        status="error"
        title={title || t('common.error')}
        subTitle={subTitle || t('common.errorMessage')}
        extra={extra || defaultExtra}
      />
    </div>
  );
};

// 组合组件：根据状态自动显示不同内容
export interface StateWrapperProps {
  loading?: boolean;
  error?: boolean | string;
  empty?: boolean;
  data?: any[] | any;
  children: React.ReactNode;
  loadingProps?: LoadingProps;
  emptyProps?: EmptyStateProps;
  errorProps?: ErrorStateProps;
  onRetry?: () => void;
}

export const StateWrapper: React.FC<StateWrapperProps> = ({
  loading = false,
  error = false,
  empty = false,
  data,
  children,
  loadingProps,
  emptyProps,
  errorProps,
  onRetry,
}) => {
  const { t } = useTranslation();
  
  // 自动判断空状态
  const isEmpty = empty || 
    (Array.isArray(data) && data.length === 0) ||
    (data && typeof data === 'object' && Object.keys(data).length === 0) ||
    (!data && !loading && !error);
  
  if (loading) {
    return <Loading {...loadingProps} />;
  }
  
  if (error) {
    const errorMessage = typeof error === 'string' ? error : undefined;
    return (
      <ErrorState
        {...errorProps}
        subTitle={errorMessage || errorProps?.subTitle}
        onRetry={onRetry || errorProps?.onRetry}
      />
    );
  }
  
  if (isEmpty) {
    return <EmptyState {...emptyProps} />;
  }
  
  return <>{children}</>;
};

// 页面级别的加载组件
export interface PageLoadingProps {
  tip?: string;
  size?: 'small' | 'default' | 'large';
}

export const PageLoading: React.FC<PageLoadingProps> = ({ tip, size = 'large' }) => {
  const { t } = useTranslation();
  
  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        background: 'rgba(255, 255, 255, 0.8)',
        zIndex: 9999,
      }}
    >
      <Spin
        size={size}
        tip={tip || t('loading')}
        indicator={<LoadingOutlined style={{ fontSize: 48 }} spin />}
      />
    </div>
  );
};

// 导出所有组件
export default {
  Loading,
  EmptyState,
  ErrorState,
  StateWrapper,
  PageLoading,
};

// 导出类型
export type {
  LoadingProps,
  EmptyStateProps,
  ErrorStateProps,
  StateWrapperProps,
  PageLoadingProps,
};