<template>
  <AppPage>
    <n-result m-auto status="404">
      <template #icon>
        <icon-custom-not-found text-400px text-primary></icon-custom-not-found>
      </template>
      <template #footer>
        <n-button type="primary" @click="replace('/')">{{
          $t('views.errors.text_back_to_home')
        }}</n-button>
      </template>
    </n-result>
  </AppPage>
</template>

<script setup>
const { replace } = useRouter()
</script>
