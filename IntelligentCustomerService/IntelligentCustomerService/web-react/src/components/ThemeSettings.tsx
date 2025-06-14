import React, {useState} from 'react'
import {
    Badge,
    Button,
    Card,
    ColorPicker,
    Divider,
    Drawer,
    Form,
    Input,
    message,
    Modal,
    Popconfirm,
    Space,
    Switch,
    Tabs,
    Tooltip,
    Typography,
} from 'antd'
import {
    BgColorsOutlined,
    BulbOutlined,
    CheckOutlined,
    CloseOutlined,
    DeleteOutlined,
    PlusOutlined,
    SaveOutlined,
    SettingOutlined,
} from '@ant-design/icons'
import {useTheme} from '../contexts/ThemeContext'
import type {ThemePreset} from '../store/theme'
import type {Color} from 'antd/es/color-picker'
import {useTranslation} from 'react-i18next'

const { Title, Text } = Typography
const { TabPane } = Tabs

interface ThemeSettingsProps {
  children?: React.ReactNode
}

const ThemeSettings: React.FC<ThemeSettingsProps> = ({ children }) => {
  const [open, setOpen] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [form] = Form.useForm()
  const [activeTab, setActiveTab] = useState('1')
  const { t } = useTranslation()

  const {
    isDark,
    toggleTheme,
    primaryColor,
    secondaryColor,
    successColor,
    warningColor,
    errorColor,
    infoColor,
    setThemeColor,
    activePreset,
    presets,
    customPresets,
    applyPreset,
    addCustomPreset,
    removeCustomPreset,
  } = useTheme()

  // 合并系统预设和自定义预设
  const allPresets = [...presets, ...customPresets]

  const showDrawer = () => {
    setOpen(true)
  }

  const onClose = () => {
    setOpen(false)
  }

  const handleColorChange = (colorKey: string, color: Color) => {
    const hexColor = color.toHexString()
    setThemeColor(colorKey, hexColor)
  }

  const showAddPresetModal = () => {
    form.resetFields()
    form.setFieldsValue({
      primaryColor,
      secondaryColor,
      successColor,
      warningColor,
      errorColor,
      infoColor,
    })
    setModalVisible(true)
  }

  const handleAddPreset = () => {
    form.validateFields().then((values) => {
      const newPreset: ThemePreset = {
        name: values.name,
        primaryColor: values.primaryColor,
        secondaryColor: values.secondaryColor,
        successColor: values.successColor,
        warningColor: values.warningColor,
        errorColor: values.errorColor,
        infoColor: values.infoColor,
      }

      // 检查是否已存在同名预设
      const exists = allPresets.some((p) => p.name === values.name)
      if (exists) {
        message.error(t('theme.presetAlreadyExists'))
        return
      }

      addCustomPreset(newPreset)
      applyPreset(values.name)
      setModalVisible(false)
      message.success(t('theme.presetSaved'))
    })
  }

  const handleRemovePreset = (presetName: string) => {
    removeCustomPreset(presetName)
    // 如果移除的是当前激活的预设，切换到默认预设
    if (activePreset === presetName) {
      applyPreset(t('theme.defaultBlue'))
    }
    message.success(t('theme.presetDeleted'))
  }

  const getPresetDisplayName = (presetName: string) => {
    const presetNameMap: Record<string, string> = {
      默认蓝: 'theme.defaultBlue',
      科技紫: 'theme.techPurple',
      活力橙: 'theme.vividOrange',
      沉稳绿: 'theme.calmGreen',
      商务灰: 'theme.businessGray',
    }

    if (presetName in presetNameMap) {
      return t(presetNameMap[presetName])
    }

    return presetName
  }

  return (
    <>
      {children ? (
        <span onClick={showDrawer}>{children}</span>
      ) : (
        <Button type='text' icon={<SettingOutlined />} onClick={showDrawer} style={{ fontSize: '16px' }} />
      )}
      <Drawer
        title={t('theme.settings')}
        placement='right'
        width={340}
        onClose={onClose}
        open={open}
        extra={
          <Space>
            <Button onClick={onClose}>{t('common.cancel')}</Button>
          </Space>
        }
      >
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane
            tab={
              <span>
                <BulbOutlined />
                {t('theme.mode')}
              </span>
            }
            key='1'
          >
            <div className='p-4'>
              <Title level={5}>{t('theme.mode')}</Title>
              <div className='flex-y-center justify-between mt-4'>
                <Text>{t('theme.darkMode')}</Text>
                <Switch checked={isDark} onChange={toggleTheme} checkedChildren={<CheckOutlined />} unCheckedChildren={<CloseOutlined />} />
              </div>

              <Divider />

              <Title level={5}>{t('theme.preset')}</Title>
              <div className='grid grid-cols-2 gap-2 mt-4'>
                {allPresets.map((preset) => {
                  const isActive = activePreset === preset.name
                  const isCustom = customPresets.some((p) => p.name === preset.name)
                  const displayName = getPresetDisplayName(preset.name)

                  return (
                    <Badge.Ribbon key={preset.name} text={isActive ? t('theme.currentTheme') : ''} color={isActive ? 'blue' : 'transparent'}>
                      <Card
                        size='small'
                        className={`cursor-pointer border-2 ${isActive ? 'border-blue-500' : 'border-gray-200 dark:border-gray-700'}`}
                        onClick={() => applyPreset(preset.name)}
                        bodyStyle={{ padding: '8px' }}
                      >
                        <div className='flex items-center justify-between'>
                          <div className='flex items-center'>
                            <div className='w-5 h-5 rounded-full mr-2' style={{ backgroundColor: preset.primaryColor }} />
                            <Text ellipsis>{displayName}</Text>
                          </div>
                          {isCustom && (
                            <Popconfirm
                              title={t('theme.confirmDelete')}
                              onConfirm={(e) => {
                                e?.stopPropagation()
                                handleRemovePreset(preset.name)
                              }}
                              okText={t('common.confirm')}
                              cancelText={t('common.cancel')}
                            >
                              <Button type='text' size='small' danger icon={<DeleteOutlined />} onClick={(e) => e.stopPropagation()} />
                            </Popconfirm>
                          )}
                        </div>
                      </Card>
                    </Badge.Ribbon>
                  )
                })}

                <Button className='h-full border-dashed' icon={<PlusOutlined />} onClick={showAddPresetModal}>
                  {t('theme.createPreset')}
                </Button>
              </div>
            </div>
          </TabPane>

          <TabPane
            tab={
              <span>
                <BgColorsOutlined />
                {t('theme.colorConfig')}
              </span>
            }
            key='2'
          >
            <div className='p-4'>
              <Title level={5}>{t('theme.colorConfig')}</Title>

              <div className='mt-4'>
                <div className='flex-y-center justify-between mb-3'>
                  <Text>{t('theme.primaryColor')}</Text>
                  <ColorPicker value={primaryColor} onChange={(color) => handleColorChange('primaryColor', color)} />
                </div>

                <div className='flex-y-center justify-between mb-3'>
                  <Text>{t('theme.secondaryColor')}</Text>
                  <ColorPicker value={secondaryColor} onChange={(color) => handleColorChange('secondaryColor', color)} />
                </div>

                <div className='flex-y-center justify-between mb-3'>
                  <Text>{t('theme.successColor')}</Text>
                  <ColorPicker value={successColor} onChange={(color) => handleColorChange('successColor', color)} />
                </div>

                <div className='flex-y-center justify-between mb-3'>
                  <Text>{t('theme.warningColor')}</Text>
                  <ColorPicker value={warningColor} onChange={(color) => handleColorChange('warningColor', color)} />
                </div>

                <div className='flex-y-center justify-between mb-3'>
                  <Text>{t('theme.errorColor')}</Text>
                  <ColorPicker value={errorColor} onChange={(color) => handleColorChange('errorColor', color)} />
                </div>

                <div className='flex-y-center justify-between mb-3'>
                  <Text>{t('theme.infoColor')}</Text>
                  <ColorPicker value={infoColor} onChange={(color) => handleColorChange('infoColor', color)} />
                </div>
              </div>

              <Divider />

              <div className='flex justify-end mt-4'>
                <Tooltip title={t('theme.saveAsPreset')}>
                  <Button type='primary' icon={<SaveOutlined />} onClick={showAddPresetModal}>
                    {t('theme.saveAsPreset')}
                  </Button>
                </Tooltip>
              </div>
            </div>
          </TabPane>
        </Tabs>
      </Drawer>

      <Modal
        title={t('theme.saveAsPreset')}
        open={modalVisible}
        onOk={handleAddPreset}
        onCancel={() => setModalVisible(false)}
        okText={t('common.save')}
        cancelText={t('common.cancel')}
      >
        <Form
          form={form}
          layout='vertical'
          initialValues={{
            primaryColor,
            secondaryColor,
            successColor,
            warningColor,
            errorColor,
            infoColor,
          }}
        >
          <Form.Item name='name' label={t('theme.presetName')} rules={[{ required: true, message: t('theme.presetNameRequired') }]}>
            <Input placeholder={t('theme.presetName')} />
          </Form.Item>

          <Form.Item name='primaryColor' label={t('theme.primaryColor')}>
            <ColorPicker />
          </Form.Item>

          <Form.Item name='secondaryColor' label={t('theme.secondaryColor')}>
            <ColorPicker />
          </Form.Item>

          <Form.Item name='successColor' label={t('theme.successColor')}>
            <ColorPicker />
          </Form.Item>

          <Form.Item name='warningColor' label={t('theme.warningColor')}>
            <ColorPicker />
          </Form.Item>

          <Form.Item name='errorColor' label={t('theme.errorColor')}>
            <ColorPicker />
          </Form.Item>

          <Form.Item name='infoColor' label={t('theme.infoColor')}>
            <ColorPicker />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}

export default ThemeSettings
