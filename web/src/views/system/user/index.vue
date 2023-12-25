<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import {
  NButton,
  NCheckbox,
  NCheckboxGroup,
  NForm,
  NFormItem,
  NImage,
  NInput,
  NSpace,
  NSwitch,
  NTag,
  NPopconfirm,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'

import { formatDate, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
// import { loginTypeMap, loginTypeOptions } from '@/constant/data'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'
import { useUserStore } from '@/store'
import { useI18n } from 'vue-i18n'

defineOptions({ name: '用户列表' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const { t } = useI18n({ useScope: 'global' })

const {
  modalVisible,
  modalTitle,
  modalAction,
  modalLoading,
  handleSave,
  modalForm,
  modalFormRef,
  handleEdit,
  handleDelete,
  handleAdd,
} = useCRUD({
  name: t('views.system.user_management.label_user'),
  initForm: {},
  doCreate: api.createUser,
  doUpdate: api.updateUser,
  doDelete: api.deleteUser,
  refresh: () => $table.value?.handleSearch(),
})

const roleOption = ref([])

onMounted(() => {
  $table.value?.handleSearch()
  api.getRoleList({ page: 1, page_size: 9999 }).then((res) => (roleOption.value = res.data))
})

const columns = [
  {
    title: t('views.system.user_management.table.column_avatar'),
    key: 'avatar',
    width: 50,
    align: 'center',
    render(row) {
      return h(NImage, {
        height: 50,
        imgProps: { style: { 'border-radius': '3px' } },
        src: row.avatar,
        'fallback-src': 'http://dummyimage.com/400x400', // 加载失败
        'show-toolbar-tooltip': true,
      })
    },
  },
  {
    title: t('views.system.user_management.table.column_username'),
    key: 'username',
    width: 60,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: t('views.system.user_management.table.column_email'),
    key: 'email',
    width: 60,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: t('views.system.user_management.table.column_role'),
    key: 'role',
    width: 60,
    align: 'center',
    render(row) {
      const roles = row.roles ?? []
      const group = []
      for (let i = 0; i < roles.length; i++)
        group.push(
          h(NTag, { type: 'info', style: { margin: '2px 3px' } }, { default: () => roles[i].name }),
        )
      return h('span', group)
    },
  },
  {
    title: t('views.system.user_management.table.column_is_superuser'),
    key: 'is_superuser',
    align: 'center',
    width: 40,
    render(row) {
      return h(
        NTag,
        { type: 'info', style: { margin: '2px 3px' } },
        { default: () => (row.is_superuser ? t('common.text.yes') : t('common.text.no')) },
      )
    },
  },
  {
    title: t('views.system.user_management.table.column_last_login'),
    key: 'last_login',
    align: 'center',
    width: 80,
    ellipsis: { tooltip: true },
    render(row) {
      return h(
        NButton,
        { size: 'small', type: 'text', ghost: true },
        {
          default: () => (row.last_login !== null ? formatDate(row.last_login) : null),
          icon: renderIcon('mdi:update', { size: 16 }),
        },
      )
    },
  },
  {
    title: t('views.system.user_management.table.column_is_active'),
    key: 'is_active',
    width: 50,
    align: 'center',
    render(row) {
      return h(NSwitch, {
        size: 'small',
        rubberBand: false,
        value: row.is_active,
        loading: !!row.publishing,
        checkedValue: false,
        uncheckedValue: true,
        onUpdateValue: () => handleUpdateDisable(row),
      })
    },
  },
  {
    title: t('views.system.user_management.table.column_actions'),
    key: 'actions',
    width: 80,
    align: 'center',
    fixed: 'right',
    render(row) {
      return [
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              style: 'margin-right: 8px;',
              onClick: () => {
                // roles => role_ids
                handleEdit(row)
                modalForm.value.roles = row.roles.map((e) => (e = e.id))
              },
            },
            {
              default: () => t('common.buttons.edit'),
              icon: renderIcon('material-symbols:edit', { size: 16 }),
            },
          ),
          [[vPermission, 'post/api/v1/user/update']],
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ user_id: row.id }, false),
            onNegativeClick: () => {},
          },
          {
            trigger: () =>
              withDirectives(
                h(
                  NButton,
                  {
                    size: 'small',
                    type: 'error',
                  },
                  {
                    default: () => t('common.buttons.remove'),
                    icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
                  },
                ),
                [[vPermission, 'delete/api/v1/user/delete']],
              ),
            default: () => h('div', {}, t('views.system.user.message_confirm_remove_user')),
          },
        ),
      ]
    },
  },
]

// 修改用户禁用状态
async function handleUpdateDisable(row) {
  if (!row.id) return
  const userStore = useUserStore()
  if (userStore.userId === row.id) {
    $message.error(t('views.system.user_management.user_form.message_cannot_inactive'))
    return
  }
  row.publishing = true
  row.is_active = row.is_active === false
  row.publishing = false
  const role_ids = []
  row.roles.forEach((e) => {
    role_ids.push(e.id)
  })
  row.roles = role_ids
  try {
    await api.updateUser(row)
    $message?.success(
      row.is_active
        ? t('views.system.user_management.user_form.message_user_activated')
        : t('views.system.user_management.user_form.message_user_inactivated'),
    )
    $table.value?.handleSearch()
  } catch (err) {
    // 有异常恢复原来的状态
    row.is_active = row.is_active === false
  } finally {
    row.publishing = false
  }
}

const validateAddUser = {
  username: [
    {
      required: true,
      message: t('views.system.user_management.user_form.message_username_required'),
      trigger: ['input', 'blur'],
    },
  ],
  email: [
    {
      required: true,
      message: t('views.system.user_management.user_form.message_email_required'),
      trigger: ['input', 'change'],
    },
    {
      trigger: ['blur'],
      validator: (rule, value, callback) => {
        const re = /^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/
        if (!re.test(modalForm.value.email)) {
          callback(t('views.system.user_management.user_form.message_email_type'))
          return
        }
        callback()
      },
    },
  ],
  password: [
    {
      required: true,
      message: t('views.system.user_management.user_form.message_password_required'),
      trigger: ['input', 'blur', 'change'],
    },
  ],
  confirmPassword: [
    {
      required: true,
      message: t('views.system.user_management.user_form.message_password_confirmation_required'),
      trigger: ['input'],
    },
    {
      trigger: ['blur'],
      validator: (rule, value, callback) => {
        if (value !== modalForm.value.password) {
          callback(t('views.system.user_management.user_form.message_password_confirmation_diff'))
          return
        }
        callback()
      },
    },
  ],
  roles: [
    {
      type: 'array',
      required: true,
      message: t('views.system.user_management.user_form.message_role_required'),
      trigger: ['blur', 'change'],
    },
  ],
}
</script>

<template>
  <!-- 业务页面 -->
  <CommonPage show-footer :title="$t('views.system.user_management.label_user_list')">
    <template #action>
      <NButton v-permission="'post/api/v1/user/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />
        {{ $t('views.system.user_management.button_add_user') }}
      </NButton>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getUserList"
    >
      <template #queryBar>
        <QueryBarItem :label="$t('views.system.user_management.query_form.label_username')">
          <NInput
            v-model:value="queryItems.username"
            clearable
            type="text"
            :placeholder="$t('views.system.user_management.query_form.placeholder_username')"
            @keypress.enter="$table?.handleSearch"
          />
        </QueryBarItem>
        <QueryBarItem :label="$t('views.system.user_management.query_form.label_email')">
          <NInput
            v-model:value="queryItems.email"
            clearable
            type="text"
            :placeholder="$t('views.system.user_management.query_form.placeholder_email')"
            @keypress.enter="$table?.handleSearch"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- 新增/编辑 弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @save="handleSave"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="120"
        :model="modalForm"
        :rules="validateAddUser"
      >
        <NFormItem
          :label="$t('views.system.user_management.user_form.label_username')"
          path="username"
        >
          <NInput
            v-model:value="modalForm.username"
            clearable
            :placeholder="$t('views.system.user_management.user_form.placeholder_username')"
          />
        </NFormItem>
        <NFormItem :label="$t('views.system.user_management.user_form.label_email')" path="email">
          <NInput
            v-model:value="modalForm.email"
            clearable
            :placeholder="$t('views.system.user_management.user_form.placeholder_email')"
          />
        </NFormItem>
        <NFormItem
          v-if="modalAction === 'add'"
          :label="$t('views.system.user_management.user_form.label_password')"
          path="password"
        >
          <NInput
            v-model:value="modalForm.password"
            show-password-on="mousedown"
            type="password"
            clearable
            :placeholder="$t('views.system.user_management.user_form.placeholder_password')"
          />
        </NFormItem>
        <NFormItem
          v-if="modalAction === 'add'"
          :label="$t('views.system.user_management.user_form.label_confirmPassword')"
          path="confirmPassword"
        >
          <NInput
            v-model:value="modalForm.confirmPassword"
            show-password-on="mousedown"
            type="password"
            clearable
            :placeholder="$t('views.system.user_management.user_form.placeholder_confirmPassword')"
          />
        </NFormItem>
        <NFormItem :label="$t('views.system.user_management.user_form.label_roles')" path="roles">
          <NCheckboxGroup v-model:value="modalForm.roles">
            <NSpace item-style="display: flex;">
              <NCheckbox
                v-for="item in roleOption"
                :key="item.id"
                :value="item.id"
                :label="item.name"
              />
            </NSpace>
          </NCheckboxGroup>
        </NFormItem>
        <NFormItem
          :label="$t('views.system.user_management.user_form.label_is_superuser')"
          path="is_superuser"
        >
          <NSwitch
            v-model:value="modalForm.is_superuser"
            size="small"
            :checked-value="true"
            :unchecked-value="false"
          ></NSwitch>
        </NFormItem>
        <NFormItem
          :label="$t('views.system.user_management.user_form.label_is_active')"
          path="is_active"
        >
          <NSwitch
            v-model:value="modalForm.is_active"
            :checked-value="false"
            :unchecked-value="true"
            :default-value="true"
          />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
