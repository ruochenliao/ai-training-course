import { setup } from '@css-render/vue3-ssr'
import {
  // create naive ui
  create,
  // component
  NButton,
  NCard,
  NConfigProvider,
  NDataTable,
  NDatePicker,
  NDialog,
  NDialogProvider,
  NDropdown,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NInputNumber,
  NLayout,
  NLayoutContent,
  NLayoutHeader,
  NLayoutSider,
  NLoadingBarProvider,
  NMenu,
  NMessageProvider,
  NModal,
  NNotificationProvider,
  NPagination,
  NPopconfirm,
  NSelect,
  NSpace,
  NSpin,
  NSwitch,
  NTable,
  NTag,
  NTooltip,
  NUpload,
  NUploadDragger,
  NAvatar,
  NBreadcrumb,
  NBreadcrumbItem,
  NCheckbox,
  NCheckboxGroup,
  NRadio,
  NRadioGroup,
  NSlider,
  NSteps,
  NStep,
  NTabs,
  NTabPane,
  NTree,
  NAlert,
  NBadge,
  NCollapse,
  NCollapseItem,
  NDescriptions,
  NDescriptionsItem,
  NDrawer,
  NDrawerContent,
  NEmpty,
  NResult,
  NSkeleton,
  NStatistic,
  NTimeline,
  NTimelineItem,
  NBackTop,
  NDivider,
  NEl,
  NScrollbar,
  NWatermark
} from 'naive-ui'

export default defineNuxtPlugin((nuxtApp) => {
  if (process.server) {
    const { collect } = setup(nuxtApp.vueApp)
    const originalRenderToString = nuxtApp.ssrContext?.renderToString
    if (originalRenderToString) {
      nuxtApp.ssrContext!.renderToString = async (input, context) => {
        const html = await originalRenderToString(input, context)
        return {
          html,
          renderResourceHeaders: () => {
            return {
              'naive-ui-style': collect()
            }
          }
        }
      }
    }
  }

  const naive = create({
    components: [
      NButton,
      NCard,
      NConfigProvider,
      NDataTable,
      NDatePicker,
      NDialog,
      NDialogProvider,
      NDropdown,
      NForm,
      NFormItem,
      NIcon,
      NInput,
      NInputNumber,
      NLayout,
      NLayoutContent,
      NLayoutHeader,
      NLayoutSider,
      NLoadingBarProvider,
      NMenu,
      NMessageProvider,
      NModal,
      NNotificationProvider,
      NPagination,
      NPopconfirm,
      NSelect,
      NSpace,
      NSpin,
      NSwitch,
      NTable,
      NTag,
      NTooltip,
      NUpload,
      NUploadDragger,
      NAvatar,
      NBreadcrumb,
      NBreadcrumbItem,
      NCheckbox,
      NCheckboxGroup,
      NRadio,
      NRadioGroup,
      NSlider,
      NSteps,
      NStep,
      NTabs,
      NTabPane,
      NTree,
      NAlert,
      NBadge,
      NCollapse,
      NCollapseItem,
      NDescriptions,
      NDescriptionsItem,
      NDrawer,
      NDrawerContent,
      NEmpty,
      NResult,
      NSkeleton,
      NStatistic,
      NTimeline,
      NTimelineItem,
      NBackTop,
      NDivider,
      NEl,
      NScrollbar,
      NWatermark
    ]
  })

  nuxtApp.vueApp.use(naive)
})
