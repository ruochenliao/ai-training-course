/**
 * 打字指示器组件
 * 显示AI正在思考/回复的动画效果
 */

'use client';

import React from 'react';
import {motion} from 'framer-motion';
import {Avatar} from 'antd';
import {RobotOutlined} from '@ant-design/icons';
import {useTheme} from '@/contexts/ThemeContext';

interface TypingIndicatorProps {
  className?: string;
}

export function TypingIndicator({ className = '' }: TypingIndicatorProps) {
  const { theme } = useTheme();

  // 打字动画变体
  const dotVariants = {
    initial: { y: 0 },
    animate: { y: -8 },
  };

  // 容器动画变体
  const containerVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { 
      opacity: 1, 
      y: 0,
      transition: {
        duration: 0.3,
        ease: 'easeOut'
      }
    },
    exit: { 
      opacity: 0, 
      y: -20,
      transition: {
        duration: 0.2,
        ease: 'easeIn'
      }
    }
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className={`flex items-start gap-3 max-w-[80%] ${className}`}
    >
      {/* AI头像 */}
      <div className="flex-shrink-0">
        <Avatar 
          icon={<RobotOutlined />} 
          style={{ backgroundColor: theme.colors.success }}
        />
      </div>
      
      {/* 打字气泡 */}
      <div
        className="rounded-2xl px-4 py-3 shadow-sm"
        style={{
          backgroundColor: theme.colors.assistantMessage,
          border: `1px solid ${theme.colors.outline}`
        }}
      >
        <div className="flex items-center gap-1">
          {/* 思考文本 */}
          <span 
            className="text-sm mr-2"
            style={{ color: theme.colors.onSurfaceVariant }}
          >
            AI正在思考
          </span>
          
          {/* 跳动的点 */}
          <div className="flex items-center gap-1">
            {[0, 1, 2].map((index) => (
              <motion.div
                key={index}
                variants={dotVariants}
                initial="initial"
                animate="animate"
                transition={{
                  duration: 0.6,
                  repeat: Infinity,
                  repeatType: 'reverse',
                  delay: index * 0.2,
                  ease: 'easeInOut'
                }}
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: theme.colors.primary }}
              />
            ))}
          </div>
        </div>
        
        {/* 进度条动画 */}
        <motion.div
          className="mt-2 h-1 rounded-full overflow-hidden"
          style={{ backgroundColor: theme.colors.surfaceVariant }}
        >
          <motion.div
            className="h-full rounded-full"
            style={{ backgroundColor: theme.colors.primary }}
            initial={{ width: '0%' }}
            animate={{ width: '100%' }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut'
            }}
          />
        </motion.div>
      </div>
    </motion.div>
  );
}

// 简化版打字指示器（只有点动画）
export function SimpleTypingIndicator({ className = '' }: TypingIndicatorProps) {
  const { theme } = useTheme();

  const dotVariants = {
    initial: { scale: 1, opacity: 0.3 },
    animate: { scale: 1.2, opacity: 1 },
  };

  return (
    <div className={`flex items-center gap-1 ${className}`}>
      {[0, 1, 2].map((index) => (
        <motion.div
          key={index}
          variants={dotVariants}
          initial="initial"
          animate="animate"
          transition={{
            duration: 0.8,
            repeat: Infinity,
            repeatType: 'reverse',
            delay: index * 0.3,
            ease: 'easeInOut'
          }}
          className="w-2 h-2 rounded-full"
          style={{ backgroundColor: theme.colors.onSurfaceVariant }}
        />
      ))}
    </div>
  );
}

// 脉冲式打字指示器
export function PulseTypingIndicator({ className = '' }: TypingIndicatorProps) {
  const { theme } = useTheme();

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <motion.div
        className="w-3 h-3 rounded-full"
        style={{ backgroundColor: theme.colors.primary }}
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.5, 1, 0.5]
        }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
          ease: 'easeInOut'
        }}
      />
      <span 
        className="text-sm"
        style={{ color: theme.colors.onSurfaceVariant }}
      >
        正在生成回复...
      </span>
    </div>
  );
}

// 波浪式打字指示器
export function WaveTypingIndicator({ className = '' }: TypingIndicatorProps) {
  const { theme } = useTheme();

  return (
    <div className={`flex items-center gap-1 ${className}`}>
      {[0, 1, 2, 3, 4].map((index) => (
        <motion.div
          key={index}
          className="w-1 rounded-full"
          style={{ 
            backgroundColor: theme.colors.primary,
            height: '16px'
          }}
          animate={{
            scaleY: [1, 2, 1],
            opacity: [0.3, 1, 0.3]
          }}
          transition={{
            duration: 1,
            repeat: Infinity,
            delay: index * 0.1,
            ease: 'easeInOut'
          }}
        />
      ))}
    </div>
  );
}
