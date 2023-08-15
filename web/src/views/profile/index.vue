<script setup>
import { ref } from 'vue'
import { NButton, NForm, NFormItem, NInput, NTabPane, NTabs, NImage } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import { useUserStore } from '@/store'
import api from '@/api'
import { is } from '~/src/utils'

const userStore = useUserStore()
const isLoading = ref(false)

// 用户信息的表单
const infoFormRef = ref(null)
const infoForm = ref({
  avatar: userStore.avatar,
  username: userStore.name,
  email: userStore.email,
})
async function updateProfile() {
  isLoading.value = true
  infoFormRef.value?.validate(async (err) => {
    if (err) return
    await api
      .updateUser({ ...infoForm.value, id: userStore.userId })
      .then(() => {
        userStore.setUserInfo(infoForm.value)
        isLoading.value = false
        $message.success('修改成功')
      })
      .catch(() => {
        isLoading.value = false
      })
  })
}
const infoFormRules = {
  username: [
    {
      required: true,
      message: '请输入昵称',
      trigger: ['input', 'blur', 'change'],
    },
  ],
}

// 修改密码的表单
const passwordFormRef = ref(null)
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

async function updatePassword() {
  isLoading.value = true
  passwordFormRef.value?.validate(async (err) => {
    if (!err) {
      const data = { ...passwordForm.value, id: userStore.userId }
      await api
        .updatePassword(data)
        .then((res) => {
          $message.success(res.msg)
          passwordForm.value = {
            old_password: '',
            new_password: '',
            confirm_password: '',
          }
          isLoading.value = false
        })
        .catch(() => {
          isLoading.value = false
        })
    }
  })
}
const passwordFormRules = {
  old_password: [
    {
      required: true,
      message: '请输入旧密码',
      trigger: ['input', 'blur', 'change'],
    },
  ],
  new_password: [
    {
      required: true,
      message: '请输入新密码',
      trigger: ['input', 'blur', 'change'],
    },
  ],
  confirm_password: [
    {
      required: true,
      message: '请再次输入密码',
      trigger: ['input', 'blur'],
    },
    {
      validator: validatePasswordStartWith,
      message: '两次密码输入不一致',
      trigger: 'input',
    },
    {
      validator: validatePasswordSame,
      message: '两次密码输入不一致',
      trigger: ['blur', 'password-input'],
    },
  ],
}
function validatePasswordStartWith(rule, value) {
  return (
    !!passwordForm.value.new_password &&
    passwordForm.value.new_password.startsWith(value) &&
    passwordForm.value.new_password.length >= value.length
  )
}
function validatePasswordSame(rule, value) {
  return value === passwordForm.value.new_password
}
</script>

<template>
  <CommonPage :show-header="false">
    <NTabs type="line" animated>
      <NTabPane name="website" tab="修改信息">
        <div class="m-30 flex items-center">
          <NForm
            ref="infoFormRef"
            label-placement="left"
            label-align="left"
            label-width="100"
            :model="infoForm"
            :rules="infoFormRules"
            class="w-400"
          >
            <NFormItem label="头像" path="avatar">
              <NImage width="100" :src="infoForm.avatar"></NImage>
            </NFormItem>
            <NFormItem label="用户姓名" path="username">
              <NInput v-model:value="infoForm.username" type="text" placeholder="请填写姓名" />
            </NFormItem>
            <NFormItem label="邮箱" path="email">
              <NInput v-model:value="infoForm.email" type="text" placeholder="请填写邮箱" />
            </NFormItem>
            <NButton type="primary" :loading="isLoading" @click="updateProfile"> 修改 </NButton>
          </NForm>
        </div>
      </NTabPane>
      <NTabPane name="contact" tab="修改密码">
        <NForm
          ref="passwordFormRef"
          label-placement="left"
          label-align="left"
          :model="passwordForm"
          label-width="100"
          :rules="passwordFormRules"
          class="m-30 w-400"
        >
          <NFormItem label="旧密码" path="old_password">
            <NInput
              v-model:value="passwordForm.old_password"
              type="password"
              show-password-on="mousedown"
              placeholder="请输入旧密码"
            />
          </NFormItem>
          <NFormItem label="新密码" path="new_password">
            <NInput
              v-model:value="passwordForm.new_password"
              :disabled="!passwordForm.old_password"
              type="password"
              show-password-on="mousedown"
              placeholder="请输入新密码"
            />
          </NFormItem>
          <NFormItem label="确认密码" path="confirm_password">
            <NInput
              v-model:value="passwordForm.confirm_password"
              :disabled="!passwordForm.new_password"
              type="password"
              show-password-on="mousedown"
              placeholder="请再次输入新密码"
            />
          </NFormItem>
          <NButton type="primary" :loading="isLoading" @click="updatePassword"> 修改 </NButton>
        </NForm>
      </NTabPane>
    </NTabs>
  </CommonPage>
</template>
