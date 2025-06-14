import React, {useState} from 'react'
import {Button, Card, Divider, Input, message, Space, Typography} from 'antd'
import {chatApi} from '../../api/chat'

const { TextArea } = Input
const { Title, Text, Paragraph } = Typography

/**
 * 聊天API测试页面
 * 用于验证前后端联调是否正常
 */
const ChatApiTest: React.FC = () => {
  const [testMessage, setTestMessage] = useState('你好，这是一个测试消息')
  const [conversationId, setConversationId] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<any[]>([])

  const addResult = (title: string, data: any, success = true) => {
    setResults((prev) => [
      ...prev,
      {
        title,
        data: JSON.stringify(data, null, 2),
        success,
        timestamp: new Date().toLocaleTimeString(),
      },
    ])
  }

  // 测试健康检查
  const testHealthCheck = async () => {
    setLoading(true)
    try {
      const result = await chatApi.healthCheck()
      addResult('健康检查', result)
      message.success('健康检查成功')
    } catch (error) {
      addResult('健康检查', error, false)
      message.error('健康检查失败')
    } finally {
      setLoading(false)
    }
  }

  // 测试获取配置
  const testGetConfig = async () => {
    setLoading(true)
    try {
      const result = await chatApi.getChatConfig()
      addResult('获取配置', result)
      message.success('获取配置成功')
    } catch (error) {
      addResult('获取配置', error, false)
      message.error('获取配置失败')
    } finally {
      setLoading(false)
    }
  }

  // 测试创建对话
  const testCreateConversation = async () => {
    setLoading(true)
    try {
      const result = await chatApi.createConversation('测试对话')
      setConversationId(result.conversation_id)
      addResult('创建对话', result)
      message.success('创建对话成功')
    } catch (error) {
      addResult('创建对话', error, false)
      message.error('创建对话失败')
    } finally {
      setLoading(false)
    }
  }

  // 测试发送消息（非流式）
  const testSendMessage = async () => {
    if (!conversationId) {
      message.warning('请先创建对话')
      return
    }

    setLoading(true)
    try {
      const result = await chatApi.sendMessage({
        message: testMessage,
        conversation_id: conversationId,
      })
      addResult('发送消息（非流式）', result)
      message.success('发送消息成功')
    } catch (error) {
      addResult('发送消息（非流式）', error, false)
      message.error('发送消息失败')
    } finally {
      setLoading(false)
    }
  }

  // 测试流式发送消息
  const testSendMessageStream = async () => {
    if (!conversationId) {
      message.warning('请先创建对话')
      return
    }

    setLoading(true)
    try {
      const stream = await chatApi.sendMessageStream({
        message: testMessage,
        conversation_id: conversationId,
      })

      const reader = stream.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let fullContent = ''

      // eslint-disable-next-line no-constant-condition
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim()
            if (data === '[DONE]') {
              addResult('流式消息完成', { fullContent })
              message.success('流式消息发送成功')
              return
            }

            try {
              const parsed = JSON.parse(data)
              if (parsed.content) {
                fullContent += parsed.content
              }
              addResult('流式消息块', parsed)
            } catch (parseError) {
              console.error('解析流式数据失败:', parseError)
            }
          }
        }
      }
    } catch (error) {
      addResult('发送消息（流式）', error, false)
      message.error('流式发送消息失败')
    } finally {
      setLoading(false)
    }
  }

  // 测试获取对话列表
  const testGetConversations = async () => {
    setLoading(true)
    try {
      const result = await chatApi.getConversations()
      addResult('获取对话列表', result)
      message.success('获取对话列表成功')
    } catch (error) {
      addResult('获取对话列表', error, false)
      message.error('获取对话列表失败')
    } finally {
      setLoading(false)
    }
  }

  // 测试获取消息历史
  const testGetMessages = async () => {
    if (!conversationId) {
      message.warning('请先创建对话')
      return
    }

    setLoading(true)
    try {
      const result = await chatApi.getConversationMessages(conversationId)
      addResult('获取消息历史', result)
      message.success('获取消息历史成功')
    } catch (error) {
      addResult('获取消息历史', error, false)
      message.error('获取消息历史失败')
    } finally {
      setLoading(false)
    }
  }

  // 清空结果
  const clearResults = () => {
    setResults([])
  }

  return (
    <div className='p-6'>
      <Title level={2}>聊天API测试</Title>
      <Paragraph>这个页面用于测试智能客服聊天API的各个功能，确保前后端联调正常工作。</Paragraph>

      <Card title='测试控制' className='mb-4'>
        <Space direction='vertical' style={{ width: '100%' }}>
          <div>
            <Text strong>测试消息：</Text>
            <TextArea value={testMessage} onChange={(e) => setTestMessage(e.target.value)} placeholder='输入测试消息' rows={2} className='mt-2' />
          </div>

          <div>
            <Text strong>当前对话ID：</Text>
            <Text code>{conversationId || '未创建'}</Text>
          </div>

          <Space wrap>
            <Button onClick={testHealthCheck} loading={loading}>
              健康检查
            </Button>
            <Button onClick={testGetConfig} loading={loading}>
              获取配置
            </Button>
            <Button onClick={testCreateConversation} loading={loading} type='primary'>
              创建对话
            </Button>
            <Button onClick={testSendMessage} loading={loading} disabled={!conversationId}>
              发送消息（非流式）
            </Button>
            <Button onClick={testSendMessageStream} loading={loading} disabled={!conversationId}>
              发送消息（流式）
            </Button>
            <Button onClick={testGetConversations} loading={loading}>
              获取对话列表
            </Button>
            <Button onClick={testGetMessages} loading={loading} disabled={!conversationId}>
              获取消息历史
            </Button>
            <Button onClick={clearResults} danger>
              清空结果
            </Button>
          </Space>
        </Space>
      </Card>

      <Card title='测试结果' className='mb-4'>
        <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
          {results.length === 0 ? (
            <Text type='secondary'>暂无测试结果</Text>
          ) : (
            results.map((result, index) => (
              <div key={index} className='mb-4'>
                <div className='flex items-center justify-between mb-2'>
                  <Text strong className={result.success ? 'text-green-600' : 'text-red-600'}>
                    {result.title}
                  </Text>
                  <Text type='secondary' className='text-sm'>
                    {result.timestamp}
                  </Text>
                </div>
                <pre className='bg-gray-100 p-3 rounded text-sm overflow-x-auto'>{result.data}</pre>
                {index < results.length - 1 && <Divider />}
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  )
}

export default ChatApiTest
