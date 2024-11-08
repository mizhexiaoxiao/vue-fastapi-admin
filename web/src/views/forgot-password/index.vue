<script setup>
import AppPage from '@/components/page/AppPage.vue'
import bgImg from '@/assets/images/login_bg.webp'
import { lStorage } from '@/utils'
import { useI18n } from 'vue-i18n'
import api from '@/api'

const { t } = useI18n({ useScope: 'global' })

const loading = ref(false)

const isSent = ref(false)
const isSuccess = ref(true)
const viewMessage = ref('')
const forgotPassword = ref({
  email: '',
  language: lStorage.get('locale'),
})

const handleForgotPassword = async () => {
  loading.value = true
  await api
    .forgotPassword(forgotPassword.value)
    .then((res) => {
      isSuccess.value = true
      isSent.value = true
      viewMessage.value = t(`views.forget_password.${res.msg}`)
    })
    .catch((res) => {
      isSuccess.value = false
      isSent.value = true
      console.log(res.error.msg)
      console.log(`views.forget_password.${res.error.msg}`)
      viewMessage.value = t(`views.forget_password.${res.error.msg}`)
    })
    .finally(() => {
      loading.value = false
    })
}
</script>

<template>
  <AppPage :show-footer="false" bg-cover :style="{ backgroundImage: `url(${bgImg})` }">
    <div
      style="transform: translateY(25px)"
      class="m-auto max-w-1500 min-w-345 f-c-c rounded-10 bg-white bg-opacity-60 p-15 card-shadow"
      dark:bg-dark
    >
      <div id="card" w-320 flex-col px-20 py-35>
        <template v-if="!isSent">
          <h6 f-c-c text-18 font-normal color="#6a6a6a">
            {{ $t('views.forget_password.forget_password') }}
          </h6>
          <div mt-30>
            <n-input
              v-model:value="forgotPassword.email"
              autofocus
              class="h-50 items-center pl-10 text-16"
              placeholder="Email"
            />
          </div>
          <div mt-20>
            <n-button
              h-50
              w-full
              rounded-5
              text-16
              type="primary"
              :loading="loading"
              @click="handleForgotPassword"
            >
              {{ $t('views.forget_password.send_password_reset_email') }}
            </n-button>
          </div>
        </template>
        <template v-else-if="isSent && isSuccess">
          <div mt-10>
            <n-result status="success" :description="viewMessage"></n-result>
          </div>
        </template>
        <template v-else>
          <div mt-10>
            <n-result status="error" :description="viewMessage"></n-result>
          </div>
        </template>
      </div>
    </div>
  </AppPage>
</template>

<style scoped></style>
