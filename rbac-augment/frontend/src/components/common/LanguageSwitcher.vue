<template>
  <el-dropdown trigger="click" @command="handleLanguageChange" class="language-switcher">
    <el-button type="link" class="switcher-btn">
      <el-icon size="18">
        <Position />
      </el-icon>
      <span class="language-text">{{ currentLanguageLabel }}</span>
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item :command="'zh-CN'" :class="{ 'is-active': appStore.language === 'zh-CN' }">
          <span>简体中文</span>
        </el-dropdown-item>
        <el-dropdown-item :command="'en-US'" :class="{ 'is-active': appStore.language === 'en-US' }">
          <span>English</span>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup lang="ts">
/**
 * 语言切换组件
 * 用于在不同语言之间切换
 */
import { computed } from 'vue'
import { Position } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import { useI18n } from 'vue-i18n'

const appStore = useAppStore()
const { locale } = useI18n()

// 当前语言标签
const currentLanguageLabel = computed(() => {
  return appStore.language === 'zh-CN' ? '简体中文' : 'English'
})

// 处理语言切换
const handleLanguageChange = (lang: string) => {
  // 类型断言确保类型安全
  const validLang = lang as 'zh-CN' | 'en-US'
  appStore.setLanguage(validLang)
  locale.value = validLang // 同步更新 i18n 的 locale
}
</script>

<style lang="scss" scoped>
.language-switcher {
  .switcher-btn {
    display: flex;
    align-items: center;
    gap: 4px;
    height: 32px;
    padding: 0 8px;
    
    .language-text {
      font-size: 14px;
      margin-left: 4px;
    }
  }
  
  :deep(.el-dropdown-menu__item.is-active) {
    color: var(--el-color-primary);
    font-weight: 500;
    background-color: rgba(var(--el-color-primary-rgb), 0.1);
  }
}
</style>