<template>
  <AppPage>
    <n-result m-auto status="401">
      <template #icon>
        <icon-custom-unauthorized text-400px text-primary></icon-custom-unauthorized>
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
