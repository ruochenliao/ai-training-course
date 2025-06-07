import React from 'react';
import {Avatar, Button, Card, Space, Statistic, Typography} from 'antd';
import {useTranslation} from 'react-i18next';

const { Title, Text } = Typography;

// 模拟用户数据
const mockUser = {
  name: '管理员',
  avatar: 'https://api.dicebear.com/7.x/miniavs/svg?seed=1'
};

// 模拟项目数据
const dummyText = '一个基于 Vue3.0、FastAPI、Naive UI 的轻量级后台管理模板';

const Workbench: React.FC = () => {
  const { t } = useTranslation();

  // 统计数据
  const statisticData = [
    {
      id: 0,
      title: '项目数量',
      value: 25,
    },
    {
      id: 1,
      title: '待办事项',
      value: '4/16',
    },
    {
      id: 2,
      title: '消息通知',
      value: 12,
    },
  ];

  return (
    <div style={{ flex: 1, padding: '24px' }}>
      {/* 顶部用户信息和统计卡片 */}
      <Card 
        style={{ 
          borderRadius: '10px',
          marginBottom: '15px'
        }}
      >
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between' 
        }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Avatar 
              size={60} 
              src={mockUser.avatar}
              style={{ borderRadius: '50%' }}
            />
            <div style={{ marginLeft: '40px' }}>
              <Text 
                style={{ 
                  fontSize: '20px', 
                  fontWeight: 600,
                  display: 'block'
                }}
              >
                你好，{mockUser.name}！
              </Text>
              <Text 
                style={{ 
                  marginTop: '5px',
                  fontSize: '14px',
                  opacity: 0.6,
                  display: 'block'
                }}
              >
                欢迎回来，祝你开心每一天！
              </Text>
            </div>
          </div>
          <Space size={12}>
            {statisticData.map((item) => (
              <Statistic
                key={item.id}
                title={item.title}
                value={item.value}
              />
            ))}
          </Space>
        </div>
      </Card>

      {/* 项目列表卡片 */}
      <Card
        title="项目"
        size="small"
        style={{
          marginTop: '15px',
          borderRadius: '10px'
        }}
        extra={
          <Button type="link">
            更多
          </Button>
        }
      >
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          gap: '16px'
        }}>
          {Array.from({ length: 9 }, (_, i) => (
            <Card
              key={i}
              title="Vue FastAPI Admin"
              size="small"
              style={{
                width: '300px',
                marginBottom: '10px',
                marginTop: '10px',
                cursor: 'pointer',
                transition: 'box-shadow 0.3s'
              }}
              className="hover:shadow-lg"
            >
              <Text style={{ opacity: 0.6 }}>
                {dummyText}
              </Text>
            </Card>
          ))}
        </div>
      </Card>
    </div>
  );
};

export default Workbench;