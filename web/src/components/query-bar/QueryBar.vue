<template>
  <div
    bg="#fafafc"
    min-h-60
    flex
    items-start
    justify-between
    b-1
    rounded-8
    p-15
    bc-ccc
    dark:bg-black
  >
    <n-space wrap :size="[35, 15]">
      <slot />
      <div>
        <n-button secondary type="primary" @click="emit('reset')">重置</n-button>
        <n-button ml-20 type="primary" @click="emit('search')">搜索</n-button>
      </div>
    </n-space>
  </div>
</template>

<script setup>
const emit = defineEmits(['search', 'reset'])
</script>
