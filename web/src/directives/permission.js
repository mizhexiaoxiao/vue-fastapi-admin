import { useUserStore, usePermissionStore } from '@/store'

function hasPermission(permission) {
  const userStore = useUserStore()
  const userPermissionStore = usePermissionStore()

  const accessApis = userPermissionStore.apis
  if (userStore.isSuperUser) {
    return true
  }
  return accessApis.includes(permission)
}

export default function setupPermissionDirective(app) {
  function updateElVisible(el, permission) {
    if (!permission) {
      throw new Error(`need roles: like v-permission="get/api/v1/user/list"`)
    }
    if (!hasPermission(permission)) {
      el.parentElement?.removeChild(el)
    }
  }

  const permissionDirective = {
    mounted(el, binding) {
      updateElVisible(el, binding.value)
    },
    beforeUpdate(el, binding) {
      updateElVisible(el, binding.value)
    },
  }

  app.directive('permission', permissionDirective)
}
