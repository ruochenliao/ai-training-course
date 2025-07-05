<template>
  <transition
    :name="transitionName"
    :mode="mode"
    :appear="appear"
    :duration="duration"
    @before-enter="handleBeforeEnter"
    @enter="handleEnter"
    @after-enter="handleAfterEnter"
    @before-leave="handleBeforeLeave"
    @leave="handleLeave"
    @after-leave="handleAfterLeave"
  >
    <slot />
  </transition>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// 组件属性
interface Props {
  type?: 'fade' | 'slide-up' | 'slide-down' | 'slide-left' | 'slide-right' | 'zoom' | 'flip' | 'bounce' | 'elastic' | 'custom'
  mode?: 'in-out' | 'out-in'
  appear?: boolean
  duration?: number | { enter: number; leave: number }
  delay?: number
  customName?: string
}

const props = withDefaults(defineProps<Props>(), {
  type: 'fade',
  mode: 'out-in',
  appear: false,
  duration: 300,
  delay: 0
})

// 组件事件
interface Emits {
  (e: 'before-enter', el: Element): void
  (e: 'enter', el: Element): void
  (e: 'after-enter', el: Element): void
  (e: 'before-leave', el: Element): void
  (e: 'leave', el: Element): void
  (e: 'after-leave', el: Element): void
}

const emit = defineEmits<Emits>()

// 计算过渡名称
const transitionName = computed(() => {
  if (props.type === 'custom' && props.customName) {
    return props.customName
  }
  return `animated-${props.type}`
})

// 过渡事件处理
const handleBeforeEnter = (el: Element) => {
  if (props.delay > 0) {
    (el as HTMLElement).style.animationDelay = `${props.delay}ms`
  }
  emit('before-enter', el)
}

const handleEnter = (el: Element) => {
  emit('enter', el)
}

const handleAfterEnter = (el: Element) => {
  if (props.delay > 0) {
    (el as HTMLElement).style.animationDelay = ''
  }
  emit('after-enter', el)
}

const handleBeforeLeave = (el: Element) => {
  emit('before-leave', el)
}

const handleLeave = (el: Element) => {
  emit('leave', el)
}

const handleAfterLeave = (el: Element) => {
  emit('after-leave', el)
}
</script>

<style lang="scss" scoped>
// 动画持续时间变量
$duration-fast: 200ms;
$duration-normal: 300ms;
$duration-slow: 500ms;

// 缓动函数
$ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
$ease-out: cubic-bezier(0, 0, 0.2, 1);
$ease-in: cubic-bezier(0.4, 0, 1, 1);
$ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
$ease-elastic: cubic-bezier(0.175, 0.885, 0.32, 1.275);

// 淡入淡出动画
.animated-fade-enter-active,
.animated-fade-leave-active {
  transition: opacity $duration-normal $ease-in-out;
}

.animated-fade-enter-from,
.animated-fade-leave-to {
  opacity: 0;
}

// 向上滑动动画
.animated-slide-up-enter-active,
.animated-slide-up-leave-active {
  transition: all $duration-normal $ease-out;
}

.animated-slide-up-enter-from {
  opacity: 0;
  transform: translateY(30px);
}

.animated-slide-up-leave-to {
  opacity: 0;
  transform: translateY(-30px);
}

// 向下滑动动画
.animated-slide-down-enter-active,
.animated-slide-down-leave-active {
  transition: all $duration-normal $ease-out;
}

.animated-slide-down-enter-from {
  opacity: 0;
  transform: translateY(-30px);
}

.animated-slide-down-leave-to {
  opacity: 0;
  transform: translateY(30px);
}

// 向左滑动动画
.animated-slide-left-enter-active,
.animated-slide-left-leave-active {
  transition: all $duration-normal $ease-out;
}

.animated-slide-left-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.animated-slide-left-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

// 向右滑动动画
.animated-slide-right-enter-active,
.animated-slide-right-leave-active {
  transition: all $duration-normal $ease-out;
}

.animated-slide-right-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.animated-slide-right-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

// 缩放动画
.animated-zoom-enter-active,
.animated-zoom-leave-active {
  transition: all $duration-normal $ease-out;
}

.animated-zoom-enter-from {
  opacity: 0;
  transform: scale(0.8);
}

.animated-zoom-leave-to {
  opacity: 0;
  transform: scale(1.2);
}

// 翻转动画
.animated-flip-enter-active,
.animated-flip-leave-active {
  transition: all $duration-normal $ease-in-out;
}

.animated-flip-enter-from {
  opacity: 0;
  transform: rotateY(-90deg);
}

.animated-flip-leave-to {
  opacity: 0;
  transform: rotateY(90deg);
}

// 弹跳动画
.animated-bounce-enter-active {
  animation: bounce-in $duration-slow $ease-bounce;
}

.animated-bounce-leave-active {
  animation: bounce-out $duration-normal $ease-in;
}

@keyframes bounce-in {
  0% {
    opacity: 0;
    transform: scale(0.3);
  }
  50% {
    opacity: 1;
    transform: scale(1.05);
  }
  70% {
    transform: scale(0.9);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes bounce-out {
  0% {
    opacity: 1;
    transform: scale(1);
  }
  100% {
    opacity: 0;
    transform: scale(0.3);
  }
}

// 弹性动画
.animated-elastic-enter-active {
  animation: elastic-in $duration-slow $ease-elastic;
}

.animated-elastic-leave-active {
  animation: elastic-out $duration-normal $ease-in;
}

@keyframes elastic-in {
  0% {
    opacity: 0;
    transform: scale(0) rotate(-360deg);
  }
  50% {
    opacity: 1;
    transform: scale(1.2) rotate(-180deg);
  }
  100% {
    opacity: 1;
    transform: scale(1) rotate(0deg);
  }
}

@keyframes elastic-out {
  0% {
    opacity: 1;
    transform: scale(1) rotate(0deg);
  }
  100% {
    opacity: 0;
    transform: scale(0) rotate(360deg);
  }
}

// 响应式动画调整
@media (max-width: 768px) {
  .animated-slide-up-enter-from,
  .animated-slide-up-leave-to,
  .animated-slide-down-enter-from,
  .animated-slide-down-leave-to {
    transform: translateY(20px);
  }
  
  .animated-slide-left-enter-from,
  .animated-slide-left-leave-to,
  .animated-slide-right-enter-from,
  .animated-slide-right-leave-to {
    transform: translateX(20px);
  }
}

// 减少动画模式支持
@media (prefers-reduced-motion: reduce) {
  .animated-fade-enter-active,
  .animated-fade-leave-active,
  .animated-slide-up-enter-active,
  .animated-slide-up-leave-active,
  .animated-slide-down-enter-active,
  .animated-slide-down-leave-active,
  .animated-slide-left-enter-active,
  .animated-slide-left-leave-active,
  .animated-slide-right-enter-active,
  .animated-slide-right-leave-active,
  .animated-zoom-enter-active,
  .animated-zoom-leave-active,
  .animated-flip-enter-active,
  .animated-flip-leave-active {
    transition: none;
  }
  
  .animated-bounce-enter-active,
  .animated-bounce-leave-active,
  .animated-elastic-enter-active,
  .animated-elastic-leave-active {
    animation: none;
  }
  
  .animated-fade-enter-from,
  .animated-fade-leave-to,
  .animated-slide-up-enter-from,
  .animated-slide-up-leave-to,
  .animated-slide-down-enter-from,
  .animated-slide-down-leave-to,
  .animated-slide-left-enter-from,
  .animated-slide-left-leave-to,
  .animated-slide-right-enter-from,
  .animated-slide-right-leave-to,
  .animated-zoom-enter-from,
  .animated-zoom-leave-to,
  .animated-flip-enter-from,
  .animated-flip-leave-to {
    opacity: 1;
    transform: none;
  }
}

// 暗色主题适配
.dark {
  // 在暗色主题下可以调整动画效果
  .animated-zoom-enter-from {
    filter: brightness(0.8);
  }
  
  .animated-flip-enter-from,
  .animated-flip-leave-to {
    filter: brightness(0.9);
  }
}
</style>
