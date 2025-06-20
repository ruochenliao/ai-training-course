import React, { useState, useEffect } from 'react'
import { Card, Button, Space, Typography, Tag, Tooltip, Badge } from 'antd'
import {
  BulbOutlined,
  ThunderboltOutlined,
  StarOutlined,
  HeartOutlined,
  RocketOutlined,
  FireOutlined,
  CrownOutlined,
  GiftOutlined,
  TrophyOutlined,
  MagicWandOutlined
} from '@ant-design/icons'

const { Text, Title } = Typography

interface Suggestion {
  id: string
  text: string
  category: 'quick' | 'smart' | 'trending' | 'personalized'
  icon?: React.ReactNode
  color?: string
  priority?: number
  tags?: string[]
  description?: string
}

interface SmartSuggestionsProps {
  suggestions?: Suggestion[]
  onSuggestionClick: (suggestion: Suggestion) => void
  userContext?: {
    recentTopics?: string[]
    preferences?: string[]
    conversationHistory?: any[]
  }
  className?: string
}

/**
 * 智能建议组件
 * 基于用户上下文和对话历史提供智能建议
 * 支持多种建议类型和个性化推荐
 */
const SmartSuggestions: React.FC<SmartSuggestionsProps> = ({
  suggestions: propSuggestions,
  onSuggestionClick,
  userContext,
  className
}) => {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [activeCategory, setActiveCategory] = useState<string>('all')

  // 默认建议配置
  const defaultSuggestions: Suggestion[] = [
    {
      id: '1',
      text: '✨ 帮我解决技术问题',
      category: 'quick',
      icon: <ThunderboltOutlined />,
      color: '#667eea',
      priority: 1,
      tags: ['技术支持', '问题解决'],
      description: '获取专业的技术支持和解决方案'
    },
    {
      id: '2',
      text: '🎯 产品功能咨询',
      category: 'quick',
      icon: <BulbOutlined />,
      color: '#f093fb',
      priority: 2,
      tags: ['产品咨询', '功能介绍'],
      description: '了解产品特性和使用方法'
    },
    {
      id: '3',
      text: '💡 创意建议和灵感',
      category: 'smart',
      icon: <StarOutlined />,
      color: '#ffeaa7',
      priority: 3,
      tags: ['创意', '灵感'],
      description: '获取创新想法和建议'
    },
    {
      id: '4',
      text: '❤️ 客户服务支持',
      category: 'quick',
      icon: <HeartOutlined />,
      color: '#fd79a8',
      priority: 4,
      tags: ['客户服务', '售后支持'],
      description: '专业的客户服务和售后支持'
    },
    {
      id: '5',
      text: '🚀 性能优化建议',
      category: 'smart',
      icon: <RocketOutlined />,
      color: '#00b894',
      priority: 5,
      tags: ['性能优化', '系统提升'],
      description: '系统性能分析和优化建议'
    },
    {
      id: '6',
      text: '🔥 热门功能推荐',
      category: 'trending',
      icon: <FireOutlined />,
      color: '#e17055',
      priority: 6,
      tags: ['热门', '推荐'],
      description: '最受欢迎的功能和特性'
    },
    {
      id: '7',
      text: '👑 VIP专属服务',
      category: 'personalized',
      icon: <CrownOutlined />,
      color: '#fdcb6e',
      priority: 7,
      tags: ['VIP', '专属'],
      description: '专为VIP用户提供的高级服务'
    },
    {
      id: '8',
      text: '🎁 优惠活动信息',
      category: 'trending',
      icon: <GiftOutlined />,
      color: '#a29bfe',
      priority: 8,
      tags: ['优惠', '活动'],
      description: '最新的优惠活动和促销信息'
    }
  ]

  // 智能建议生成
  const generateSmartSuggestions = () => {
    let baseSuggestions = propSuggestions || defaultSuggestions
    
    // 基于用户上下文调整建议
    if (userContext) {
      const { recentTopics, preferences, conversationHistory } = userContext
      
      // 根据最近话题调整优先级
      if (recentTopics && recentTopics.length > 0) {
        baseSuggestions = baseSuggestions.map(suggestion => {
          const relevanceScore = recentTopics.some(topic => 
            suggestion.tags?.some(tag => tag.includes(topic)) ||
            suggestion.text.includes(topic)
          ) ? 10 : 0
          
          return {
            ...suggestion,
            priority: (suggestion.priority || 0) + relevanceScore
          }
        })
      }
      
      // 根据用户偏好添加个性化建议
      if (preferences && preferences.length > 0) {
        const personalizedSuggestions: Suggestion[] = preferences.map((pref, index) => ({
          id: `personalized_${index}`,
          text: `🎯 ${pref}相关建议`,
          category: 'personalized',
          icon: <MagicWandOutlined />,
          color: '#6c5ce7',
          priority: 100 + index,
          tags: [pref, '个性化'],
          description: `基于您的偏好：${pref}`
        }))
        
        baseSuggestions = [...baseSuggestions, ...personalizedSuggestions]
      }
    }
    
    // 按优先级排序
    baseSuggestions.sort((a, b) => (b.priority || 0) - (a.priority || 0))
    
    setSuggestions(baseSuggestions)
  }

  useEffect(() => {
    generateSmartSuggestions()
  }, [propSuggestions, userContext])

  // 获取分类图标
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'quick': return <ThunderboltOutlined />
      case 'smart': return <BulbOutlined />
      case 'trending': return <FireOutlined />
      case 'personalized': return <StarOutlined />
      default: return <BulbOutlined />
    }
  }

  // 获取分类颜色
  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'quick': return '#667eea'
      case 'smart': return '#f093fb'
      case 'trending': return '#e17055'
      case 'personalized': return '#6c5ce7'
      default: return '#667eea'
    }
  }

  // 过滤建议
  const filteredSuggestions = activeCategory === 'all' 
    ? suggestions 
    : suggestions.filter(s => s.category === activeCategory)

  // 分类统计
  const categoryStats = {
    all: suggestions.length,
    quick: suggestions.filter(s => s.category === 'quick').length,
    smart: suggestions.filter(s => s.category === 'smart').length,
    trending: suggestions.filter(s => s.category === 'trending').length,
    personalized: suggestions.filter(s => s.category === 'personalized').length
  }

  return (
    <div className={`smart-suggestions ${className || ''}`}>
      {/* 分类筛选 */}
      <div className="category-filters" style={{ marginBottom: '20px' }}>
        <Space wrap>
          {[
            { key: 'all', label: '全部', icon: <TrophyOutlined /> },
            { key: 'quick', label: '快捷', icon: <ThunderboltOutlined /> },
            { key: 'smart', label: '智能', icon: <BulbOutlined /> },
            { key: 'trending', label: '热门', icon: <FireOutlined /> },
            { key: 'personalized', label: '个性化', icon: <StarOutlined /> }
          ].map(category => (
            <Badge 
              key={category.key} 
              count={categoryStats[category.key as keyof typeof categoryStats]} 
              size="small"
              style={{ backgroundColor: getCategoryColor(category.key) }}
            >
              <Button
                type={activeCategory === category.key ? 'primary' : 'default'}
                icon={category.icon}
                onClick={() => setActiveCategory(category.key)}
                style={{
                  borderRadius: '20px',
                  background: activeCategory === category.key 
                    ? `linear-gradient(135deg, ${getCategoryColor(category.key)} 0%, ${getCategoryColor(category.key)}aa 100%)`
                    : 'rgba(255, 255, 255, 0.1)',
                  backdropFilter: 'blur(20px)',
                  border: `1px solid ${activeCategory === category.key ? 'transparent' : 'rgba(255, 255, 255, 0.2)'}`,
                  color: activeCategory === category.key ? 'white' : 'rgba(255, 255, 255, 0.8)'
                }}
              >
                {category.label}
              </Button>
            </Badge>
          ))}
        </Space>
      </div>

      {/* 建议列表 */}
      <div className="suggestions-grid" style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', 
        gap: '16px' 
      }}>
        {filteredSuggestions.slice(0, 8).map((suggestion) => (
          <Card
            key={suggestion.id}
            size="small"
            hoverable
            className="suggestion-card"
            style={{
              background: 'rgba(255, 255, 255, 0.1)',
              backdropFilter: 'blur(20px)',
              border: `1px solid ${suggestion.color}33`,
              borderRadius: '16px',
              cursor: 'pointer',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              position: 'relative',
              overflow: 'hidden'
            }}
            onClick={() => onSuggestionClick(suggestion)}
            onMouseEnter={(e) => {
              const card = e.currentTarget
              card.style.transform = 'translateY(-4px) scale(1.02)'
              card.style.boxShadow = `0 12px 32px ${suggestion.color}40`
              card.style.borderColor = `${suggestion.color}66`
            }}
            onMouseLeave={(e) => {
              const card = e.currentTarget
              card.style.transform = 'translateY(0) scale(1)'
              card.style.boxShadow = 'none'
              card.style.borderColor = `${suggestion.color}33`
            }}
          >
            {/* 背景装饰 */}
            <div 
              style={{
                position: 'absolute',
                top: 0,
                right: 0,
                width: '60px',
                height: '60px',
                background: `linear-gradient(135deg, ${suggestion.color}20, transparent)`,
                borderRadius: '0 16px 0 60px'
              }}
            />
            
            <div style={{ position: 'relative', zIndex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', marginBottom: '12px' }}>
                <div 
                  style={{ 
                    fontSize: '24px', 
                    color: suggestion.color,
                    marginRight: '12px',
                    flexShrink: 0
                  }}
                >
                  {suggestion.icon}
                </div>
                <div style={{ flex: 1 }}>
                  <Text 
                    strong 
                    style={{ 
                      color: 'rgba(255, 255, 255, 0.9)', 
                      fontSize: '16px',
                      display: 'block',
                      marginBottom: '4px'
                    }}
                  >
                    {suggestion.text}
                  </Text>
                  {suggestion.description && (
                    <Text 
                      style={{ 
                        color: 'rgba(255, 255, 255, 0.6)', 
                        fontSize: '12px',
                        lineHeight: '1.4'
                      }}
                    >
                      {suggestion.description}
                    </Text>
                  )}
                </div>
              </div>
              
              {/* 标签 */}
              {suggestion.tags && suggestion.tags.length > 0 && (
                <div style={{ marginTop: '8px' }}>
                  <Space size={4} wrap>
                    {suggestion.tags.slice(0, 3).map((tag, index) => (
                      <Tag 
                        key={index}
                        size="small"
                        style={{
                          background: `${suggestion.color}20`,
                          border: `1px solid ${suggestion.color}40`,
                          color: suggestion.color,
                          borderRadius: '8px',
                          fontSize: '10px'
                        }}
                      >
                        {tag}
                      </Tag>
                    ))}
                  </Space>
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>

      {/* 空状态 */}
      {filteredSuggestions.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px', color: 'rgba(255, 255, 255, 0.6)' }}>
          <BulbOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
          <Text style={{ color: 'rgba(255, 255, 255, 0.6)' }}>
            暂无相关建议
          </Text>
        </div>
      )}
    </div>
  )
}

export default SmartSuggestions
