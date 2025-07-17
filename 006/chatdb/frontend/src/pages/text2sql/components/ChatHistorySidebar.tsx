import React from 'react';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { ChatHistory, ChatHistorySidebarProps } from '../../../types/chat';

const ChatHistorySidebar: React.FC<ChatHistorySidebarProps> = ({
  histories,
  selectedHistoryId,
  onSelectHistory,
  onDeleteHistory,
  onNewChat,
  collapsed,
  onToggleCollapse
}) => {
  const formatTime = (timestamp: Date) => {
    return formatDistanceToNow(timestamp, {
      addSuffix: true,
      locale: zhCN
    });
  };

  const truncateText = (text: string, maxLength: number = 30) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <div className={`chat-history-sidebar ${collapsed ? 'collapsed' : ''}`}>
      {/* 侧边栏头部 */}
      <div className="sidebar-header">
        <div className="header-content">
          {!collapsed && (
            <>
              <h3 className="sidebar-title">
                <span className="title-icon">💬</span>
                聊天历史
              </h3>
              <button
                className="new-chat-btn"
                onClick={onNewChat}
                title="新建对话"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 5v14M5 12h14"/>
                </svg>
              </button>
            </>
          )}
        </div>
        <button
          className="collapse-btn"
          onClick={onToggleCollapse}
          title={collapsed ? "展开侧边栏" : "收起侧边栏"}
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className={collapsed ? 'rotate-180' : ''}
          >
            <path d="M15 18l-6-6 6-6"/>
          </svg>
        </button>
      </div>

      {/* 历史记录列表 */}
      {!collapsed && (
        <div className="history-list">
          {histories.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📝</div>
              <p className="empty-text">暂无聊天记录</p>
              <p className="empty-hint">开始您的第一次对话吧</p>
            </div>
          ) : (
            histories.map((history) => (
              <div
                key={history.id}
                className={`history-item ${selectedHistoryId === history.id ? 'selected' : ''}`}
              >
                <div
                  className="history-content"
                  onClick={() => onSelectHistory(history.id)}
                >
                  <div className="history-title">
                    {truncateText(history.title || history.query)}
                  </div>
                  <div className="history-meta">
                    <span className="history-time">
                      {formatTime(history.timestamp)}
                    </span>
                    <div className="history-tags">
                      {history.response.sql && (
                        <span className="tag sql-tag">SQL</span>
                      )}
                      {history.response.data && history.response.data.length > 0 && (
                        <span className="tag data-tag">数据</span>
                      )}
                      {history.response.visualization && (
                        <span className="tag viz-tag">图表</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* 删除按钮 - 悬停时显示 */}
                <div className="history-actions">
                  <button
                    className="delete-button"
                    onClick={(e) => {
                      e.stopPropagation(); // 阻止事件冒泡
                      onDeleteHistory(history.id);
                    }}
                    title="删除对话"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="3,6 5,6 21,6"></polyline>
                      <path d="m19,6v14a2,2 0 0,1 -2,2H7a2,2 0 0,1 -2,-2V6m3,0V4a2,2 0 0,1 2,-2h4a2,2 0 0,1 2,2v2"></path>
                      <line x1="10" y1="11" x2="10" y2="17"></line>
                      <line x1="14" y1="11" x2="14" y2="17"></line>
                    </svg>
                  </button>
                </div>

                <div className="history-indicator">
                  <div className="indicator-dot"></div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* 收起状态下的快捷操作 */}
      {collapsed && (
        <div className="collapsed-actions">
          <button
            className="collapsed-new-chat"
            onClick={onNewChat}
            title="新建对话"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14"/>
            </svg>
          </button>
          <div className="collapsed-count">
            {histories.length}
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatHistorySidebar;
