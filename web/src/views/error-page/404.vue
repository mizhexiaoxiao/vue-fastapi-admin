<template>
  <AppPage>
    <n-result m-auto status="404" description="抱歉，您访问的页面不存在。">
      <template #icon>
        <icon-custom-not-found text-400px text-primary></icon-custom-not-found>
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
