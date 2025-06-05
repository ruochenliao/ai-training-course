import React, { useState, useRef } from 'react';
import {
  Card,
  Button,
  Space,
  Switch,
  Form,
  Input,
  InputNumber,
  Select,
  Upload,
  message,
  Tabs,
  Row,
  Col,
  Divider,
  Typography,
  Alert,
  Tag,
  Modal,
  Progress,
  List,
  Avatar,
  Tooltip,
} from 'antd';
import {
  SaveOutlined,
  ReloadOutlined,
  UploadOutlined,
  SettingOutlined,
  SecurityScanOutlined,
  MailOutlined,
  MessageOutlined,
  DatabaseOutlined,
  CloudOutlined,
  BugOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useRequest } from '../../hooks/useRequest';
import { settingsApi } from '../../api/settings';
import { StateWrapper } from '../../components/common/LoadingEmpty';

const { Text, Title, Paragraph } = Typography;
const { TextArea } = Input;
const { TabPane } = Tabs;
const { Option } = Select;

// 系统设置接口
interface SystemSettings {
  // 基础设置
  siteName: string;
  siteDescription: string;
  siteLogo: string;
  siteIcon: string;
  timezone: string;
  language: string;
  theme: 'light' | 'dark' | 'auto';
  
  // 安全设置
  passwordMinLength: number;
  passwordRequireSpecialChar: boolean;
  sessionTimeout: number;
  maxLoginAttempts: number;
  lockoutDuration: number;
  enableTwoFactor: boolean;
  
  // 邮件设置
  emailProvider: 'smtp' | 'sendgrid' | 'aws';
  smtpHost: string;
  smtpPort: number;
  smtpUsername: string;
  smtpPassword: string;
  smtpEncryption: 'none' | 'tls' | 'ssl';
  emailFromAddress: string;
  emailFromName: string;
  
  // 消息设置
  enableSms: boolean;
  smsProvider: 'twilio' | 'aliyun' | 'tencent';
  smsApiKey: string;
  smsApiSecret: string;
  enablePush: boolean;
  pushProvider: 'firebase' | 'jpush';
  pushApiKey: string;
  
  // 存储设置
  storageProvider: 'local' | 'oss' | 's3' | 'cos';
  storageEndpoint: string;
  storageAccessKey: string;
  storageSecretKey: string;
  storageBucket: string;
  storageRegion: string;
  
  // 缓存设置
  cacheProvider: 'memory' | 'redis';
  redisHost: string;
  redisPort: number;
  redisPassword: string;
  redisDatabase: number;
  cacheTtl: number;
  
  // 日志设置
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  logRetentionDays: number;
  enableAccessLog: boolean;
  enableErrorLog: boolean;
  enableAuditLog: boolean;
}

// 系统状态接口
interface SystemStatus {
  version: string;
  uptime: number;
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  databaseStatus: 'connected' | 'disconnected';
  cacheStatus: 'connected' | 'disconnected';
  emailStatus: 'configured' | 'not_configured';
  storageStatus: 'configured' | 'not_configured';
}

const Settings: React.FC = () => {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState('basic');
  const [testEmailVisible, setTestEmailVisible] = useState(false);
  const [testEmailLoading, setTestEmailLoading] = useState(false);

  // 获取系统设置
  const {
    data: settings,
    loading: settingsLoading,
    error: settingsError,
    run: fetchSettings,
  } = useRequest(settingsApi.getSettings, {
    defaultRun: true,
    onSuccess: (data) => {
      form.setFieldsValue(data);
    },
  });

  // 获取系统状态
  const {
    data: systemStatus,
    loading: statusLoading,
    run: fetchSystemStatus,
  } = useRequest(settingsApi.getSystemStatus, {
    defaultRun: true,
  });

  // 保存设置
  const { loading: saving, run: saveSettings } = useRequest(
    settingsApi.updateSettings,
    {
      manual: true,
      onSuccess: () => {
        message.success(t('settings.saveSuccess'));
        fetchSettings();
      },
    }
  );

  // 测试邮件配置
  const { loading: testingEmail, run: testEmailConfig } = useRequest(
    settingsApi.testEmailConfig,
    {
      manual: true,
      onSuccess: () => {
        message.success(t('settings.emailTestSuccess'));
        setTestEmailVisible(false);
      },
    }
  );

  // 测试存储配置
  const { loading: testingStorage, run: testStorageConfig } = useRequest(
    settingsApi.testStorageConfig,
    {
      manual: true,
      onSuccess: () => {
        message.success(t('settings.storageTestSuccess'));
      },
    }
  );

  // 清理缓存
  const { loading: clearingCache, run: clearCache } = useRequest(
    settingsApi.clearCache,
    {
      manual: true,
      onSuccess: () => {
        message.success(t('settings.cacheClearSuccess'));
        fetchSystemStatus();
      },
    }
  );

  // 处理保存
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      await saveSettings(values);
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  // 处理重置
  const handleReset = () => {
    Modal.confirm({
      title: t('settings.confirmReset'),
      content: t('settings.confirmResetMessage'),
      onOk: () => {
        form.setFieldsValue(settings);
        message.success(t('settings.resetSuccess'));
      },
    });
  };

  // 处理测试邮件
  const handleTestEmail = async (values: { email: string; subject: string; content: string }) => {
    await testEmailConfig(values);
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
      case 'configured':
        return 'green';
      case 'disconnected':
      case 'not_configured':
        return 'red';
      default:
        return 'orange';
    }
  };

  // 获取状态图标
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
      case 'configured':
        return <CheckCircleOutlined />;
      case 'disconnected':
      case 'not_configured':
        return <ExclamationCircleOutlined />;
      default:
        return <InfoCircleOutlined />;
    }
  };

  // 格式化运行时间
  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}${t('settings.days')} ${hours}${t('settings.hours')} ${minutes}${t('settings.minutes')}`;
  };

  return (
    <div style={{ padding: '24px' }}>
      <StateWrapper
        loading={settingsLoading}
        error={settingsError}
        onRetry={fetchSettings}
      >
        <Card
          title={
            <Space>
              <SettingOutlined />
              <Text strong>{t('settings.title')}</Text>
            </Space>
          }
          extra={
            <Space>
              <Button icon={<ReloadOutlined />} onClick={handleReset}>
                {t('settings.reset')}
              </Button>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                loading={saving}
                onClick={handleSave}
              >
                {t('settings.save')}
              </Button>
            </Space>
          }
        >
          <Tabs activeKey={activeTab} onChange={setActiveTab}>
            {/* 基础设置 */}
            <TabPane tab={t('settings.basic')} key="basic">
              <Form form={form} layout="vertical">
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Form.Item
                      name="siteName"
                      label={t('settings.siteName')}
                      rules={[{ required: true, message: t('settings.siteNameRequired') }]}
                    >
                      <Input placeholder={t('settings.siteNamePlaceholder')} />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="timezone" label={t('settings.timezone')}>
                      <Select placeholder={t('settings.timezonePlaceholder')}>
                        <Option value="Asia/Shanghai">{t('settings.timezoneShanghai')}</Option>
                        <Option value="America/New_York">{t('settings.timezoneNewYork')}</Option>
                        <Option value="Europe/London">{t('settings.timezoneLondon')}</Option>
                        <Option value="Asia/Tokyo">{t('settings.timezoneTokyo')}</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col span={24}>
                    <Form.Item name="siteDescription" label={t('settings.siteDescription')}>
                      <TextArea
                        rows={3}
                        placeholder={t('settings.siteDescriptionPlaceholder')}
                      />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="language" label={t('settings.language')}>
                      <Select>
                        <Option value="zh-CN">{t('settings.languageZhCN')}</Option>
                        <Option value="en-US">{t('settings.languageEnUS')}</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="theme" label={t('settings.theme')}>
                      <Select>
                        <Option value="light">{t('settings.themeLight')}</Option>
                        <Option value="dark">{t('settings.themeDark')}</Option>
                        <Option value="auto">{t('settings.themeAuto')}</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                </Row>
              </Form>
            </TabPane>

            {/* 安全设置 */}
            <TabPane tab={t('settings.security')} key="security">
              <Form form={form} layout="vertical">
                <Row gutter={[16, 16]}>
                  <Col span={8}>
                    <Form.Item
                      name="passwordMinLength"
                      label={t('settings.passwordMinLength')}
                      rules={[{ required: true, message: t('settings.passwordMinLengthRequired') }]}
                    >
                      <InputNumber min={6} max={20} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                  <Col span={8}>
                    <Form.Item
                      name="sessionTimeout"
                      label={t('settings.sessionTimeout')}
                      extra={t('settings.sessionTimeoutExtra')}
                    >
                      <InputNumber min={30} max={1440} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                  <Col span={8}>
                    <Form.Item
                      name="maxLoginAttempts"
                      label={t('settings.maxLoginAttempts')}
                    >
                      <InputNumber min={3} max={10} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name="passwordRequireSpecialChar"
                      label={t('settings.passwordRequireSpecialChar')}
                      valuePropName="checked"
                    >
                      <Switch />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name="enableTwoFactor"
                      label={t('settings.enableTwoFactor')}
                      valuePropName="checked"
                    >
                      <Switch />
                    </Form.Item>
                  </Col>
                </Row>
              </Form>
            </TabPane>

            {/* 邮件设置 */}
            <TabPane tab={t('settings.email')} key="email">
              <Form form={form} layout="vertical">
                <Row gutter={[16, 16]}>
                  <Col span={24}>
                    <Alert
                      message={t('settings.emailConfigTip')}
                      type="info"
                      showIcon
                      style={{ marginBottom: '16px' }}
                    />
                  </Col>
                  <Col span={8}>
                    <Form.Item name="emailProvider" label={t('settings.emailProvider')}>
                      <Select>
                        <Option value="smtp">SMTP</Option>
                        <Option value="sendgrid">SendGrid</Option>
                        <Option value="aws">AWS SES</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col span={8}>
                    <Form.Item name="smtpHost" label={t('settings.smtpHost')}>
                      <Input placeholder="smtp.gmail.com" />
                    </Form.Item>
                  </Col>
                  <Col span={8}>
                    <Form.Item name="smtpPort" label={t('settings.smtpPort')}>
                      <InputNumber min={1} max={65535} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="smtpUsername" label={t('settings.smtpUsername')}>
                      <Input />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="smtpPassword" label={t('settings.smtpPassword')}>
                      <Input.Password />
                    </Form.Item>
                  </Col>
                  <Col span={8}>
                    <Form.Item name="smtpEncryption" label={t('settings.smtpEncryption')}>
                      <Select>
                        <Option value="none">{t('settings.encryptionNone')}</Option>
                        <Option value="tls">TLS</Option>
                        <Option value="ssl">SSL</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col span={8}>
                    <Form.Item name="emailFromAddress" label={t('settings.emailFromAddress')}>
                      <Input placeholder="noreply@example.com" />
                    </Form.Item>
                  </Col>
                  <Col span={8}>
                    <Form.Item name="emailFromName" label={t('settings.emailFromName')}>
                      <Input placeholder={t('settings.emailFromNamePlaceholder')} />
                    </Form.Item>
                  </Col>
                  <Col span={24}>
                    <Button
                      icon={<MailOutlined />}
                      onClick={() => setTestEmailVisible(true)}
                    >
                      {t('settings.testEmail')}
                    </Button>
                  </Col>
                </Row>
              </Form>
            </TabPane>

            {/* 存储设置 */}
            <TabPane tab={t('settings.storage')} key="storage">
              <Form form={form} layout="vertical">
                <Row gutter={[16, 16]}>
                  <Col span={24}>
                    <Form.Item name="storageProvider" label={t('settings.storageProvider')}>
                      <Select>
                        <Option value="local">{t('settings.storageLocal')}</Option>
                        <Option value="oss">{t('settings.storageOSS')}</Option>
                        <Option value="s3">{t('settings.storageS3')}</Option>
                        <Option value="cos">{t('settings.storageCOS')}</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="storageEndpoint" label={t('settings.storageEndpoint')}>
                      <Input placeholder="https://oss-cn-hangzhou.aliyuncs.com" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="storageBucket" label={t('settings.storageBucket')}>
                      <Input placeholder="my-bucket" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="storageAccessKey" label={t('settings.storageAccessKey')}>
                      <Input />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="storageSecretKey" label={t('settings.storageSecretKey')}>
                      <Input.Password />
                    </Form.Item>
                  </Col>
                  <Col span={24}>
                    <Button
                      icon={<CloudOutlined />}
                      loading={testingStorage}
                      onClick={() => testStorageConfig()}
                    >
                      {t('settings.testStorage')}
                    </Button>
                  </Col>
                </Row>
              </Form>
            </TabPane>

            {/* 系统状态 */}
            <TabPane tab={t('settings.systemStatus')} key="status">
              <Row gutter={[16, 16]}>
                <Col span={24}>
                  <Card title={t('settings.systemInfo')} size="small">
                    <Row gutter={[16, 16]}>
                      <Col span={6}>
                        <Text strong>{t('settings.version')}: </Text>
                        <Tag color="blue">{systemStatus?.version}</Tag>
                      </Col>
                      <Col span={6}>
                        <Text strong>{t('settings.uptime')}: </Text>
                        <Text>{systemStatus ? formatUptime(systemStatus.uptime) : '-'}</Text>
                      </Col>
                      <Col span={12}>
                        <Space>
                          <Button
                            size="small"
                            icon={<ReloadOutlined />}
                            onClick={fetchSystemStatus}
                            loading={statusLoading}
                          >
                            {t('settings.refresh')}
                          </Button>
                          <Button
                            size="small"
                            icon={<DatabaseOutlined />}
                            loading={clearingCache}
                            onClick={clearCache}
                          >
                            {t('settings.clearCache')}
                          </Button>
                        </Space>
                      </Col>
                    </Row>
                  </Card>
                </Col>
                
                <Col span={12}>
                  <Card title={t('settings.resourceUsage')} size="small">
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <div>
                        <Text>{t('settings.cpuUsage')}</Text>
                        <Progress
                          percent={systemStatus?.cpuUsage || 0}
                          status={systemStatus?.cpuUsage && systemStatus.cpuUsage > 80 ? 'exception' : 'normal'}
                        />
                      </div>
                      <div>
                        <Text>{t('settings.memoryUsage')}</Text>
                        <Progress
                          percent={systemStatus?.memoryUsage || 0}
                          status={systemStatus?.memoryUsage && systemStatus.memoryUsage > 80 ? 'exception' : 'normal'}
                        />
                      </div>
                      <div>
                        <Text>{t('settings.diskUsage')}</Text>
                        <Progress
                          percent={systemStatus?.diskUsage || 0}
                          status={systemStatus?.diskUsage && systemStatus.diskUsage > 90 ? 'exception' : 'normal'}
                        />
                      </div>
                    </Space>
                  </Card>
                </Col>
                
                <Col span={12}>
                  <Card title={t('settings.serviceStatus')} size="small">
                    <List
                      size="small"
                      dataSource={[
                        {
                          name: t('settings.database'),
                          status: systemStatus?.databaseStatus || 'disconnected',
                          icon: <DatabaseOutlined />,
                        },
                        {
                          name: t('settings.cache'),
                          status: systemStatus?.cacheStatus || 'disconnected',
                          icon: <BugOutlined />,
                        },
                        {
                          name: t('settings.email'),
                          status: systemStatus?.emailStatus || 'not_configured',
                          icon: <MailOutlined />,
                        },
                        {
                          name: t('settings.storage'),
                          status: systemStatus?.storageStatus || 'not_configured',
                          icon: <CloudOutlined />,
                        },
                      ]}
                      renderItem={(item) => (
                        <List.Item>
                          <List.Item.Meta
                            avatar={<Avatar icon={item.icon} size="small" />}
                            title={item.name}
                            description={
                              <Tag color={getStatusColor(item.status)} icon={getStatusIcon(item.status)}>
                                {t(`settings.status${item.status.charAt(0).toUpperCase() + item.status.slice(1).replace('_', '')}`)}
                              </Tag>
                            }
                          />
                        </List.Item>
                      )}
                    />
                  </Card>
                </Col>
              </Row>
            </TabPane>
          </Tabs>
        </Card>
      </StateWrapper>

      {/* 测试邮件弹窗 */}
      <Modal
        title={t('settings.testEmail')}
        open={testEmailVisible}
        onCancel={() => setTestEmailVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          layout="vertical"
          onFinish={handleTestEmail}
          initialValues={{
            subject: t('settings.testEmailSubject'),
            content: t('settings.testEmailContent'),
          }}
        >
          <Form.Item
            name="email"
            label={t('settings.testEmailAddress')}
            rules={[
              { required: true, message: t('settings.testEmailAddressRequired') },
              { type: 'email', message: t('settings.testEmailAddressInvalid') },
            ]}
          >
            <Input placeholder="test@example.com" />
          </Form.Item>
          <Form.Item
            name="subject"
            label={t('settings.testEmailSubjectLabel')}
            rules={[{ required: true, message: t('settings.testEmailSubjectRequired') }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="content"
            label={t('settings.testEmailContentLabel')}
            rules={[{ required: true, message: t('settings.testEmailContentRequired') }]}
          >
            <TextArea rows={4} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button onClick={() => setTestEmailVisible(false)}>
                {t('common.cancel')}
              </Button>
              <Button type="primary" htmlType="submit" loading={testingEmail}>
                {t('settings.sendTestEmail')}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Settings;