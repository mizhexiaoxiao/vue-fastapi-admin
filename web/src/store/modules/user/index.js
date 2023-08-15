import { defineStore } from 'pinia'
import { resetRouter } from '@/router'
import { useTagsStore, usePermissionStore } from '@/store'
import { removeToken, toLogin } from '@/utils'
import api from '@/api'

export const useUserStore = defineStore('user', {
  state() {
    return {
      userInfo: {},
    }
  },
  getters: {
    userId() {
      return this.userInfo?.id
    },
    name() {
      return this.userInfo?.username
    },
    email() {
      return this.userInfo?.email
    },
    avatar() {
      return this.userInfo?.avatar
    },
    role() {
      return this.userInfo?.roles || []
    },
    isSuperUser() {
      return this.userInfo?.is_superuser
    },
    isActive() {
      return this.userInfo?.is_active
    },
  },
  actions: {
    async getUserInfo() {
      try {
        const res = await api.getUserInfo()
        const { id, username, email, avatar, roles, is_superuser, is_active } = res.data
        this.userInfo = { id, username, email, avatar, roles, is_superuser, is_active }
        return Promise.resolve(res.data)
      } catch (error) {
        return Promise.reject(error)
      }
    },
    async logout() {
      const { resetTags } = useTagsStore()
      const { resetPermission } = usePermissionStore()
      removeToken()
      resetTags()
      resetPermission()
      resetRouter()
      this.$reset()
      toLogin()
    },
    setUserInfo(userInfo = {}) {
      this.userInfo = { ...this.userInfo, ...userInfo }
    },
  },
})
