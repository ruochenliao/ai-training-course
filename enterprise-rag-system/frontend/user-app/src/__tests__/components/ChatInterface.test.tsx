import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import ChatInterface from '../../components/ChatInterface'

// Mock API
jest.mock('../../utils/api', () => ({
  sendChatMessage: jest.fn(),
  getConversations: jest.fn(),
  getConversation: jest.fn(),
  deleteConversation: jest.fn()
}))

// Mock hooks
jest.mock('../../hooks/useChat', () => ({
  useChat: () => ({
    messages: [
      {
        id: '1',
        role: 'assistant',
        content: '您好！我是您的AI助手，有什么可以帮助您的吗？',
        timestamp: new Date()
      }
    ],
    conversations: [
      {
        id: 1,
        title: '测试对话',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        message_count: 1
      }
    ],
    currentConversationId: null,
    isLoading: false,
    error: null,
    sendMessage: jest.fn(),
    loadConversations: jest.fn(),
    loadConversation: jest.fn(),
    startNewConversation: jest.fn(),
    deleteConversation: jest.fn(),
    clearError: jest.fn(),
    stopGeneration: jest.fn(),
    resendLastMessage: jest.fn()
  })
}))

describe('ChatInterface', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('renders chat interface correctly', () => {
    render(<ChatInterface />)
    
    // 检查是否渲染了聊天界面的主要元素
    expect(screen.getByText('AI助手对话')).toBeInTheDocument()
    expect(screen.getByText('新建对话')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('输入您的问题...')).toBeInTheDocument()
  })

  test('displays initial message', () => {
    render(<ChatInterface />)
    
    expect(screen.getByText('您好！我是您的AI助手，有什么可以帮助您的吗？')).toBeInTheDocument()
  })

  test('shows conversation list', () => {
    render(<ChatInterface />)
    
    expect(screen.getByText('测试对话')).toBeInTheDocument()
  })

  test('allows typing in input field', () => {
    render(<ChatInterface />)
    
    const input = screen.getByPlaceholderText('输入您的问题...')
    fireEvent.change(input, { target: { value: '测试消息' } })
    
    expect(input).toHaveValue('测试消息')
  })

  test('send button is disabled when input is empty', () => {
    render(<ChatInterface />)
    
    const sendButton = screen.getByTitle('发送消息')
    expect(sendButton).toBeDisabled()
  })

  test('send button is enabled when input has text', () => {
    render(<ChatInterface />)
    
    const input = screen.getByPlaceholderText('输入您的问题...')
    const sendButton = screen.getByTitle('发送消息')
    
    fireEvent.change(input, { target: { value: '测试消息' } })
    expect(sendButton).not.toBeDisabled()
  })

  test('calls sendMessage when send button is clicked', async () => {
    const mockSendMessage = jest.fn()
    
    // 重新mock useChat hook
    jest.doMock('../../hooks/useChat', () => ({
      useChat: () => ({
        messages: [],
        conversations: [],
        currentConversationId: null,
        isLoading: false,
        error: null,
        sendMessage: mockSendMessage,
        loadConversations: jest.fn(),
        loadConversation: jest.fn(),
        startNewConversation: jest.fn(),
        deleteConversation: jest.fn(),
        clearError: jest.fn(),
        stopGeneration: jest.fn(),
        resendLastMessage: jest.fn()
      })
    }))

    render(<ChatInterface />)
    
    const input = screen.getByPlaceholderText('输入您的问题...')
    const sendButton = screen.getByTitle('发送消息')
    
    fireEvent.change(input, { target: { value: '测试消息' } })
    fireEvent.click(sendButton)
    
    await waitFor(() => {
      expect(mockSendMessage).toHaveBeenCalledWith('测试消息')
    })
  })

  test('sends message on Enter key press', async () => {
    const mockSendMessage = jest.fn()
    
    jest.doMock('../../hooks/useChat', () => ({
      useChat: () => ({
        messages: [],
        conversations: [],
        currentConversationId: null,
        isLoading: false,
        error: null,
        sendMessage: mockSendMessage,
        loadConversations: jest.fn(),
        loadConversation: jest.fn(),
        startNewConversation: jest.fn(),
        deleteConversation: jest.fn(),
        clearError: jest.fn(),
        stopGeneration: jest.fn(),
        resendLastMessage: jest.fn()
      })
    }))

    render(<ChatInterface />)
    
    const input = screen.getByPlaceholderText('输入您的问题...')
    
    fireEvent.change(input, { target: { value: '测试消息' } })
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13 })
    
    await waitFor(() => {
      expect(mockSendMessage).toHaveBeenCalledWith('测试消息')
    })
  })

  test('does not send message on Shift+Enter', () => {
    const mockSendMessage = jest.fn()
    
    jest.doMock('../../hooks/useChat', () => ({
      useChat: () => ({
        messages: [],
        conversations: [],
        currentConversationId: null,
        isLoading: false,
        error: null,
        sendMessage: mockSendMessage,
        loadConversations: jest.fn(),
        loadConversation: jest.fn(),
        startNewConversation: jest.fn(),
        deleteConversation: jest.fn(),
        clearError: jest.fn(),
        stopGeneration: jest.fn(),
        resendLastMessage: jest.fn()
      })
    }))

    render(<ChatInterface />)
    
    const input = screen.getByPlaceholderText('输入您的问题...')
    
    fireEvent.change(input, { target: { value: '测试消息' } })
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13, shiftKey: true })
    
    expect(mockSendMessage).not.toHaveBeenCalled()
  })

  test('shows loading state', () => {
    jest.doMock('../../hooks/useChat', () => ({
      useChat: () => ({
        messages: [],
        conversations: [],
        currentConversationId: null,
        isLoading: true,
        error: null,
        sendMessage: jest.fn(),
        loadConversations: jest.fn(),
        loadConversation: jest.fn(),
        startNewConversation: jest.fn(),
        deleteConversation: jest.fn(),
        clearError: jest.fn(),
        stopGeneration: jest.fn(),
        resendLastMessage: jest.fn()
      })
    }))

    render(<ChatInterface />)
    
    // 检查是否显示加载动画
    expect(screen.getByTestId('loading-dots')).toBeInTheDocument()
  })

  test('shows error message', () => {
    jest.doMock('../../hooks/useChat', () => ({
      useChat: () => ({
        messages: [],
        conversations: [],
        currentConversationId: null,
        isLoading: false,
        error: '发送消息失败',
        sendMessage: jest.fn(),
        loadConversations: jest.fn(),
        loadConversation: jest.fn(),
        startNewConversation: jest.fn(),
        deleteConversation: jest.fn(),
        clearError: jest.fn(),
        stopGeneration: jest.fn(),
        resendLastMessage: jest.fn()
      })
    }))

    render(<ChatInterface />)
    
    expect(screen.getByText('发送消息失败')).toBeInTheDocument()
  })

  test('handles file upload', () => {
    render(<ChatInterface />)
    
    const fileInput = screen.getByTestId('file-input')
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' })
    
    fireEvent.change(fileInput, { target: { files: [file] } })
    
    // 验证文件上传处理逻辑
    expect(fileInput.files).toHaveLength(1)
    expect(fileInput.files[0]).toBe(file)
  })

  test('knowledge base selector works', () => {
    render(<ChatInterface />)
    
    const selector = screen.getByDisplayValue('全部知识库')
    fireEvent.change(selector, { target: { value: '1' } })
    
    expect(selector).toHaveValue('1')
  })

  test('new conversation button works', () => {
    const mockStartNewConversation = jest.fn()
    
    jest.doMock('../../hooks/useChat', () => ({
      useChat: () => ({
        messages: [],
        conversations: [],
        currentConversationId: null,
        isLoading: false,
        error: null,
        sendMessage: jest.fn(),
        loadConversations: jest.fn(),
        loadConversation: jest.fn(),
        startNewConversation: mockStartNewConversation,
        deleteConversation: jest.fn(),
        clearError: jest.fn(),
        stopGeneration: jest.fn(),
        resendLastMessage: jest.fn()
      })
    }))

    render(<ChatInterface />)
    
    const newChatButton = screen.getByText('新建对话')
    fireEvent.click(newChatButton)
    
    expect(mockStartNewConversation).toHaveBeenCalled()
  })
})
