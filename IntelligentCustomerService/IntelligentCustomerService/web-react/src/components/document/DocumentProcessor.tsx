import React, { useState, useRef } from 'react'
import { 
  Upload, 
  Button, 
  Card, 
  Progress, 
  List, 
  Typography, 
  Space, 
  Tag, 
  message, 
  Modal,
  Tooltip,
  Divider,
  Alert
} from 'antd'
import {
  FileTextOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FileExcelOutlined,
  FilePptOutlined,
  FileImageOutlined,
  DeleteOutlined,
  EyeOutlined,
  SearchOutlined,
  UploadOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons'
import type { UploadFile, UploadProps } from 'antd'

const { Text, Title, Paragraph } = Typography
const { Dragger } = Upload

interface DocumentFile {
  id: string
  filename: string
  file_type: string
  file_size: number
  status: 'processing' | 'completed' | 'failed'
  chunk_count?: number
  created_at: string
  processed_at?: string
  metadata?: any
}

interface DocumentProcessorProps {
  conversationId?: string
  onDocumentProcessed?: (document: DocumentFile) => void
  onDocumentSearch?: (query: string) => void
  className?: string
}

/**
 * 文档处理器组件
 * 支持文档上传、解析、搜索等功能
 * 集成Marker框架进行高质量文档解析
 */
const DocumentProcessor: React.FC<DocumentProcessorProps> = ({
  conversationId,
  onDocumentProcessed,
  onDocumentSearch,
  className
}) => {
  const [documents, setDocuments] = useState<DocumentFile[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [previewVisible, setPreviewVisible] = useState(false)
  const [previewDocument, setPreviewDocument] = useState<DocumentFile | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 获取文件图标
  const getFileIcon = (fileType: string) => {
    const type = fileType.toLowerCase()
    if (type === '.pdf') return <FilePdfOutlined style={{ color: '#ff4d4f' }} />
    if (['.doc', '.docx'].includes(type)) return <FileWordOutlined style={{ color: '#1890ff' }} />
    if (['.xls', '.xlsx'].includes(type)) return <FileExcelOutlined style={{ color: '#52c41a' }} />
    if (['.ppt', '.pptx'].includes(type)) return <FilePptOutlined style={{ color: '#fa8c16' }} />
    if (['.jpg', '.jpeg', '.png', '.gif'].includes(type)) return <FileImageOutlined style={{ color: '#722ed1' }} />
    return <FileTextOutlined style={{ color: '#666' }} />
  }

  // 获取状态标签
  const getStatusTag = (status: string) => {
    switch (status) {
      case 'processing':
        return <Tag icon={<ClockCircleOutlined />} color="processing">处理中</Tag>
      case 'completed':
        return <Tag icon={<CheckCircleOutlined />} color="success">已完成</Tag>
      case 'failed':
        return <Tag icon={<ExclamationCircleOutlined />} color="error">处理失败</Tag>
      default:
        return <Tag color="default">未知状态</Tag>
    }
  }

  // 格式化文件大小
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // 上传配置
  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    action: '/api/v1/document/upload',
    headers: {
      authorization: `Bearer ${localStorage.getItem('token')}`,
    },
    data: {
      conversation_id: conversationId,
      extract_images: true,
      extract_tables: true,
      chunk_size: 1000,
      chunk_overlap: 200
    },
    beforeUpload: (file) => {
      // 检查文件类型
      const supportedTypes = [
        '.pdf', '.doc', '.docx', '.ppt', '.pptx', 
        '.xls', '.xlsx', '.txt', '.md', '.html', 
        '.csv', '.json', '.xml', '.rtf'
      ]
      
      const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()
      if (!supportedTypes.includes(fileExt)) {
        message.error(`不支持的文件格式: ${fileExt}`)
        return false
      }

      // 检查文件大小 (50MB)
      const maxSize = 50 * 1024 * 1024
      if (file.size > maxSize) {
        message.error('文件大小不能超过50MB')
        return false
      }

      setUploading(true)
      setUploadProgress(0)
      return true
    },
    onChange: (info) => {
      const { status } = info.file
      
      if (status === 'uploading') {
        setUploadProgress(info.file.percent || 0)
      } else if (status === 'done') {
        setUploading(false)
        setUploadProgress(0)
        
        const response = info.file.response
        if (response && response.document_id) {
          const newDocument: DocumentFile = {
            id: response.document_id,
            filename: response.file_name,
            file_type: '.' + response.file_name.split('.').pop()?.toLowerCase(),
            file_size: response.file_size,
            status: 'processing',
            created_at: new Date().toISOString()
          }
          
          setDocuments(prev => [newDocument, ...prev])
          message.success(`${info.file.name} 上传成功，正在处理中...`)
          
          // 轮询检查处理状态
          checkProcessingStatus(response.document_id)
          
          if (onDocumentProcessed) {
            onDocumentProcessed(newDocument)
          }
        }
      } else if (status === 'error') {
        setUploading(false)
        setUploadProgress(0)
        message.error(`${info.file.name} 上传失败`)
      }
    },
    onDrop: (e) => {
      console.log('Dropped files', e.dataTransfer.files)
    }
  }

  // 检查处理状态
  const checkProcessingStatus = async (documentId: string) => {
    try {
      const response = await fetch(`/api/v1/document/info/${documentId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      
      if (response.ok) {
        const documentInfo = await response.json()
        
        setDocuments(prev => prev.map(doc => 
          doc.id === documentId 
            ? { ...doc, ...documentInfo }
            : doc
        ))
        
        // 如果还在处理中，继续轮询
        if (documentInfo.status === 'processing') {
          setTimeout(() => checkProcessingStatus(documentId), 3000)
        } else if (documentInfo.status === 'completed') {
          message.success(`文档 ${documentInfo.filename} 处理完成`)
        } else if (documentInfo.status === 'failed') {
          message.error(`文档 ${documentInfo.filename} 处理失败`)
        }
      }
    } catch (error) {
      console.error('检查处理状态失败:', error)
    }
  }

  // 删除文档
  const deleteDocument = async (documentId: string) => {
    try {
      const response = await fetch(`/api/v1/document/delete/${documentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      
      if (response.ok) {
        setDocuments(prev => prev.filter(doc => doc.id !== documentId))
        message.success('文档删除成功')
      } else {
        message.error('文档删除失败')
      }
    } catch (error) {
      message.error('文档删除失败')
    }
  }

  // 预览文档
  const previewDocument = (document: DocumentFile) => {
    setPreviewDocument(document)
    setPreviewVisible(true)
  }

  // 搜索文档
  const searchInDocuments = () => {
    if (onDocumentSearch) {
      // 这里可以打开搜索对话框或直接触发搜索
      onDocumentSearch('')
    }
  }

  return (
    <div className={`document-processor ${className || ''}`}>
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span>📄 文档处理器</span>
            <Space>
              <Tooltip title="在文档中搜索">
                <Button 
                  type="text" 
                  icon={<SearchOutlined />} 
                  onClick={searchInDocuments}
                  disabled={documents.length === 0}
                />
              </Tooltip>
            </Space>
          </div>
        }
        style={{
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          borderRadius: '16px'
        }}
        headStyle={{
          background: 'rgba(102, 126, 234, 0.2)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          color: 'rgba(255, 255, 255, 0.9)'
        }}
        bodyStyle={{
          background: 'transparent'
        }}
      >
        {/* 上传区域 */}
        <Dragger
          {...uploadProps}
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '2px dashed rgba(102, 126, 234, 0.3)',
            borderRadius: '12px',
            marginBottom: '24px'
          }}
        >
          <div style={{ padding: '20px', textAlign: 'center' }}>
            <UploadOutlined style={{ fontSize: '48px', color: '#667eea', marginBottom: '16px' }} />
            <Title level={4} style={{ color: 'rgba(255, 255, 255, 0.9)', margin: '0 0 8px 0' }}>
              拖拽文档到此处或点击上传
            </Title>
            <Paragraph style={{ color: 'rgba(255, 255, 255, 0.7)', margin: 0 }}>
              支持 PDF、Word、Excel、PowerPoint、文本等格式，单个文件不超过50MB
            </Paragraph>
          </div>
        </Dragger>

        {/* 上传进度 */}
        {uploading && (
          <div style={{ marginBottom: '24px' }}>
            <Progress 
              percent={uploadProgress} 
              status="active"
              strokeColor={{
                '0%': '#667eea',
                '100%': '#764ba2',
              }}
            />
            <Text style={{ color: 'rgba(255, 255, 255, 0.8)' }}>
              正在上传文档...
            </Text>
          </div>
        )}

        {/* 支持格式说明 */}
        <Alert
          message="支持的文档格式"
          description={
            <div>
              <Tag color="red">PDF</Tag>
              <Tag color="blue">Word</Tag>
              <Tag color="green">Excel</Tag>
              <Tag color="orange">PowerPoint</Tag>
              <Tag color="purple">文本</Tag>
              <Tag color="cyan">Markdown</Tag>
              <Tag color="geekblue">HTML</Tag>
              <Tag color="gold">CSV/JSON</Tag>
            </div>
          }
          type="info"
          showIcon
          style={{
            background: 'rgba(24, 144, 255, 0.1)',
            border: '1px solid rgba(24, 144, 255, 0.3)',
            marginBottom: '24px'
          }}
        />

        {/* 文档列表 */}
        {documents.length > 0 && (
          <>
            <Divider style={{ borderColor: 'rgba(255, 255, 255, 0.2)' }}>
              <Text style={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                已上传文档 ({documents.length})
              </Text>
            </Divider>
            
            <List
              dataSource={documents}
              renderItem={(document) => (
                <List.Item
                  style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    borderRadius: '8px',
                    marginBottom: '8px',
                    padding: '12px 16px',
                    border: '1px solid rgba(255, 255, 255, 0.1)'
                  }}
                  actions={[
                    <Tooltip title="预览">
                      <Button
                        type="text"
                        icon={<EyeOutlined />}
                        onClick={() => previewDocument(document)}
                        style={{ color: 'rgba(255, 255, 255, 0.8)' }}
                      />
                    </Tooltip>,
                    <Tooltip title="删除">
                      <Button
                        type="text"
                        icon={<DeleteOutlined />}
                        onClick={() => deleteDocument(document.id)}
                        style={{ color: 'rgba(255, 107, 107, 0.8)' }}
                        danger
                      />
                    </Tooltip>
                  ]}
                >
                  <List.Item.Meta
                    avatar={getFileIcon(document.file_type)}
                    title={
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Text 
                          style={{ color: 'rgba(255, 255, 255, 0.9)', fontWeight: 500 }}
                          ellipsis={{ tooltip: document.filename }}
                        >
                          {document.filename}
                        </Text>
                        {getStatusTag(document.status)}
                      </div>
                    }
                    description={
                      <div style={{ color: 'rgba(255, 255, 255, 0.6)' }}>
                        <Text style={{ color: 'inherit', fontSize: '12px' }}>
                          {formatFileSize(document.file_size)}
                        </Text>
                        {document.chunk_count && (
                          <>
                            <Divider type="vertical" />
                            <Text style={{ color: 'inherit', fontSize: '12px' }}>
                              {document.chunk_count} 个分块
                            </Text>
                          </>
                        )}
                        <Divider type="vertical" />
                        <Text style={{ color: 'inherit', fontSize: '12px' }}>
                          {new Date(document.created_at).toLocaleString()}
                        </Text>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </>
        )}

        {/* 空状态 */}
        {documents.length === 0 && !uploading && (
          <div style={{ textAlign: 'center', padding: '40px', color: 'rgba(255, 255, 255, 0.6)' }}>
            <FileTextOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
            <Text style={{ color: 'rgba(255, 255, 255, 0.6)' }}>
              暂无上传的文档
            </Text>
          </div>
        )}
      </Card>

      {/* 文档预览模态框 */}
      <Modal
        title={`文档详情 - ${previewDocument?.filename}`}
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={null}
        width={800}
        style={{
          background: 'rgba(15, 15, 35, 0.95)',
          backdropFilter: 'blur(40px)'
        }}
      >
        {previewDocument && (
          <div>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <div>
                <Title level={4} style={{ color: 'rgba(255, 255, 255, 0.9)' }}>
                  基本信息
                </Title>
                <div style={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                  <p><strong>文件名:</strong> {previewDocument.filename}</p>
                  <p><strong>文件类型:</strong> {previewDocument.file_type}</p>
                  <p><strong>文件大小:</strong> {formatFileSize(previewDocument.file_size)}</p>
                  <p><strong>状态:</strong> {getStatusTag(previewDocument.status)}</p>
                  <p><strong>上传时间:</strong> {new Date(previewDocument.created_at).toLocaleString()}</p>
                  {previewDocument.processed_at && (
                    <p><strong>处理完成时间:</strong> {new Date(previewDocument.processed_at).toLocaleString()}</p>
                  )}
                  {previewDocument.chunk_count && (
                    <p><strong>分块数量:</strong> {previewDocument.chunk_count}</p>
                  )}
                </div>
              </div>
              
              {previewDocument.metadata && (
                <div>
                  <Title level={4} style={{ color: 'rgba(255, 255, 255, 0.9)' }}>
                    处理信息
                  </Title>
                  <pre style={{ 
                    background: 'rgba(255, 255, 255, 0.1)', 
                    padding: '12px', 
                    borderRadius: '8px',
                    color: 'rgba(255, 255, 255, 0.8)',
                    fontSize: '12px',
                    overflow: 'auto',
                    maxHeight: '300px'
                  }}>
                    {JSON.stringify(previewDocument.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </Space>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default DocumentProcessor
