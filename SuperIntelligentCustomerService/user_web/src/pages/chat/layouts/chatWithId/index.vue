<!-- 每个回话对应的聊天内容 -->
<script setup lang="ts">
import type { AnyObject } from 'typescript-api-pro';
import type { Sender } from 'vue-element-plus-x';
import type { BubbleProps } from 'vue-element-plus-x/types/Bubble';
import type { BubbleListInstance } from 'vue-element-plus-x/types/BubbleList';
import type { FilesCardProps } from 'vue-element-plus-x/types/FilesCard';
import type { ThinkingStatus } from 'vue-element-plus-x/types/Thinking';
import { useHookFetch } from 'hook-fetch/vue';
import { useRoute } from 'vue-router';
import { sendStream, parseStreamResponse } from '@/api';
import FilesSelect from '@/components/FilesSelect/index.vue';
import ModelSelect from '@/components/ModelSelect/index.vue';
import { useChatStore } from '@/stores/modules/chat';
import { useFilesStore } from '@/stores/modules/files';
import { useModelStore } from '@/stores/modules/model';
import { useUserStore } from '@/stores/modules/user';

type MessageItem = BubbleProps & {
  key: number;
  role: 'ai' | 'user' | 'system';
  avatar: string;
  thinkingStatus?: ThinkingStatus;
  thinlCollapse?: boolean;
};

const route = useRoute();
const chatStore = useChatStore();
const modelStore = useModelStore();
const filesStore = useFilesStore();
const userStore = useUserStore();

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
// 记录进入思考中
let isThinking = false;

watch(
  () => route.params?.id,
  async (_id_) => {
    if (_id_) {
      if (_id_ !== 'not_login') {
        // 判断的当前会话id是否有聊天记录，有缓存则直接赋值展示
        if (chatStore.chatMap[`${_id_}`] && chatStore.chatMap[`${_id_}`].length) {
          bubbleItems.value = chatStore.chatMap[`${_id_}`] as MessageItem[];
          // 滚动到底部
          setTimeout(() => {
            bubbleListRef.value!.scrollToBottom();
          }, 350);
          return;
        }

        // 无缓存则请求聊天记录
        await chatStore.requestChatList(`${_id_}`);
        // 请求聊天记录后，赋值回显，并滚动到底部
        bubbleItems.value = chatStore.chatMap[`${_id_}`] as MessageItem[];

        // 滚动到底部
        setTimeout(() => {
          bubbleListRef.value!.scrollToBottom();
        }, 350);
      }

      // 如果本地有发送内容 ，则直接发送
      const v = localStorage.getItem('chatContent');
      if (v) {
        // 发送消息
        console.log('发送消息 v', v);
        setTimeout(() => {
          startSSE(v);
        }, 350);

        localStorage.removeItem('chatContent');
      }
    }
  },
  { immediate: true, deep: true },
);

// 封装数据处理逻辑
function handleDataChunk(chunk: AnyObject) {
  try {
    console.log('收到流式数据:', chunk);

    // 处理OpenAI格式的流式数据
    if (!chunk || !chunk.choices || !chunk.choices[0]) {
      return;
    }

    const choice = chunk.choices[0];

    const delta = choice.delta;

    if (!delta) {
      return;
    }

    // 获取最后一条消息（AI回复）
    if (!bubbleItems.value || bubbleItems.value.length === 0) {
      return;
    }
    const lastMessage = bubbleItems.value[bubbleItems.value.length - 1];
    if (!lastMessage || (lastMessage.role !== 'assistant' && lastMessage.role !== 'system')) {
      return;
    }

    // 处理思考内容（reasoning_content）
    const reasoningChunk = delta.reasoning_content;
    if (reasoningChunk) {
      // 开始思考链状态
      lastMessage.thinkingStatus = 'thinking';
      lastMessage.loading = true;
      lastMessage.thinlCollapse = true;
      lastMessage.reasoning_content = (lastMessage.reasoning_content || '') + reasoningChunk;
    }

    // 处理正常内容
    const contentChunk = delta.content;
    if (contentChunk) {
      // 检查是否包含思考标签
      const thinkStart = contentChunk.includes('<think>');
      const thinkEnd = contentChunk.includes('</think>');

      if (thinkStart) {
        isThinking = true;
      }
      if (thinkEnd) {
        isThinking = false;
      }

      if (isThinking) {
        // 处理思考内容
        lastMessage.thinkingStatus = 'thinking';
        lastMessage.loading = true;
        lastMessage.thinlCollapse = true;
        const thinkingContent = contentChunk
          .replace('<think>', '')
          .replace('</think>', '');
        lastMessage.reasoning_content = (lastMessage.reasoning_content || '') + thinkingContent;
      } else {
        // 处理正常回复内容
        lastMessage.thinkingStatus = 'end';
        lastMessage.loading = false;
        lastMessage.typing = true;
        lastMessage.content = (lastMessage.content || '') + contentChunk;
      }
    }

    // 处理完成状态
    if (choice.finish_reason === 'stop' || choice.finish_reason === 'end' || choice.finish_reason === 'complete') {
      lastMessage.loading = false;
      lastMessage.typing = false;
      lastMessage.thinkingStatus = 'end';
    }

    // 自动滚动到底部
    nextTick(() => {
      bubbleListRef.value?.scrollToBottom();
    });

  } catch (err) {
    console.error('解析流式数据时出错:', err);
  }
}

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

    // 添加用户输入的消息
    inputValue.value = '';
    addMessage(chatContent, true);
    addMessage('', false);

    // 滚动到底部
    bubbleListRef.value?.scrollToBottom();

    // 准备发送的消息数据，匹配后端SendDTO格式
    // 只发送当前用户的消息，避免发送整个对话历史
    const sendData = {
      messages: [
        {
          role: 'user',
          content: chatContent,
        }
      ],
      sessionId: route.params?.id !== 'not_login' ? String(route.params?.id) : '1', // 确保有sessionId
      model: modelStore.currentModelInfo.modelName ?? 'deepseek-chat',
      stream: true,
    };

    console.log('发送流式聊天请求:', sendData);

    // 使用新的流式API
    const stream = await sendStream(sendData);

    // 解析流式响应
    for await (const chunk of parseStreamResponse(stream)) {
      // 检查是否被中断
      if (abortController?.signal.aborted) {
        console.log('流式聊天被用户中断');
        break;
      }
      handleDataChunk(chunk);
    }
  }
  catch (err) {
    console.error('流式聊天错误:', err);
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
    console.log('流式数据接收完毕');
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
  }
  .chat-defaul-sender {
    width: 100%;
    margin-bottom: 22px;
  }
}
</style>
