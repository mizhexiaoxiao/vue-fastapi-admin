<template>
  <n-layout has-sider wh-full>
    <n-layout-sider
      bordered
      collapse-mode="width"
      :collapsed-width="64"
      :width="220"
      :native-scrollbar="false"
      :collapsed="appStore.collapsed"
    >
      <SideBar />
    </n-layout-sider>

    <article flex-col flex-1 overflow-hidden>
      <header
        class="flex items-center border-b bg-white px-15 bc-eee"
        dark="bg-dark border-0"
        :style="`height: ${header.height}px`"
      >
        <AppHeader />
      </header>
      <section v-if="tags.visible" hidden border-b bc-eee sm:block dark:border-0>
        <AppTags :style="{ height: `${tags.height}px` }" />
      </section>
      <section flex-1 overflow-hidden bg-hex-f5f6fb dark:bg-hex-101014>
        <AppMain />
      </section>
    </article>
  </n-layout>
</template>

<script setup>
import AppHeader from './components/header/index.vue'
import SideBar from './components/sidebar/index.vue'
import AppMain from './components/AppMain.vue'
import AppTags from './components/tags/index.vue'
import { useAppStore } from '@/store'
import { header, tags } from '~/settings'

// 移动端适配
import { useBreakpoints } from '@vueuse/core'

const appStore = useAppStore()
const breakpointsEnum = {
  xl: 1600,
  lg: 1199,
  md: 991,
  sm: 666,
  xs: 575,
}
const breakpoints = reactive(useBreakpoints(breakpointsEnum))
const isMobile = breakpoints.smaller('sm')
const isPad = breakpoints.between('sm', 'md')
const isPC = breakpoints.greater('md')
watchEffect(() => {
  if (isMobile.value) {
    // Mobile
    appStore.setCollapsed(true)
    appStore.setFullScreen(false)
  }

  if (isPad.value) {
    // IPad
    appStore.setCollapsed(true)
    appStore.setFullScreen(false)
  }

  if (isPC.value) {
    // PC
    appStore.setCollapsed(false)
    appStore.setFullScreen(true)
  }
})
</script>
