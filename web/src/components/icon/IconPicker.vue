<script setup>
import { ref } from 'vue'
import { watchDebounced } from '@vueuse/core'
import { NInput, NPopover } from 'naive-ui'

import TheIcon from './TheIcon.vue'
import iconData from '@/assets/js/icons'

const props = defineProps({ value: String })
const emit = defineEmits(['update:value'])

const choosed = ref(props.value) // 选中值
const icons = ref(iconData)
// const icons = ref(iconData.filter((icon) => icon.includes(choosed.value))) // 可选图标列表

function filterIcons() {
  icons.value = iconData.filter((item) => item.includes(choosed.value))
}

function selectIcon(icon) {
  choosed.value = icon
  emit('update:value', choosed.value)
}

watchDebounced(
  choosed,
  () => {
    filterIcons()
    emit('update:value', choosed.value)
  },
  { debounce: 200 },
)
</script>

<template>
  <div class="w-full">
    <NPopover trigger="click" placement="bottom-start">
      <template #trigger>
        <NInput v-model:value="choosed" placeholder="请输入图标名称" @update:value="filterIcons">
          <template #prefix>
            <span class="i-mdi:magnify text-18" />
          </template>
          <template #suffix>
            <TheIcon :icon="choosed" :size="18" />
          </template>
        </NInput>
      </template>
      <template #footer>
        更多图标去
        <a class="text-blue" target="_blank" href="https://icones.js.org/collection/all">
          Icones
        </a>
        查看
      </template>
      <ul v-if="icons.length" class="h-150 w-300 overflow-y-scroll">
        <li
          v-for="(icon, index) in icons"
          :key="index"
          class="mx-5 inline-block cursor-pointer hover:text-cyan"
          @click="selectIcon(icon)"
        >
          <TheIcon :icon="icon" :size="18" />
        </li>
      </ul>
      <div v-else>
        <TheIcon :icon="choosed" :size="18" />
      </div>
    </NPopover>
  </div>
</template>
