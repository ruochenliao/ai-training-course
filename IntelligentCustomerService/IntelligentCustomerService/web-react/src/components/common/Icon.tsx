import React from 'react';
import * as AntdIcons from '@ant-design/icons';
import { IconProps } from '@ant-design/icons/lib/components/Icon';

interface CustomIconProps extends Omit<IconProps, 'component'> {
  name: string;
  size?: number | string;
}

const Icon: React.FC<CustomIconProps> = ({ name, size, style, ...props }) => {
  // 动态获取图标组件
  const IconComponent = (AntdIcons as any)[name];
  
  if (!IconComponent) {
    console.warn(`Icon "${name}" not found in @ant-design/icons`);
    return <AntdIcons.QuestionCircleOutlined {...props} style={{ fontSize: size, ...style }} />;
  }

  return (
    <IconComponent
      {...props}
      style={{
        fontSize: size,
        ...style,
      }}
    />
  );
};

export default Icon;

// 常用图标名称导出
export const IconNames = {
  // 导航图标
  DASHBOARD: 'DashboardOutlined',
  USER: 'UserOutlined',
  TEAM: 'TeamOutlined',
  SETTING: 'SettingOutlined',
  MENU: 'MenuOutlined',
  HOME: 'HomeOutlined',
  
  // 操作图标
  EDIT: 'EditOutlined',
  DELETE: 'DeleteOutlined',
  ADD: 'PlusOutlined',
  SEARCH: 'SearchOutlined',
  REFRESH: 'ReloadOutlined',
  SAVE: 'SaveOutlined',
  CANCEL: 'CloseOutlined',
  
  // 状态图标
  SUCCESS: 'CheckCircleOutlined',
  ERROR: 'CloseCircleOutlined',
  WARNING: 'ExclamationCircleOutlined',
  INFO: 'InfoCircleOutlined',
  LOADING: 'LoadingOutlined',
  
  // 文件图标
  FILE: 'FileOutlined',
  FOLDER: 'FolderOutlined',
  DOWNLOAD: 'DownloadOutlined',
  UPLOAD: 'UploadOutlined',
  
  // 其他图标
  EYE: 'EyeOutlined',
  EYE_INVISIBLE: 'EyeInvisibleOutlined',
  LOCK: 'LockOutlined',
  UNLOCK: 'UnlockOutlined',
  HEART: 'HeartOutlined',
  STAR: 'StarOutlined',
  LIKE: 'LikeOutlined',
  DISLIKE: 'DislikeOutlined',
  SHARE: 'ShareAltOutlined',
  COPY: 'CopyOutlined',
  LINK: 'LinkOutlined',
  MAIL: 'MailOutlined',
  PHONE: 'PhoneOutlined',
  CALENDAR: 'CalendarOutlined',
  CLOCK: 'ClockCircleOutlined',
  LOCATION: 'EnvironmentOutlined',
  CAMERA: 'CameraOutlined',
  PICTURE: 'PictureOutlined',
  VIDEO: 'VideoCameraOutlined',
  SOUND: 'SoundOutlined',
  NOTIFICATION: 'BellOutlined',
  MESSAGE: 'MessageOutlined',
  COMMENT: 'CommentOutlined',
  QUESTION: 'QuestionCircleOutlined',
  HELP: 'QuestionOutlined',
  FILTER: 'FilterOutlined',
  SORT: 'SortAscendingOutlined',
  EXPORT: 'ExportOutlined',
  IMPORT: 'ImportOutlined',
  PRINT: 'PrinterOutlined',
  FULLSCREEN: 'FullscreenOutlined',
  COMPRESS: 'CompressOutlined',
  EXPAND: 'ExpandOutlined',
  LEFT: 'LeftOutlined',
  RIGHT: 'RightOutlined',
  UP: 'UpOutlined',
  DOWN: 'DownOutlined',
  DOUBLE_LEFT: 'DoubleLeftOutlined',
  DOUBLE_RIGHT: 'DoubleRightOutlined',
  CARET_UP: 'CaretUpOutlined',
  CARET_DOWN: 'CaretDownOutlined',
  CARET_LEFT: 'CaretLeftOutlined',
  CARET_RIGHT: 'CaretRightOutlined',
} as const;

export type IconName = typeof IconNames[keyof typeof IconNames];