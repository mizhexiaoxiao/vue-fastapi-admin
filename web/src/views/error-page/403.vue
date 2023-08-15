<template>
  <AppPage>
    <n-result m-auto status="403" description="抱歉，您无权访问该页面">
      <template #icon>
        <icon-custom-forbidden text-400px text-primary></icon-custom-forbidden>
      </template>
      <template #footer>
        <n-button type="primary" @click="replace('/')">返回首页</n-button>
      </template>
    </n-result>
  </AppPage>
</template>

<script setup>
const { replace } = useRouter()
</script>
