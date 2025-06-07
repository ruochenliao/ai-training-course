import React, {useCallback, useEffect, useState} from 'react'
import {Avatar, Badge, Button, Dropdown, Empty, Input, List, message, Modal, Select, Spin, Tag} from 'antd'
import {ClockCircleOutlined, ExclamationCircleOutlined, MoreOutlined, UserOutlined} from '@ant-design/icons'
import {customerServiceApi, Session, SessionPriority, SessionQueryParams, SessionStatus} from '@/api/customerService'
import {getTimeAgo} from '@/utils/time'
import './SessionList.less'

interface SessionListProps {
  selectedSessionId?: string
  onSessionSelect: (session: Session) => void
}

const { Search } = Input
const { Option } = Select

const SessionList: React.FC<SessionListProps> = ({
  selectedSessionId,
  onSessionSelect
}) => {
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(false)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [statusFilter, setStatusFilter] = useState<SessionStatus | 'all'>('all')
  const [priorityFilter, setPriorityFilter] = useState<SessionPriority | 'all'>('all')
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  })

  // 加载会话列表
  const loadSessions = useCallback(async (params?: Partial<SessionQueryParams>) => {
    try {
      setLoading(true)
      const queryParams: SessionQueryParams = {
        page: pagination.current,
        pageSize: pagination.pageSize,
        sortBy: 'updatedAt',
        sortOrder: 'desc',
        ...params
      }
      
      if (searchKeyword) {
        queryParams.keyword = searchKeyword
      }
      
      if (statusFilter !== 'all') {
        queryParams.status = statusFilter
      }
      
      if (priorityFilter !== 'all') {
        queryParams.priority = priorityFilter
      }
      
      const response = await customerServiceApi.getSessions(queryParams)
      setSessions(response.list)
      setPagination(prev => ({
        ...prev,
        total: response.pagination.total
      }))
    } catch (error) {
      message.error('加载会话列表失败')
    } finally {
      setLoading(false)
    }
  }, [pagination.current, pagination.pageSize, searchKeyword, statusFilter, priorityFilter])

  // 稳定的加载函数引用
  const stableLoadSessions = useCallback(() => {
    loadSessions()
  }, [loadSessions])

  // 搜索处理
  const handleSearch = useCallback((value: string) => {
    setSearchKeyword(value)
    setPagination(prev => ({ ...prev, current: 1 }))
  }, [])

  // 状态筛选
  const handleStatusFilter = useCallback((value: SessionStatus | 'all') => {
    setStatusFilter(value)
    setPagination(prev => ({ ...prev, current: 1 }))
  }, [])

  // 优先级筛选
  const handlePriorityFilter = useCallback((value: SessionPriority | 'all') => {
    setPriorityFilter(value)
    setPagination(prev => ({ ...prev, current: 1 }))
  }, [])

  // 分配会话
  const handleAssignSession = useCallback(async (sessionId: string) => {
    try {
      await customerServiceApi.assignSession(sessionId, 'current-agent-id') // 实际项目中应该获取当前客服ID
      message.success('会话分配成功')
      loadSessions()
    } catch (error) {
      message.error('会话分配失败')
    }
  }, [loadSessions])

  // 关闭会话
  const handleCloseSession = useCallback(async (sessionId: string) => {
    Modal.confirm({
      title: '确认关闭会话',
      content: '关闭后将无法继续对话，是否确认？',
      icon: <ExclamationCircleOutlined />,
      onOk: async () => {
        try {
          await customerServiceApi.closeSession(sessionId, {})
          message.success('会话已关闭')
          loadSessions()
        } catch (error) {
          message.error('关闭会话失败')
        }
      }
    })
  }, [loadSessions])

  // 转移会话
  const handleTransferSession = useCallback((_sessionId: string) => {
    Modal.info({
      title: '转移会话',
      content: '转移功能需要选择目标客服，请在实际项目中实现选择器组件'
    })
  }, [])

  // 获取状态颜色
  const getStatusColor = useCallback((status: SessionStatus) => {
    switch (status) {
      case SessionStatus.WAITING:
        return 'orange'
      case SessionStatus.ACTIVE:
        return 'green'
      case SessionStatus.CLOSED:
        return 'default'
      case SessionStatus.TRANSFERRED:
        return 'blue'
      default:
        return 'default'
    }
  }, [])

  // 获取优先级颜色
  const getPriorityColor = useCallback((priority: SessionPriority) => {
    switch (priority) {
      case SessionPriority.URGENT:
        return 'red'
      case SessionPriority.HIGH:
        return 'orange'
      case SessionPriority.NORMAL:
        return 'blue'
      case SessionPriority.LOW:
        return 'default'
      default:
        return 'default'
    }
  }, [])

  // 获取状态文本
  const getStatusText = useCallback((status: SessionStatus) => {
    switch (status) {
      case SessionStatus.WAITING:
        return '等待中'
      case SessionStatus.ACTIVE:
        return '进行中'
      case SessionStatus.CLOSED:
        return '已关闭'
      case SessionStatus.TRANSFERRED:
        return '已转移'
      default:
        return status
    }
  }, [])

  // 获取优先级文本
  const getPriorityText = useCallback((priority: SessionPriority) => {
    switch (priority) {
      case SessionPriority.URGENT:
        return '紧急'
      case SessionPriority.HIGH:
        return '高'
      case SessionPriority.NORMAL:
        return '普通'
      case SessionPriority.LOW:
        return '低'
      default:
        return priority
    }
  }, [])

  // 会话操作菜单
  const getSessionActions = useCallback((session: Session) => {
    const items = []
    
    if (session.status === SessionStatus.WAITING) {
      items.push({
        key: 'assign',
        label: '接受会话',
        onClick: () => handleAssignSession(session.id)
      })
    }
    
    if (session.status === SessionStatus.ACTIVE) {
      items.push(
        {
          key: 'transfer',
          label: '转移会话',
          onClick: () => handleTransferSession(session.id)
        },
        {
          key: 'close',
          label: '关闭会话',
          onClick: () => handleCloseSession(session.id)
        }
      )
    }
    
    return items
  }, [handleAssignSession, handleTransferSession, handleCloseSession])

  // 初始化加载
  useEffect(() => {
    stableLoadSessions()
  }, [stableLoadSessions])

  return (
    <div className="session-list">
      {/* 搜索和筛选 */}
      <div className="session-filters">
        <Search
          placeholder="搜索会话..."
          allowClear
          onSearch={handleSearch}
          style={{ marginBottom: 12 }}
        />
        
        <div className="filter-row">
          <Select
            value={statusFilter}
            onChange={handleStatusFilter}
            style={{ width: 100 }}
            size="small"
          >
            <Option value="all">全部状态</Option>
            <Option value={SessionStatus.WAITING}>等待中</Option>
            <Option value={SessionStatus.ACTIVE}>进行中</Option>
            <Option value={SessionStatus.CLOSED}>已关闭</Option>
            <Option value={SessionStatus.TRANSFERRED}>已转移</Option>
          </Select>
          
          <Select
            value={priorityFilter}
            onChange={handlePriorityFilter}
            style={{ width: 100 }}
            size="small"
          >
            <Option value="all">全部优先级</Option>
            <Option value={SessionPriority.URGENT}>紧急</Option>
            <Option value={SessionPriority.HIGH}>高</Option>
            <Option value={SessionPriority.NORMAL}>普通</Option>
            <Option value={SessionPriority.LOW}>低</Option>
          </Select>
        </div>
      </div>

      {/* 会话列表 */}
      <div className="session-list-content">
        <Spin spinning={loading}>
          {sessions.length === 0 ? (
            <Empty 
              description="暂无会话" 
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ) : (
            <List
              dataSource={sessions}
              renderItem={(session) => {
                const isSelected = session.id === selectedSessionId
                const actions = getSessionActions(session)
                
                return (
                  <List.Item
                    className={`session-item ${isSelected ? 'selected' : ''}`}
                    onClick={() => onSessionSelect(session)}
                    actions={[
                      actions.length > 0 && (
                        <Dropdown
                          menu={{ items: actions }}
                          trigger={['click']}
                          key="actions"
                        >
                          <Button 
                            type="text" 
                            icon={<MoreOutlined />} 
                            size="small"
                            onClick={(e) => e.stopPropagation()}
                          />
                        </Dropdown>
                      )
                    ].filter(Boolean)}
                  >
                    <List.Item.Meta
                      avatar={
                        <Badge 
                          count={session.unreadCount} 
                          size="small"
                          offset={[-5, 5]}
                        >
                          <Avatar 
                            src={session.userInfo.avatar} 
                            icon={<UserOutlined />}
                            size={40}
                          >
                            {session.userInfo.nickname?.[0]}
                          </Avatar>
                        </Badge>
                      }
                      title={
                        <div className="session-title">
                          <span className="user-name">
                            {session.userInfo.nickname || session.userInfo.username}
                          </span>
                          <div className="session-tags">
                            <Tag 
                              color={getStatusColor(session.status)}
                            >
                              {getStatusText(session.status)}
                            </Tag>
                            <Tag 
                              color={getPriorityColor(session.priority)}
                            >
                              {getPriorityText(session.priority)}
                            </Tag>
                          </div>
                        </div>
                      }
                      description={
                        <div className="session-description">
                          <div className="last-message">
                            {session.lastMessage ? (
                              <span className="message-content">
                                {session.lastMessage.type === 'text' 
                                  ? session.lastMessage.content 
                                  : `[${session.lastMessage.type}]`
                                }
                              </span>
                            ) : (
                              <span className="no-message">暂无消息</span>
                            )}
                          </div>
                          
                          <div className="session-meta">
                            <span className="time">
                              <ClockCircleOutlined />
                              {getTimeAgo(session.updatedAt)}
                            </span>
                            
                            {session.waitingTime && session.waitingTime > 0 && (
                              <span className="waiting-time">
                                等待 {Math.floor(session.waitingTime / 60)}分钟
                              </span>
                            )}
                            
                            <span className="source">
                              来源: {session.source}
                            </span>
                          </div>
                        </div>
                      }
                    />
                  </List.Item>
                )
              }}
            />
          )}
        </Spin>
      </div>

      {/* 分页 */}
      {pagination.total > pagination.pageSize && (
        <div className="session-pagination">
          <Button
            size="small"
            disabled={pagination.current === 1}
            onClick={() => {
              setPagination(prev => ({ ...prev, current: prev.current - 1 }))
            }}
          >
            上一页
          </Button>
          
          <span className="pagination-info">
            {pagination.current} / {Math.ceil(pagination.total / pagination.pageSize)}
          </span>
          
          <Button
            size="small"
            disabled={pagination.current >= Math.ceil(pagination.total / pagination.pageSize)}
            onClick={() => {
              setPagination(prev => ({ ...prev, current: prev.current + 1 }))
            }}
          >
            下一页
          </Button>
        </div>
      )}
    </div>
  )
}

export default SessionList