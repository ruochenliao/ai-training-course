<script setup>
import SideLogo from './components/SideLogo.vue'
import SideMenu from './components/SideMenu.vue'
</script>

<style lang="scss" scoped>
.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.sidebar-menu {
  flex: 1;
  overflow-y: auto;
}
</style>

<template>
  <div class="sidebar-container">
    <SideLogo />
    <SideMenu class="sidebar-menu" />
  </div>
</template>
