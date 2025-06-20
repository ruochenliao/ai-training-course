import React, { useState, useRef } from 'react'
import { Upload, Button, Image, Card, Space, Typography, message, Progress, Tag } from 'antd'
import {
  PictureOutlined,
  FileOutlined,
  VideoCameraOutlined,
  AudioOutlined,
  DeleteOutlined,
  EyeOutlined,
  DownloadOutlined
} from '@ant-design/icons'
import type { UploadFile, UploadProps } from 'antd'

const { Text, Title } = Typography
const { Dragger } = Upload

interface MultimodalFile {
  id: string
  name: string
  type: string
  size: number
  url?: string
  file?: File
  status: 'uploading' | 'done' | 'error'
  progress?: number
  preview?: string
}

interface MultimodalSupportProps {
  files: MultimodalFile[]
  onFilesChange: (files: MultimodalFile[]) => void
  maxFiles?: number
  maxSize?: number // MB
  acceptedTypes?: string[]
  onAnalyze?: (file: MultimodalFile) => void
}

/**
 * 多模态内容支持组件
 * 支持图片、视频、音频、文档等多种格式
 * 提供预览、分析、管理功能
 */
const MultimodalSupport: React.FC<MultimodalSupportProps> = ({
  files,
  onFilesChange,
  maxFiles = 10,
  maxSize = 50,
  acceptedTypes = ['image/*', 'video/*', 'audio/*', '.pdf', '.doc', '.docx', '.txt'],
  onAnalyze
}) => {
  const [previewVisible, setPreviewVisible] = useState(false)
  const [previewImage, setPreviewImage] = useState('')
  const [previewTitle, setPreviewTitle] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 获取文件图标
  const getFileIcon = (type: string) => {
    if (type.startsWith('image/')) return <PictureOutlined />
    if (type.startsWith('video/')) return <VideoCameraOutlined />
    if (type.startsWith('audio/')) return <AudioOutlined />
    return <FileOutlined />
  }

  // 获取文件类型标签颜色
  const getFileTypeColor = (type: string) => {
    if (type.startsWith('image/')) return 'blue'
    if (type.startsWith('video/')) return 'purple'
    if (type.startsWith('audio/')) return 'green'
    return 'default'
  }

  // 格式化文件大小
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // 处理文件上传
  const handleUpload: UploadProps['customRequest'] = async (options) => {
    const { file, onSuccess, onError, onProgress } = options
    const uploadFile = file as File

    // 检查文件大小
    if (uploadFile.size > maxSize * 1024 * 1024) {
      message.error(`文件大小不能超过 ${maxSize}MB`)
      onError?.(new Error('文件过大'))
      return
    }

    // 检查文件数量
    if (files.length >= maxFiles) {
      message.error(`最多只能上传 ${maxFiles} 个文件`)
      onError?.(new Error('文件数量超限'))
      return
    }

    const fileId = `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const newFile: MultimodalFile = {
      id: fileId,
      name: uploadFile.name,
      type: uploadFile.type,
      size: uploadFile.size,
      file: uploadFile,
      status: 'uploading',
      progress: 0
    }

    // 添加到文件列表
    const updatedFiles = [...files, newFile]
    onFilesChange(updatedFiles)

    try {
      // 模拟上传进度
      const progressInterval = setInterval(() => {
        newFile.progress = (newFile.progress || 0) + Math.random() * 30
        if (newFile.progress >= 100) {
          newFile.progress = 100
          newFile.status = 'done'
          clearInterval(progressInterval)
          
          // 生成预览URL
          if (uploadFile.type.startsWith('image/')) {
            newFile.preview = URL.createObjectURL(uploadFile)
          }
          
          onFilesChange([...files.filter(f => f.id !== fileId), newFile])
          onSuccess?.(newFile)
          message.success(`${uploadFile.name} 上传成功`)
        } else {
          onFilesChange([...files.filter(f => f.id !== fileId), newFile])
        }
      }, 200)

    } catch (error) {
      newFile.status = 'error'
      onFilesChange([...files.filter(f => f.id !== fileId), newFile])
      onError?.(error as Error)
      message.error(`${uploadFile.name} 上传失败`)
    }
  }

  // 删除文件
  const handleRemoveFile = (fileId: string) => {
    const updatedFiles = files.filter(f => f.id !== fileId)
    onFilesChange(updatedFiles)
    message.success('文件已删除')
  }

  // 预览图片
  const handlePreview = (file: MultimodalFile) => {
    if (file.type.startsWith('image/') && file.preview) {
      setPreviewImage(file.preview)
      setPreviewTitle(file.name)
      setPreviewVisible(true)
    }
  }

  // 分析文件
  const handleAnalyze = (file: MultimodalFile) => {
    if (onAnalyze) {
      onAnalyze(file)
      message.info(`正在分析 ${file.name}...`)
    }
  }

  return (
    <div className="multimodal-support">
      {/* 文件上传区域 */}
      <Dragger
        multiple
        customRequest={handleUpload}
        showUploadList={false}
        accept={acceptedTypes.join(',')}
        className="multimodal-uploader"
        style={{
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(20px)',
          border: '2px dashed rgba(102, 126, 234, 0.3)',
          borderRadius: '16px',
          padding: '24px'
        }}
      >
        <div className="upload-content">
          <div className="upload-icon" style={{ fontSize: '48px', color: '#667eea', marginBottom: '16px' }}>
            <PictureOutlined />
          </div>
          <Title level={4} style={{ color: 'rgba(255, 255, 255, 0.9)', margin: '0 0 8px 0' }}>
            拖拽文件到此处或点击上传
          </Title>
          <Text style={{ color: 'rgba(255, 255, 255, 0.7)' }}>
            支持图片、视频、音频、文档等格式，单个文件不超过 {maxSize}MB
          </Text>
        </div>
      </Dragger>

      {/* 文件列表 */}
      {files.length > 0 && (
        <div className="file-list" style={{ marginTop: '24px' }}>
          <Title level={5} style={{ color: 'rgba(255, 255, 255, 0.9)', marginBottom: '16px' }}>
            已上传文件 ({files.length}/{maxFiles})
          </Title>
          
          <div className="file-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
            {files.map((file) => (
              <Card
                key={file.id}
                size="small"
                className="file-card"
                style={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  backdropFilter: 'blur(20px)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '12px'
                }}
                actions={[
                  file.type.startsWith('image/') && (
                    <Button
                      type="text"
                      icon={<EyeOutlined />}
                      onClick={() => handlePreview(file)}
                      style={{ color: 'rgba(255, 255, 255, 0.8)' }}
                    >
                      预览
                    </Button>
                  ),
                  onAnalyze && (
                    <Button
                      type="text"
                      icon={<EyeOutlined />}
                      onClick={() => handleAnalyze(file)}
                      style={{ color: 'rgba(102, 126, 234, 0.8)' }}
                    >
                      分析
                    </Button>
                  ),
                  <Button
                    type="text"
                    icon={<DeleteOutlined />}
                    onClick={() => handleRemoveFile(file.id)}
                    style={{ color: 'rgba(255, 107, 107, 0.8)' }}
                    danger
                  >
                    删除
                  </Button>
                ].filter(Boolean)}
              >
                <Card.Meta
                  avatar={
                    <div style={{ fontSize: '24px', color: '#667eea' }}>
                      {getFileIcon(file.type)}
                    </div>
                  }
                  title={
                    <div>
                      <Text 
                        ellipsis={{ tooltip: file.name }} 
                        style={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 500 }}
                      >
                        {file.name}
                      </Text>
                      <div style={{ marginTop: '4px' }}>
                        <Tag color={getFileTypeColor(file.type)} size="small">
                          {file.type.split('/')[0]}
                        </Tag>
                      </div>
                    </div>
                  }
                  description={
                    <div>
                      <Text style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '12px' }}>
                        {formatFileSize(file.size)}
                      </Text>
                      {file.status === 'uploading' && file.progress !== undefined && (
                        <Progress
                          percent={Math.round(file.progress)}
                          size="small"
                          style={{ marginTop: '8px' }}
                          strokeColor={{
                            '0%': '#667eea',
                            '100%': '#764ba2',
                          }}
                        />
                      )}
                      {file.status === 'error' && (
                        <Text type="danger" style={{ fontSize: '12px', marginTop: '4px', display: 'block' }}>
                          上传失败
                        </Text>
                      )}
                    </div>
                  }
                />
                
                {/* 图片预览缩略图 */}
                {file.type.startsWith('image/') && file.preview && (
                  <div style={{ marginTop: '12px', textAlign: 'center' }}>
                    <img
                      src={file.preview}
                      alt={file.name}
                      style={{
                        maxWidth: '100%',
                        maxHeight: '120px',
                        borderRadius: '8px',
                        objectFit: 'cover',
                        cursor: 'pointer'
                      }}
                      onClick={() => handlePreview(file)}
                    />
                  </div>
                )}
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* 图片预览模态框 */}
      <Image
        style={{ display: 'none' }}
        src={previewImage}
        preview={{
          visible: previewVisible,
          onVisibleChange: setPreviewVisible,
          mask: (
            <div style={{ color: 'white' }}>
              <EyeOutlined style={{ marginRight: 8 }} />
              预览 {previewTitle}
            </div>
          )
        }}
      />
    </div>
  )
}

export default MultimodalSupport
