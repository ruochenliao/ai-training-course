import React, { useMemo } from 'react';
import { Avatar, Button, Card, Space, Statistic } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuthStore } from '../../store/auth';
import { cn } from '../../utils';

// 模拟项目描述文本
const dummyText = '一个基于 Vue3.0、FastAPI、Naive UI 的轻量级后台管理模板';



const Workbench: React.FC = () => {
  const { t } = useTranslation();
  const { isDark, primaryColor } = useTheme();
  const { user } = useAuthStore();

  // 统计数据 - 对应Vue版本的statisticData
  const statisticData = useMemo(() => [
    {
      id: 0,
      label: t('workbench.label_number_of_items'),
      value: '25',
    },
    {
      id: 1,
      label: t('workbench.label_upcoming'),
      value: '4/16',
    },
    {
      id: 2,
      label: t('workbench.label_information'),
      value: '12',
    },
  ], [t]);

  // 用户头像 - 如果没有头像则使用默认头像
  const userAvatar = user?.avatar || 'https://api.dicebear.com/7.x/miniavs/svg?seed=1';
  const userName = user?.username || 'admin';

  return (
    <div className="workbench flex-1">
      {/* 主要卡片 - 对应Vue版本的第一个n-card */}
      <Card
        bordered={false}
        className={cn(
          "mb-4",
          isDark ? "bg-gray-800" : "bg-white"
        )}
        style={{ borderRadius: '10px' }}
      >
        <div className="flex items-center justify-between">
          {/* 左侧用户信息 */}
          <div className="flex items-center">
            <img
              src={userAvatar}
              alt="avatar"
              className="rounded-full"
              style={{ width: '60px', height: '60px' }}
            />
            <div className="ml-10">
              <p className="text-20 font-semibold">
                {t('workbench.text_hello', { username: userName })}
              </p>
              <p className="mt-5 text-14 opacity-60">
                {t('workbench.text_welcome')}
              </p>
            </div>
          </div>

          {/* 右侧统计数据 */}
          <Space size={12} wrap={false}>
            {statisticData.map(item => (
              <Statistic
                key={item.id}
                title={item.label}
                value={item.value}
                className={cn(
                  isDark ? "text-white" : "text-gray-800"
                )}
              />
            ))}
          </Space>
        </div>
      </Card>

      {/* 项目列表卡片 - 对应Vue版本的第二个n-card */}
      <Card
        title={t('workbench.label_project')}
        size="small"
        bordered={false}
        className={cn(
          "mt-15",
          isDark ? "bg-gray-800" : "bg-white"
        )}
        style={{ borderRadius: '10px' }}
        extra={
          <Button type="link" style={{ color: primaryColor }}>
            {t('workbench.label_more')}
          </Button>
        }
      >
        <div className="flex flex-wrap justify-between">
          {/* 生成9个项目卡片，对应Vue版本的v-for="i in 9" */}
          {Array.from({ length: 9 }, (_, i) => (
            <Card
              key={i + 1}
              className={cn(
                "mb-10 mt-10 w-300 cursor-pointer hover-card-shadow",
                isDark ? "bg-gray-700 border-gray-600" : "bg-white"
              )}
              title="Vue FastAPI Admin"
              size="small"
            >
              <p className="opacity-60">
                {dummyText}
              </p>
            </Card>
          ))}
        </div>
      </Card>
    </div>
  );
};

export default Workbench;