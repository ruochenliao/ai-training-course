<template>
  <n-icon mr-20 size="18" style="cursor: pointer" @click="handleLinkClick">
    <icon-mdi:help-circle />
  </n-icon>
</template>

<script setup>
function handleLinkClick() {
  // 可以链接到帮助文档或技术支持页面
  window.open('#')
}
</script>
