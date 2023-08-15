<script setup>
import { renderIcon } from '@/utils'

defineProps({
  icon: {
    type: String,
    required: true,
  },
  size: {
    type: Number,
    default: 14,
  },
  color: {
    type: String,
    default: undefined,
  },
})
</script>

<template>
  <component :is="renderIcon(icon, { size, color })" />
</template>
