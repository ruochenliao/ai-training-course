import React from 'react';
import * as AntdIcons from '@ant-design/icons';
import { cn } from '../../utils';

interface CustomIconProps {
  icon?: string; // 图标名称
  size?: number | string; // 图标大小
  color?: string; // 图标颜色
  className?: string;
  style?: React.CSSProperties;
  onClick?: () => void;
}

/**
 * 自定义图标组件
 * 对应Vue版本的CustomIcon.vue
 */
const CustomIcon: React.FC<CustomIconProps> = ({
  icon,
  size = 16,
  color,
  className,
  style,
  onClick,
}) => {
  if (!icon) {
    return null;
  }

  // 动态获取Ant Design图标组件
  const IconComponent = (AntdIcons as any)[icon];
  
  if (!IconComponent) {
    console.warn(`Icon "${icon}" not found in Ant Design icons`);
    return null;
  }

  const iconStyle: React.CSSProperties = {
    fontSize: typeof size === 'number' ? `${size}px` : size,
    color,
    cursor: onClick ? 'pointer' : 'default',
    ...style,
  };

  return (
    <IconComponent
      className={cn(className)}
      style={iconStyle}
      onClick={onClick}
    />
  );
};

export default CustomIcon;
