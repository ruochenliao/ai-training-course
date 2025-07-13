<!-- 每个回话对应的聊天内容 -->
<script setup lang="ts">
import type {Sender} from 'vue-element-plus-x';
import {XMarkdown} from 'vue-element-plus-x';
import type {BubbleProps} from 'vue-element-plus-x/types/Bubble';
import type {BubbleListInstance} from 'vue-element-plus-x/types/BubbleList';
import type {FilesCardProps} from 'vue-element-plus-x/types/FilesCard';
import type {ThinkingStatus} from 'vue-element-plus-x/types/Thinking';
import {useRoute} from 'vue-router';
import {parseStreamResponse, sendStream} from '@/api';
import FilesSelect from '@/components/FilesSelect/index.vue';
import ModelSelect from '@/components/ModelSelect/index.vue';
import {useChatStore} from '@/stores/modules/chat';
import {useFilesStore} from '@/stores/modules/files';
import {useUserStore} from '@/stores/modules/user';
import {useModelStore} from '@/stores/modules/model';

type MessageItem = BubbleProps & {
  key: number;
  role: 'ai' | 'user' | 'system' | 'assistant';
  avatar: string;
  thinkingStatus?: ThinkingStatus;
  thinlCollapse?: boolean;
};

const route = useRoute();
const chatStore = useChatStore();
const filesStore = useFilesStore();
const userStore = useUserStore();
const modelStore = useModelStore();

// 用户头像
const avatar = computed(() => {
  const userInfo = userStore.userInfo;
  return userInfo?.avatar || 'https://avatars.githubusercontent.com/u/76239030?v=4';
});

const inputValue = ref('');
const senderRef = ref<InstanceType<typeof Sender> | null>(null);
const bubbleItems = ref<MessageItem[]>([]);
const bubbleListRef = ref<BubbleListInstance | null>(null);

// 流式聊天状态管理
const isLoading = ref(false);
let abortController: AbortController | null = null;

// 验证会话ID是否有效
function isValidSessionId(id: string | string[]): boolean {
  if (!id || Array.isArray(id)) return false;
  const sessionId = String(id).trim();
  if (sessionId === 'not_login' || sessionId === 'undefined' || sessionId === 'null' || sessionId === '') {
    return false;
  }
  const numId = parseInt(sessionId, 10);
  return !isNaN(numId) && numId > 0;
}

watch(
  () => route.params?.id,
  async (_id_) => {
    if (_id_) {
      // 验证会话ID
      if (!isValidSessionId(_id_)) {
        // 清空聊天记录
        bubbleItems.value = [];
        return;
      }

      const sessionId = String(_id_);

      // 判断的当前会话id是否有聊天记录，有缓存则直接赋值展示
      if (chatStore.chatMap[sessionId] && chatStore.chatMap[sessionId].length) {
        bubbleItems.value = chatStore.chatMap[sessionId] as MessageItem[];
        // 滚动到底部
        setTimeout(() => {
          bubbleListRef.value!.scrollToBottom();
        }, 350);
        return;
      }

      // 无缓存则请求聊天记录
      try {
        await chatStore.requestChatList(sessionId);
        // 请求聊天记录后，赋值回显，并滚动到底部
        bubbleItems.value = chatStore.chatMap[sessionId] as MessageItem[] || [];

        // 滚动到底部
        setTimeout(() => {
          bubbleListRef.value!.scrollToBottom();
        }, 350);
      } catch (error) {
        bubbleItems.value = [];
      }

      // 如果本地有发送内容 ，则直接发送
      const v = localStorage.getItem('chatContent');
      if (v) {
        setTimeout(() => {
          startSSE(v);
        }, 350);
        localStorage.removeItem('chatContent');
      }
    }
  },
  { immediate: true, deep: true },
);

// 这个函数已被简化的流式处理逻辑替代，暂时保留以备后用
// function handleDataChunk(chunk: AnyObject) { ... }

// 封装错误处理逻辑
function handleError(err: any) {
  console.error('Fetch error:', err);
}

async function startSSE(chatContent: string) {
  if (isLoading.value) {
    console.warn('正在处理中，请稍等...');
    return;
  }

  try {
    isLoading.value = true;
    abortController = new AbortController();

    // 验证会话ID
    const currentSessionId = route.params?.id;
    if (!isValidSessionId(currentSessionId)) {
      handleError(new Error('无效的会话ID，请刷新页面重试'));
      return;
    }

    // 准备发送的消息数据，匹配后端ChatSendRequest格式（在清除文件列表之前提取文件）
    const sendData = {
      message: chatContent,
      sessionId: String(currentSessionId), // 确保有效的sessionId
      model_name: modelStore.currentModelInfo?.model_name, // 添加选中的模型
      files: (filesStore.filesList || []).map(item => item.file) // 提取File对象
    };

    // 添加用户输入的消息
    inputValue.value = '';
    // 清除文件列表（在提取文件对象之后）
    filesStore.clearAllFiles();
    addMessage(chatContent, true);
    addMessage('', false);

    // 滚动到底部
    bubbleListRef.value?.scrollToBottom();



    // 使用新的流式API
    const stream = await sendStream(sendData);

    let currentMessage = '';
    let isFirstChunk = true;
    let processingStatus = '';
    let messageBuffer = ''; // 用于缓冲内容，减少渲染闪烁
    let chunkCount = 0; // 记录接收到的数据块数量

    console.log('🚀 开始新的流式处理，所有变量已重置');

    // 解析优化的流式响应
    for await (const event of parseStreamResponse(stream)) {
      // 检查是否被中断
      if (abortController?.signal.aborted) {
        break;
      }

      // 处理不同类型的流式事件
      switch (event.type) {
        case 'start':
          processingStatus = '开始处理...';
          console.log('🚀 开始处理用户请求');
          break;

        case 'processing':
          processingStatus = event.data?.message || 'AI正在思考中...';
          console.log('🤔 AI思考中:', processingStatus);
          break;

        case 'content':
          // 累积内容
          if (event.data) {
            chunkCount++;
            messageBuffer += event.data;

            // 调试信息：记录每个数据块
            console.log(`📦 接收数据块 ${chunkCount}:`, {
              chunkIndex: event.chunk_index,
              chunkLength: event.data.length,
              totalBufferLength: messageBuffer.length,
              chunkPreview: event.data.substring(0, 50) + (event.data.length > 50 ? '...' : ''),
              isFirstChunk: chunkCount === 1
            });

            // 特别记录前几个数据块的完整内容
            if (chunkCount <= 3) {
              console.log(`🔍 数据块 ${chunkCount} 完整内容:`, JSON.stringify(event.data));
            }

            // 实时更新UI，使用防抖机制减少渲染频率
            currentMessage = messageBuffer;

            // 更新最后一条消息（AI回复）
            if (bubbleItems.value && bubbleItems.value.length > 0) {
              const lastMessage = bubbleItems.value[bubbleItems.value.length - 1];
              if (lastMessage && (lastMessage.role === 'assistant' || lastMessage.role === 'system')) {
                lastMessage.content = currentMessage;
                lastMessage.isMarkdown = true; // 标记为Markdown内容
                lastMessage.loading = false;
                lastMessage.typing = true;

                // 首次收到内容时滚动到底部
                if (isFirstChunk) {
                  isFirstChunk = false;
                  console.log('🎯 首次内容，缓冲区长度:', messageBuffer.length);
                  console.log('🎯 首次内容预览:', messageBuffer.substring(0, 100));
                  await nextTick();
                  bubbleListRef.value?.scrollToBottom();
                }
              }
            }

            // 优化滚动策略：减少滚动频率，提高性能
            if (event.chunk_index && event.chunk_index % 30 === 0) {
              await nextTick();
              bubbleListRef.value?.scrollToBottom();
            }
          }
          break;

        case 'complete':
          // 确保最终内容完整 - 使用后端提供的完整内容
          if (event.data?.full_content) {
            currentMessage = event.data.full_content;
            messageBuffer = event.data.full_content;
            console.log('🔍 使用后端完整内容，长度:', event.data.full_content.length);
            console.log('🔍 完整内容预览:', event.data.full_content.substring(0, 200) + '...');
          } else {
            currentMessage = messageBuffer;
            console.log('🔍 使用缓冲区内容，长度:', messageBuffer.length);
            console.log('🔍 缓冲区内容预览:', messageBuffer.substring(0, 200) + '...');
          }

          if (bubbleItems.value && bubbleItems.value.length > 0) {
            const lastMessage = bubbleItems.value[bubbleItems.value.length - 1];
            if (lastMessage && (lastMessage.role === 'assistant' || lastMessage.role === 'system')) {
              lastMessage.content = currentMessage;
              lastMessage.isMarkdown = true;
              lastMessage.loading = false;
              lastMessage.typing = false;
              console.log('🔍 最终设置的消息内容长度:', lastMessage.content.length);
            }
          }

          console.log('✅ 处理完成:', {
            totalChunks: event.data?.total_chunks,
            processingTime: event.data?.processing_time,
            wordCount: event.data?.word_count,
            finalContentLength: currentMessage.length,
            bufferLength: messageBuffer.length
          });

          // 最终滚动到底部
          await nextTick();
          bubbleListRef.value?.scrollToBottom();
          break;

        case 'error':
          console.error('❌ 处理出错:', event.data);
          // 显示错误信息
          if (bubbleItems.value && bubbleItems.value.length > 0) {
            const lastMessage = bubbleItems.value[bubbleItems.value.length - 1];
            if (lastMessage && (lastMessage.role === 'assistant' || lastMessage.role === 'system')) {
              lastMessage.content = event.data?.message || '处理出现错误，请重试';
              lastMessage.isMarkdown = false;
              lastMessage.loading = false;
              lastMessage.typing = false;
            }
          }
          break;

        case 'done':
          console.log('🏁 流式处理结束');
          processingStatus = '';
          // 最终滚动到底部
          await nextTick();
          bubbleListRef.value?.scrollToBottom();
          break;

        default:
          // 兼容旧版本的字符串格式
          if (typeof event === 'string' && event.trim()) {
            messageBuffer += event;
            currentMessage = messageBuffer;

            if (bubbleItems.value && bubbleItems.value.length > 0) {
              const lastMessage = bubbleItems.value[bubbleItems.value.length - 1];
              if (lastMessage && (lastMessage.role === 'assistant' || lastMessage.role === 'system')) {
                lastMessage.content = currentMessage;
                lastMessage.isMarkdown = true;
                lastMessage.loading = false;
                lastMessage.typing = true;

                // 自动滚动到底部
                nextTick(() => {
                  bubbleListRef.value?.scrollToBottom();
                });
              }
            }
          }
          console.log('📨 收到其他事件:', event);
      }

      // 优化的延迟机制：根据内容类型调整延迟时间
      const delay = event.type === 'content' ? 20 : 10; // 内容块稍微慢一点，其他事件快一点
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  catch (err) {
    handleError(err);

    // 如果流式聊天失败，显示错误消息
    if (bubbleItems.value && bubbleItems.value.length > 0) {
      const lastMessage = bubbleItems.value[bubbleItems.value.length - 1];
      if (lastMessage && (lastMessage.role === 'assistant' || lastMessage.role === 'system')) {
        lastMessage.content = '抱歉，我暂时无法回复您的消息，请稍后重试。';
        lastMessage.loading = false;
        lastMessage.typing = false;
      }
    }
  }
  finally {
    isLoading.value = false;
    abortController = null;

    // 停止打字器状态
    if (bubbleItems.value && bubbleItems.value.length > 0) {
      const lastMessage = bubbleItems.value[bubbleItems.value.length - 1];
      if (lastMessage) {
        lastMessage.typing = false;
        lastMessage.loading = false;
      }
    }
  }
}

// 中断请求
async function cancelSSE() {
  // 中断流式请求
  if (abortController) {
    abortController.abort();
    abortController = null;
  }
  isLoading.value = false;

  // 结束最后一条消息打字状态
  if (bubbleItems.value && bubbleItems.value.length > 0) {
    const lastMessage = bubbleItems.value[bubbleItems.value.length - 1];
    if (lastMessage) {
      lastMessage.typing = false;
    }
  }
}

// 添加消息 - 维护聊天记录
function addMessage(message: string, isUser: boolean) {
  // 确保bubbleItems.value存在且为数组
  if (!bubbleItems.value || !Array.isArray(bubbleItems.value)) {
    bubbleItems.value = [];
  }

  const i = bubbleItems.value.length;
  const obj: MessageItem = {
    key: i,
    avatar: isUser
      ? avatar.value
      : 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png',
    avatarSize: '32px',
    role: isUser ? 'user' : 'assistant',
    placement: isUser ? 'end' : 'start',
    isMarkdown: !isUser,
    loading: !isUser,
    content: message || '',
    reasoning_content: '',
    thinkingStatus: 'start',
    thinlCollapse: false,
  };
  bubbleItems.value.push(obj);
}

// 展开收起 事件展示
function handleChange(payload: { value: boolean; status: ThinkingStatus }) {
  console.log('value', payload.value, 'status', payload.status);
}

function handleDeleteCard(_item: FilesCardProps, index: number) {
  filesStore.deleteFileByIndex(index);
}

watch(
  () => filesStore.filesList.length,
  (val) => {
    if (val > 0) {
      nextTick(() => {
        senderRef.value?.openHeader();
      });
    }
    else {
      nextTick(() => {
        senderRef.value?.closeHeader();
      });
    }
  },
);
</script>

<template>
  <div class="chat-with-id-container">
    <div class="chat-warp">
      <BubbleList ref="bubbleListRef" :list="bubbleItems" max-height="calc(100vh - 240px)">
        <template #header="{ item }">
          <Thinking
            v-if="item.reasoning_content" v-model="item.thinlCollapse" :content="item.reasoning_content"
            :status="item.thinkingStatus" class="thinking-chain-warp" @change="handleChange"
          />
        </template>
        <template #content="{ item }">
          <!-- 如果是助手消息且标记为 Markdown，使用优化的 XMarkdown 组件渲染 -->
          <XMarkdown
            v-if="item.isMarkdown && item.role === 'assistant'"
            :markdown="item.content"
            :enable-latex="true"
            :enable-breaks="true"
            :allow-html="false"
            :themes="{
              light: 'vitesse-light',
              dark: 'vitesse-dark'
            }"
            :default-theme-mode="'light'"
            :need-view-code-btn="true"
            :enable-copy="true"
            :enable-line-numbers="false"
            :enable-word-wrap="true"
            class="enhanced-markdown-content optimized-rendering"
          />
          <!-- 否则使用普通文本显示 -->
          <div v-else class="text-content">
            {{ item.content }}
          </div>
        </template>
      </BubbleList>

      <Sender
        ref="senderRef" v-model="inputValue" class="chat-defaul-sender" :auto-size="{
          maxRows: 6,
          minRows: 2,
        }" variant="updown" clearable allow-speech :loading="isLoading" @submit="startSSE" @cancel="cancelSSE"
      >
        <template #header>
          <div class="sender-header p-12px pt-6px pb-0px">
            <Attachments :items="filesStore.filesList" :hide-upload="true" @delete-card="handleDeleteCard">
              <template #prev-button="{ show, onScrollLeft }">
                <div
                  v-if="show"
                  class="prev-next-btn left-8px flex-center w-22px h-22px rounded-8px border-1px border-solid border-[rgba(0,0,0,0.08)] c-[rgba(0,0,0,.4)] hover:bg-#f3f4f6 bg-#fff font-size-10px"
                  @click="onScrollLeft"
                >
                  <el-icon>
                    <ArrowLeftBold />
                  </el-icon>
                </div>
              </template>

              <template #next-button="{ show, onScrollRight }">
                <div
                  v-if="show"
                  class="prev-next-btn right-8px flex-center w-22px h-22px rounded-8px border-1px border-solid border-[rgba(0,0,0,0.08)] c-[rgba(0,0,0,.4)] hover:bg-#f3f4f6 bg-#fff font-size-10px"
                  @click="onScrollRight"
                >
                  <el-icon>
                    <ArrowRightBold />
                  </el-icon>
                </div>
              </template>
            </Attachments>
          </div>
        </template>
        <template #prefix>
          <div class="flex-1 flex items-center gap-8px flex-none w-fit overflow-hidden">
            <FilesSelect />
            <ModelSelect />
          </div>
        </template>
      </Sender>
    </div>
  </div>
</template>

<style scoped lang="scss">
.chat-with-id-container {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 800px;
  height: 100%;
  .chat-warp {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    width: 100%;
    height: calc(100vh - 60px);
    .thinking-chain-warp {
      margin-bottom: 12px;
    }
  }
  :deep() {
    .el-bubble-list {
      padding-top: 24px;
    }
    .el-bubble {
      padding: 0 12px;
      padding-bottom: 24px;
    }
    .el-typewriter {
      overflow: hidden;
      border-radius: 12px;
    }
    .markdown-body {
      background-color: transparent;
    }

    // Markdown 内容样式优化
    .markdown-content {
      // 基础样式
      font-size: 14px;
      line-height: 1.6;
      color: #24292f;
      word-wrap: break-word;
      max-width: 100%;
      overflow-wrap: break-word;

      // 图片样式
      :deep(img) {
        max-width: 100%;
        height: auto;
        border-radius: 8px;
        margin: 8px 0;
        display: block;
      }

      // 代码块容器样式 - 使用 :deep() 来穿透 XMarkdown 组件的样式
      :deep(.shiki) {
        background-color: #f6f8fa !important;
        border: 1px solid #d0d7de;
        border-radius: 6px;
        padding: 16px;
        margin: 12px 0;
        overflow-x: auto;
        font-size: 13px;
        line-height: 1.45;
        max-width: 100%;

        code {
          background: transparent !important;
          padding: 0;
          border-radius: 0;
          font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
        }
      }

      // 行内代码样式
      :deep(code:not(.shiki code)) {
        background-color: rgba(175, 184, 193, 0.2);
        padding: 2px 4px;
        border-radius: 3px;
        font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
        font-size: 85%;
        color: #d73a49;
      }

      // 表格样式
      :deep(table) {
        border-collapse: collapse;
        width: 100%;
        margin: 16px 0;
        border-spacing: 0;
        font-size: 13px;

        th, td {
          border: 1px solid #d0d7de;
          padding: 6px 13px;
          text-align: left;
        }

        th {
          background-color: #f6f8fa;
          font-weight: 600;
        }

        tr:nth-child(2n) {
          background-color: #f6f8fa;
        }
      }

      // 引用样式
      :deep(blockquote) {
        border-left: 4px solid #d0d7de;
        padding: 0 16px;
        margin: 16px 0;
        color: #656d76;

        p {
          margin: 8px 0;
        }
      }

      // 列表样式
      :deep(ul), :deep(ol) {
        padding-left: 24px;
        margin: 16px 0;

        li {
          margin: 4px 0;
        }
      }

      // 标题样式
      :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
        margin: 24px 0 16px 0;
        font-weight: 600;
        line-height: 1.25;

        &:first-child {
          margin-top: 0;
        }
      }

      :deep(h1) { font-size: 1.8em; }
      :deep(h2) { font-size: 1.5em; }
      :deep(h3) { font-size: 1.25em; }
      :deep(h4) { font-size: 1em; }
      :deep(h5) { font-size: 0.875em; }
      :deep(h6) { font-size: 0.85em; }

      // 段落样式
      :deep(p) {
        margin: 16px 0;
        line-height: 1.6;

        &:first-child {
          margin-top: 0;
        }

        &:last-child {
          margin-bottom: 0;
        }
      }

      // 水平分割线
      :deep(hr) {
        height: 1px;
        background-color: #d0d7de;
        border: none;
        margin: 24px 0;
      }

      // 链接样式
      :deep(a) {
        color: #0969da;
        text-decoration: none;

        &:hover {
          text-decoration: underline;
        }
      }

      // 强调样式
      :deep(strong), :deep(b) {
        font-weight: 600;
      }

      :deep(em), :deep(i) {
        font-style: italic;
      }

      // 删除线
      :deep(del), :deep(s) {
        text-decoration: line-through;
      }

      // 水平分割线
      hr {
        height: 1px;
        background-color: #d0d7de;
        border: none;
        margin: 24px 0;
      }

      // 链接样式
      a {
        color: #0969da;
        text-decoration: none;

        &:hover {
          text-decoration: underline;
        }
      }

      // 强调样式
      strong, b {
        font-weight: 600;
      }

      em, i {
        font-style: italic;
      }

      // 删除线
      del, s {
        text-decoration: line-through;
      }
    }

    // 普通文本内容样式
    .text-content {
      line-height: 1.6;
      word-wrap: break-word;
    }

    // 增强的Markdown内容样式优化
    .enhanced-markdown-content {
      width: 100%;
      max-width: 100%;
      overflow-wrap: break-word;
      word-wrap: break-word;

      // 代码块样式优化
      :deep(pre) {
        max-width: 100% !important;
        overflow-x: auto !important;
        white-space: pre !important;
        background-color: #f6f8fa !important;
        border: 1px solid #d0d7de !important;
        border-radius: 8px !important;
        padding: 16px !important;
        margin: 12px 0 !important;
        font-size: 13px !important;
        line-height: 1.45 !important;
        font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', monospace !important;

        code {
          background: transparent !important;
          padding: 0 !important;
          border-radius: 0 !important;
          white-space: pre !important;
          word-wrap: normal !important;
        }
      }

      // 行内代码样式
      :deep(p code), :deep(li code), :deep(td code), :deep(th code) {
        background-color: rgba(175, 184, 193, 0.2) !important;
        padding: 2px 4px !important;
        border-radius: 4px !important;
        font-size: 0.9em !important;
        font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', monospace !important;
        white-space: nowrap !important;
      }

      // 图片样式优化
      :deep(img) {
        max-width: 100% !important;
        height: auto !important;
        border-radius: 8px !important;
        margin: 8px 0 !important;
        display: block !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
      }

      // 表格样式优化
      :deep(table) {
        border-collapse: collapse !important;
        width: 100% !important;
        margin: 16px 0 !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;

        th, td {
          border: 1px solid #d0d7de !important;
          padding: 8px 12px !important;
          text-align: left !important;
          word-wrap: break-word !important;
        }

        th {
          background-color: #f6f8fa !important;
          font-weight: 600 !important;
        }

        tr:nth-child(even) {
          background-color: #f6f8fa !important;
        }
      }
    }
  }
  .chat-defaul-sender {
    width: 100%;
    margin-bottom: 22px;
  }
}
</style>
