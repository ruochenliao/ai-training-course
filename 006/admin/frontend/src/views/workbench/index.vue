<template>
  <AppPage :show-footer="false">
    <div flex-1>
      <!-- 欢迎卡片 -->
      <n-card
        class="welcome-card"
        :bordered="false"
        content-style="padding: 24px"
        rounded-16
      >
        <div flex items-center justify-between>
          <div flex items-center>
            <div class="avatar-container">
              <img rounded-full width="80" :src="userStore.avatar" />
              <div class="avatar-status"></div>
            </div>
            <div ml-16>
              <p text-24 font-bold class="welcome-text">
                {{ $t('views.workbench.text_hello', { username: userStore.name }) }}
              </p>
              <p mt-5 text-16 op-70 class="welcome-subtext">
                {{ $t('views.workbench.text_welcome') }}
                <n-tag class="ml-2" type="success" size="small">在线</n-tag>
              </p>
              <div class="mt-4 flex gap-4">
                <n-button size="small" type="primary" secondary>
                  <template #icon>
                    <TheIcon icon="mdi:account-edit-outline" :size="16" />
                  </template>
                  个人信息
                </n-button>
                <n-button size="small" type="info" secondary>
                  <template #icon>
                    <TheIcon icon="mdi:bell-outline" :size="16" />
                  </template>
                  消息通知
                </n-button>
              </div>
            </div>
          </div>
          <div class="stat-cards">
            <n-grid :cols="3" :x-gap="16">
              <n-grid-item v-for="item in statisticData" :key="item.id">
                <n-card class="stat-card" :bordered="false">
                  <div class="stat-icon">
                    <TheIcon :icon="item.icon" :size="24" />
                  </div>
                  <div class="stat-value">{{ item.value }}</div>
                  <div class="stat-label">{{ item.label }}</div>
                </n-card>
              </n-grid-item>
            </n-grid>
          </div>
        </div>
      </n-card>

      <!-- 快捷操作和图表区域 -->
      <div class="mt-6 grid grid-cols-1 gap-6 md:grid-cols-3">
        <!-- 快捷操作 -->
        <n-card
          class="quick-actions-card"
          :bordered="false"
          title="智能体快捷访问"
          size="small"
          rounded-16
        >
          <div class="quick-actions-grid">
            <div
              v-for="(action, index) in quickActions"
              :key="index"
              class="quick-action-item"
              @click="handleQuickAction(action)"
            >
              <div class="quick-action-icon">
                <TheIcon :icon="action.icon" :size="24" />
              </div>
              <div class="quick-action-name">{{ action.name }}</div>
            </div>
          </div>
        </n-card>

        <!-- 活动图表 -->
        <n-card
          class="activity-card"
          :bordered="false"
          title="智能体调用趋势"
          size="small"
          rounded-16
        >
          <div class="chart-container" ref="activityChartRef"></div>
        </n-card>

        <!-- 系统状态 -->
        <n-card
          class="system-status-card"
          :bordered="false"
          title="系统资源监控"
          size="small"
          rounded-16
        >
          <div class="status-items">
            <div v-for="(status, index) in systemStatus" :key="index" class="status-item">
              <div class="status-label">{{ status.label }}</div>
              <div class="status-value-container">
                <n-progress
                  type="line"
                  :percentage="status.value"
                  :color="status.color"
                  :height="12"
                  :border-radius="6"
                  :show-indicator="false"
                />
                <span class="status-value">{{ status.value }}%</span>
              </div>
            </div>
          </div>
        </n-card>
      </div>

      <!-- 项目卡片 -->
      <n-card
        class="projects-card mt-6"
        :bordered="false"
        title="智能体项目"
        size="small"
        rounded-16
      >
        <template #header-extra>
          <n-button text type="primary">
            <template #icon>
              <TheIcon icon="mdi:dots-horizontal" :size="18" />
            </template>
            查看全部
          </n-button>
        </template>
        <div class="projects-grid">
          <n-card
            v-for="(project, i) in projects"
            :key="i"
            class="project-card"
            :bordered="false"
            :title="project.title"
            size="small"
          >
            <template #header-extra>
              <n-tag :type="project.status.type" size="small">{{ project.status.text }}</n-tag>
            </template>
            <p class="project-desc">{{ project.description }}</p>
            <div class="project-footer">
              <div class="project-progress">
                <n-progress
                  type="line"
                  :percentage="project.progress"
                  :color="project.progressColor"
                  :height="6"
                  :border-radius="3"
                  :show-indicator="false"
                />
              </div>
              <div class="project-meta">
                <div class="project-date">
                  <TheIcon icon="mdi:calendar-outline" :size="14" />
                  <span>{{ project.date }}</span>
                </div>
                <div class="project-members">
                  <div class="member-avatars">
                    <img
                      v-for="(member, j) in project.members"
                      :key="j"
                      :src="member.avatar"
                      :alt="member.name"
                      :title="member.name"
                    />
                  </div>
                </div>
              </div>
            </div>
          </n-card>
        </div>
      </n-card>
    </div>
  </AppPage>
</template>

<script setup>
import { useUserStore } from '@/store'
import { useI18n } from 'vue-i18n'
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  TitleComponent,
  LegendComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

// 注册必须的组件
echarts.use([
  LineChart,
  GridComponent,
  TooltipComponent,
  TitleComponent,
  LegendComponent,
  CanvasRenderer
])

const { t } = useI18n({ useScope: 'global' })
const userStore = useUserStore()
const router = useRouter()
const activityChartRef = ref(null)
let activityChart = null

// 统计数据
const statisticData = computed(() => [
  {
    id: 0,
    label: '智能体数量',
    value: '4',
    icon: 'mdi:robot'
  },
  {
    id: 1,
    label: '今日调用量',
    value: '1,286',
    icon: 'mdi:chart-line'
  },
  {
    id: 2,
    label: '知识库文档',
    value: '128',
    icon: 'mdi:file-document-multiple'
  },
])

// 快捷操作
const quickActions = [
  { name: '智能客服', icon: 'mdi:robot', path: '/customer/service' },
  { name: '数据分析', icon: 'mdi:database', path: '/data/analysis' },
  { name: '知识库', icon: 'mdi:book-open-page-variant', path: '/customer/knowledge' },
  { name: '文案创作', icon: 'mdi:file-document-edit', path: '/content/creation' },
  { name: '用户管理', icon: 'mdi:account-group', path: '/system/user' },
  { name: '系统设置', icon: 'mdi:cog', path: '/system/settings' },
]

// 系统状态
const systemStatus = [
  { label: 'CPU使用率', value: 42, color: '#18a058' },
  { label: '内存使用率', value: 68, color: '#2080f0' },
  { label: '存储空间', value: 76, color: '#f0a020' },
  { label: '网络带宽', value: 35, color: '#8a2be2' },
]

// 项目数据
const projects = [
  {
    title: '智能客服系统',
    description: '对接公司现有业务系统回答用户问题，基于智能体调用工具完成业务处理',
    status: { text: '进行中', type: 'info' },
    progress: 75,
    progressColor: '#2080f0',
    date: '2024-05-15',
    members: [
      { name: '张三', avatar: 'https://avatars.githubusercontent.com/u/54677442?v=4' },
      { name: '李四', avatar: 'https://avatars.githubusercontent.com/u/54677442?v=4' },
      { name: '王五', avatar: 'https://avatars.githubusercontent.com/u/54677442?v=4' },
    ]
  },
  {
    title: 'Text2SQL数据分析智能体',
    description: '将自然语言问题转换为SQL语句并执行，返回命令、解释、结果及图形化报表',
    status: { text: '已完成', type: 'success' },
    progress: 100,
    progressColor: '#18a058',
    date: '2024-04-20',
    members: [
      { name: '张三', avatar: 'https://avatars.githubusercontent.com/u/54677442?v=4' },
      { name: '李四', avatar: 'https://avatars.githubusercontent.com/u/54677442?v=4' },
    ]
  },
  {
    title: '企业级知识库问答智能体',
    description: '结合传统RAG、NanoGraphRAG、多模态RAG等技术为用户提供精确的知识召回并加工',
    status: { text: '进行中', type: 'info' },
    progress: 85,
    progressColor: '#2080f0',
    date: '2024-05-10',
    members: [
      { name: '张三', avatar: 'https://avatars.githubusercontent.com/u/54677442?v=4' },
      { name: '王五', avatar: 'https://avatars.githubusercontent.com/u/54677442?v=4' },
    ]
  },
  {
    title: '企业内部文案创作智能体',
    description: '根据用户意图选择合适文案模板，借助RAG与LLM完成高质量文案生成',
    status: { text: '规划中', type: 'warning' },
    progress: 40,
    progressColor: '#f0a020',
    date: '2024-05-30',
    members: [
      { name: '李四', avatar: 'https://avatars.githubusercontent.com/u/54677442?v=4' },
      { name: '王五', avatar: 'https://avatars.githubusercontent.com/u/54677442?v=4' },
    ]
  },
]

// 处理快捷操作点击
function handleQuickAction(action) {
  if (action.path) {
    router.push(action.path)
  }
}

// 初始化活动图表
function initActivityChart() {
  if (!activityChartRef.value) return

  activityChart = echarts.init(activityChartRef.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['5/10', '5/11', '5/12', '5/13', '5/14', '5/15', '今日'],
      axisLine: {
        lineStyle: {
          color: '#ccc'
        }
      },
      axisLabel: {
        color: '#666'
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      },
      axisLabel: {
        color: '#666'
      },
      splitLine: {
        lineStyle: {
          color: '#eee'
        }
      }
    },
    series: [
      {
        name: '调用次数',
        type: 'line',
        smooth: true,
        data: [820, 932, 901, 934, 1290, 1130, 1286],
        itemStyle: {
          color: '#2080f0'
        },
        lineStyle: {
          width: 3,
          color: '#2080f0'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(32, 128, 240, 0.3)' },
            { offset: 1, color: 'rgba(32, 128, 240, 0.1)' }
          ])
        }
      },
      {
        name: '成功率(%)',
        type: 'line',
        smooth: true,
        data: [92, 93, 91, 94, 95, 93, 96],
        itemStyle: {
          color: '#18a058'
        },
        lineStyle: {
          width: 3,
          color: '#18a058'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(24, 160, 88, 0.3)' },
            { offset: 1, color: 'rgba(24, 160, 88, 0.1)' }
          ])
        }
      }
    ]
  }

  activityChart.setOption(option)
}

// 监听窗口大小变化，调整图表大小
function handleResize() {
  activityChart && activityChart.resize()
}

onMounted(() => {
  initActivityChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  activityChart && activityChart.dispose()
})
</script>

<style lang="scss" scoped>
.welcome-card {
  background: linear-gradient(135deg, #f5f7ff 0%, #e8f0ff 100%);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  }

  .welcome-text {
    background: linear-gradient(90deg, #333 0%, #666 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .welcome-subtext {
    color: #666;
  }

  .avatar-container {
    position: relative;

    .avatar-status {
      position: absolute;
      bottom: 5px;
      right: 5px;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background-color: #18a058;
      border: 2px solid #fff;
    }
  }
}

.stat-cards {
  display: flex;
  gap: 16px;

  .stat-card {
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    padding: 16px;
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    }

    .stat-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: rgba(32, 128, 240, 0.1);
      margin-bottom: 12px;
      color: #2080f0;
    }

    .stat-value {
      font-size: 24px;
      font-weight: bold;
      margin-bottom: 4px;
    }

    .stat-label {
      font-size: 14px;
      color: #666;
    }
  }

  .stat-card:nth-child(1) .stat-icon {
    background: rgba(32, 128, 240, 0.1);
    color: #2080f0;
  }

  .stat-card:nth-child(2) .stat-icon {
    background: rgba(24, 160, 88, 0.1);
    color: #18a058;
  }

  .stat-card:nth-child(3) .stat-icon {
    background: rgba(240, 160, 32, 0.1);
    color: #f0a020;
  }
}

.quick-actions-card, .activity-card, .system-status-card, .projects-card {
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  }
}

.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;

  .quick-action-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 16px;
    border-radius: 12px;
    background: #f5f7ff;
    cursor: pointer;
    transition: all 0.3s ease;

    &:hover {
      background: #e8f0ff;
      transform: translateY(-5px);
    }

    .quick-action-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 48px;
      height: 48px;
      border-radius: 12px;
      background: white;
      margin-bottom: 12px;
      color: #2080f0;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
    }

    .quick-action-name {
      font-size: 14px;
      font-weight: 500;
    }
  }
}

.chart-container {
  width: 100%;
  height: 300px;
}

.status-items {
  display: flex;
  flex-direction: column;
  gap: 24px;

  .status-item {
    .status-label {
      font-size: 14px;
      font-weight: 500;
      margin-bottom: 8px;
    }

    .status-value-container {
      display: flex;
      align-items: center;
      gap: 12px;

      .status-value {
        font-size: 14px;
        font-weight: 600;
        min-width: 45px;
        text-align: right;
      }
    }
  }
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;

  .project-card {
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    }

    .project-desc {
      color: #666;
      margin-bottom: 16px;
      height: 40px;
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }

    .project-footer {
      .project-progress {
        margin-bottom: 12px;
      }

      .project-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .project-date {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 12px;
          color: #666;
        }

        .project-members {
          .member-avatars {
            display: flex;

            img {
              width: 24px;
              height: 24px;
              border-radius: 50%;
              border: 2px solid white;
              margin-left: -8px;

              &:first-child {
                margin-left: 0;
              }
            }
          }
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .stat-cards {
    flex-direction: column;
  }

  .quick-actions-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
