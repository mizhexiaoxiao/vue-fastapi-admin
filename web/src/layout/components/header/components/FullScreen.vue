<template>
  <n-icon v-if="appStore.fullScreen" mr20 size="18" style="cursor: pointer" @click="toggle">
    <icon-ant-design:fullscreen-exit-outlined v-if="isFullscreen" />
    <icon-ant-design:fullscreen-outlined v-else />
  </n-icon>
</template>

<script setup>
import { useFullscreen } from '@vueuse/core'
import { useAppStore } from '@/store'

const appStore = useAppStore()
const { isFullscreen, toggle } = useFullscreen()
</script>
