<script setup>
import { ref, defineProps } from 'vue'
import bgImg from '@/assets/images/login_bg.webp'
import api from '@/api'
import AppPage from '@/components/page/AppPage.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n({ useScope: 'global' })

const props = defineProps({ resetToken: { type: String, required: true } })

const isSent = ref(false)
const isSuccess = ref(true)
const viewMessage = ref('')

const resetPassword = ref({
  password: '',
  reset_token: props.resetToken,
})

const handleResetPassword = async () => {
  await api
    .emailResetPassword(resetPassword.value)
    .then((res) => {
      isSuccess.value = true
      isSent.value = true
      viewMessage.value = t(`views.resetPassword.${res.msg}`)
    })
    .catch((res) => {
      isSuccess.value = false
      isSent.value = true
      viewMessage.value = t(`views.resetPassword.${res.error.msg}`)
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
            {{ $t('views.resetPassword.resetPassword') }}
          </h6>
          <div mt-30>
            <n-input
              v-model:value="resetPassword.password"
              autofocus
              class="h-50 items-center pl-10 text-16"
              placeholder="Password"
              :maxlength="20"
            />
          </div>
          <div mt-20>
            <n-button h-50 w-full rounded-5 text-16 type="primary" @click="handleResetPassword">
              {{ $t('views.resetPassword.resetPassword') }}
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
