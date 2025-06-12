import React, { useState, useMemo } from 'react';
import { Modal, Input, Row, Col, Button, Tooltip, Empty } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import * as AntdIcons from '@ant-design/icons';
import { useTheme } from '../../contexts/ThemeContext';
import { cn } from '../../utils';
import CustomIcon from './CustomIcon';

interface IconPickerProps {
  value?: string;
  onChange?: (iconName: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

/**
 * 图标选择器组件
 * 对应Vue版本的IconPicker.vue
 */
const IconPicker: React.FC<IconPickerProps> = ({
  value,
  onChange,
  placeholder = '请选择图标',
  disabled = false,
}) => {
  const { isDark } = useTheme();
  const [visible, setVisible] = useState(false);
  const [searchText, setSearchText] = useState('');

  // 获取所有Ant Design图标
  const allIcons = useMemo(() => {
    return Object.keys(AntdIcons)
      .filter(key => 
        key !== 'default' && 
        key !== 'createFromIconfontCN' && 
        key !== 'IconProvider' &&
        typeof (AntdIcons as any)[key] === 'object'
      )
      .sort();
  }, []);

  // 过滤图标
  const filteredIcons = useMemo(() => {
    if (!searchText) return allIcons;
    return allIcons.filter(iconName =>
      iconName.toLowerCase().includes(searchText.toLowerCase())
    );
  }, [allIcons, searchText]);

  // 选择图标
  const handleSelectIcon = (iconName: string) => {
    onChange?.(iconName);
    setVisible(false);
    setSearchText('');
  };

  // 清除选择
  const handleClear = () => {
    onChange?.('');
  };

  return (
    <>
      {/* 触发器 */}
      <div
        className={cn(
          "flex items-center justify-between border rounded px-3 py-2 cursor-pointer transition-colors",
          disabled ? "bg-gray-100 cursor-not-allowed" : "hover:border-blue-400",
          isDark ? "border-gray-600 bg-gray-700" : "border-gray-300 bg-white"
        )}
        onClick={() => !disabled && setVisible(true)}
      >
        <div className="flex items-center gap-2">
          {value ? (
            <>
              <CustomIcon icon={value} size={16} />
              <span className={cn(
                "text-sm",
                isDark ? "text-white" : "text-gray-800"
              )}>
                {value}
              </span>
            </>
          ) : (
            <span className={cn(
              "text-sm",
              isDark ? "text-gray-400" : "text-gray-400"
            )}>
              {placeholder}
            </span>
          )}
        </div>
        
        {value && !disabled && (
          <Button
            type="text"
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              handleClear();
            }}
          >
            ×
          </Button>
        )}
      </div>

      {/* 图标选择模态框 */}
      <Modal
        title="选择图标"
        open={visible}
        onCancel={() => setVisible(false)}
        footer={null}
        width={800}
        className={cn(isDark ? "dark-modal" : "")}
      >
        <div className="space-y-4">
          {/* 搜索框 */}
          <Input
            placeholder="搜索图标..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            allowClear
          />

          {/* 图标网格 */}
          <div 
            className="max-h-96 overflow-y-auto"
            style={{ maxHeight: '400px' }}
          >
            {filteredIcons.length > 0 ? (
              <Row gutter={[8, 8]}>
                {filteredIcons.map((iconName) => (
                  <Col span={3} key={iconName}>
                    <Tooltip title={iconName}>
                      <div
                        className={cn(
                          "flex flex-col items-center justify-center p-3 rounded cursor-pointer transition-colors",
                          "hover:bg-blue-50 hover:border-blue-300",
                          value === iconName ? "bg-blue-100 border-blue-400" : "border border-gray-200",
                          isDark ? "hover:bg-gray-600 border-gray-600" : ""
                        )}
                        onClick={() => handleSelectIcon(iconName)}
                      >
                        <CustomIcon icon={iconName} size={20} />
                        <span className={cn(
                          "text-xs mt-1 text-center truncate w-full",
                          isDark ? "text-gray-300" : "text-gray-600"
                        )}>
                          {iconName}
                        </span>
                      </div>
                    </Tooltip>
                  </Col>
                ))}
              </Row>
            ) : (
              <Empty description="未找到匹配的图标" />
            )}
          </div>
        </div>
      </Modal>
    </>
  );
};

export default IconPicker;
