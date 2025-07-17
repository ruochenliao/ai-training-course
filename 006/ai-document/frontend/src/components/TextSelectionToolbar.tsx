import React, { useState, useEffect, useRef } from 'react';
import { Button, Tooltip, Space } from 'antd';
import {
  EditOutlined,
  BulbOutlined,
  ExpandAltOutlined,
  CompressOutlined,
  TranslationOutlined,
  CheckOutlined,
  FormatPainterOutlined
} from '@ant-design/icons';
import './TextSelectionToolbar.css';

interface TextSelectionToolbarProps {
  visible: boolean;
  position: { x: number; y: number };
  selectedText: string;
  onAIWriting: () => void;
  onPolish: () => void;
  onExpand: () => void;
  onSummarize: () => void;
  onTranslate: () => void;
  onFormat: () => void;
  onClose: () => void;
}

const TextSelectionToolbar: React.FC<TextSelectionToolbarProps> = ({
  visible,
  position,
  selectedText,
  onAIWriting,
  onPolish,
  onExpand,
  onSummarize,
  onTranslate,
  onFormat,
  onClose
}) => {
  const toolbarRef = useRef<HTMLDivElement>(null);
  const [adjustedPosition, setAdjustedPosition] = useState(position);

  // 调整工具栏位置，确保不超出视窗
  useEffect(() => {
    if (visible && toolbarRef.current) {
      const toolbar = toolbarRef.current;
      const rect = toolbar.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;

      let newX = position.x;
      let newY = position.y;

      // 水平位置调整
      if (newX + rect.width > viewportWidth) {
        newX = viewportWidth - rect.width - 10;
      }
      if (newX < 10) {
        newX = 10;
      }

      // 垂直位置调整
      if (newY + rect.height > viewportHeight) {
        newY = position.y - rect.height - 10; // 显示在选中文本上方
      }
      if (newY < 10) {
        newY = 10;
      }

      setAdjustedPosition({ x: newX, y: newY });
    }
  }, [visible, position]);

  // 点击外部关闭工具栏
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (toolbarRef.current && !toolbarRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (visible) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [visible, onClose]);

  if (!visible || !selectedText) {
    return null;
  }

  return (
    <div
      ref={toolbarRef}
      className="text-selection-toolbar"
      style={{
        position: 'fixed',
        left: adjustedPosition.x,
        top: adjustedPosition.y,
        zIndex: 1000
      }}
    >
      <div className="toolbar-content">
        <Space size="small">
          <Tooltip title="AI写作" placement="top">
            <Button
              type="primary"
              size="small"
              icon={<EditOutlined />}
              onClick={onAIWriting}
              className="ai-writing-btn"
            >
              AI写作
            </Button>
          </Tooltip>

          <Tooltip title="AI润色" placement="top">
            <Button
              size="small"
              icon={<BulbOutlined />}
              onClick={onPolish}
              className="toolbar-btn"
            >
              润色
            </Button>
          </Tooltip>

          <Tooltip title="AI扩写" placement="top">
            <Button
              size="small"
              icon={<ExpandAltOutlined />}
              onClick={onExpand}
              className="toolbar-btn"
            >
              扩写
            </Button>
          </Tooltip>

          <Tooltip title="AI总结" placement="top">
            <Button
              size="small"
              icon={<CompressOutlined />}
              onClick={onSummarize}
              className="toolbar-btn"
            >
              总结
            </Button>
          </Tooltip>

          <Tooltip title="AI翻译" placement="top">
            <Button
              size="small"
              icon={<TranslationOutlined />}
              onClick={onTranslate}
              className="toolbar-btn"
            >
              翻译
            </Button>
          </Tooltip>

          <Tooltip title="格式化" placement="top">
            <Button
              size="small"
              icon={<FormatPainterOutlined />}
              onClick={onFormat}
              className="toolbar-btn"
            >
              格式化
            </Button>
          </Tooltip>
        </Space>

        {/* 选中文本预览 */}
        <div className="selected-text-preview">
          <span className="preview-label">已选择:</span>
          <span className="preview-text">
            {selectedText.length > 30 
              ? `${selectedText.substring(0, 30)}...` 
              : selectedText
            }
          </span>
          <span className="text-length">({selectedText.length}字)</span>
        </div>
      </div>

      {/* 工具栏箭头指示器 */}
      <div className="toolbar-arrow" />
    </div>
  );
};

export default TextSelectionToolbar;
