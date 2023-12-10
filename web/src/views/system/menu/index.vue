<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NPopconfirm,
  NSwitch,
  NTreeSelect,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import IconPicker from '@/components/icon/IconPicker.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

import { formatDate, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'

defineOptions({ name: '菜单管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const menuDisabled = ref(false)

// 表单初始化内容
const initForm = {
  order: 1,
  keepalive: true,
}

const {
  modalVisible,
  modalTitle,
  modalLoading,
  handleAdd,
  handleDelete,
  handleEdit,
  handleSave,
  modalForm,
  modalFormRef,
} = useCRUD({
  name: '菜单',
  initForm,
  doCreate: api.createMenu,
  doDelete: api.deleteMenu,
  doUpdate: api.updateMenu,
  refresh: () => $table.value?.handleSearch(),
})

onMounted(() => {
  $table.value?.handleSearch()
  getTreeSelect()
})

// 是否展示 "菜单类型"
const showMenuType = ref(false)
const menuOptions = ref([])

const columns = [
  { title: 'ID', key: 'id', width: 50, ellipsis: { tooltip: true } },
  { title: '菜单名称', key: 'name', width: 80, ellipsis: { tooltip: true } },
  {
    title: '图标',
    key: 'icon',
    width: 30,
    render(row) {
      return h(TheIcon, { icon: row.icon, size: 20 })
    },
  },
  { title: '排序', key: 'order', width: 30, ellipsis: { tooltip: true } },
  { title: '访问路径', key: 'path', width: 60, ellipsis: { tooltip: true } },
  { title: '跳转路径', key: 'redirect', width: 60, ellipsis: { tooltip: true } },
  { title: '组件路径', key: 'component', width: 60, ellipsis: { tooltip: true } },
  {
    title: '保活',
    key: 'keepalive',
    width: 40,
    render(row) {
      return h(NSwitch, {
        size: 'small',
        rubberBand: false,
        value: row.keepalive,
        onUpdateValue: () => handleUpdateKeepalive(row),
      })
    },
  },
  {
    title: '隐藏',
    key: 'is_hidden',
    width: 40,
    render(row) {
      return h(NSwitch, {
        size: 'small',
        rubberBand: false,
        value: row.is_hidden,
        onUpdateValue: () => handleUpdateHidden(row),
      })
    },
  },
  {
    title: '创建日期',
    key: 'created_at',
    width: 70,
    render(row) {
      return h('span', formatDate(row.created_at))
    },
  },
  {
    title: '操作',
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
              size: 'tiny',
              quaternary: true,
              type: 'primary',
              style: `display: ${row.children ? '' : 'none'};`,
              onClick: () => {
                initForm.parent_id = row.id
                initForm.menu_type = 'menu'
                showMenuType.value = false
                menuDisabled.value = false
                handleAdd()
              },
            },
            { default: () => '子菜单', icon: renderIcon('material-symbols:add', { size: 16 }) },
          ),
          [[vPermission, 'post/api/v1/menu/create']],
        ),
        withDirectives(
          h(
            NButton,
            {
              size: 'tiny',
              quaternary: true,
              type: 'info',
              onClick: () => {
                showMenuType.value = false
                handleEdit(row)
              },
            },
            {
              default: () => '编辑',
              icon: renderIcon('material-symbols:edit-outline', { size: 16 }),
            },
          ),
          [[vPermission, 'post/api/v1/menu/update']],
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ id: row.id }, false),
          },
          {
            trigger: () =>
              withDirectives(
                h(
                  NButton,
                  {
                    size: 'tiny',
                    quaternary: true,
                    type: 'error',
                    style: `display: ${row.children && row.children.length > 0 ? 'none' : ''};`, //有子菜单不允许删除
                  },
                  {
                    default: () => '删除',
                    icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
                  },
                ),
                [[vPermission, 'delete/api/v1/menu/delete']],
              ),
            default: () => h('div', {}, '确定删除该菜单吗?'),
          },
        ),
      ]
    },
  },
]
// 修改是否keepalive
async function handleUpdateKeepalive(row) {
  if (!row.id) return
  row.publishing = true
  row.keepalive = row.keepalive === false ? true : false
  await api.updateMenu(row)
  row.publishing = false
  $message?.success(row.keepalive ? '已开启' : '已关闭')
}

// 修改是否隐藏
async function handleUpdateHidden(row) {
  if (!row.id) return
  row.publishing = true
  row.is_hidden = row.is_hidden === false ? true : false
  await api.updateMenu(row)
  row.publishing = false
  $message?.success(row.is_hidden ? '已隐藏' : '已取消隐藏')
}

// 新增菜单(可选目录)
function handleClickAdd() {
  initForm.parent_id = 0
  initForm.menu_type = 'catalog'
  initForm.is_hidden = false
  initForm.order = 1
  initForm.keepalive = true
  showMenuType.value = true
  menuDisabled.value = true
  handleAdd()
}

async function getTreeSelect() {
  const { data } = await api.getMenus()
  const menu = { id: 0, name: '根目录', children: [] }
  menu.children = data
  menuOptions.value = [menu]
}
</script>

<template>
  <!-- 业务页面 -->
  <CommonPage show-footer title="菜单列表">
    <template #action>
      <NButton v-permission="'post/api/v1/menu/create'" type="primary" @click="handleClickAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建根菜单
      </NButton>
    </template>

    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :is-pagination="false"
      :columns="columns"
      :get-data="api.getMenus"
      :single-line="true"
    >
    </CrudTable>

    <!-- 新增/编辑/查看 弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @save="handleSave(getTreeSelect)"
    >
      <!-- 表单 -->
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="80"
        :model="modalForm"
      >
        <NFormItem label="上级菜单" path="parent_id">
          <NTreeSelect
            v-model:value="modalForm.parent_id"
            key-field="id"
            label-field="name"
            :options="menuOptions"
            default-expand-all="true"
            :disabled="menuDisabled"
          />
        </NFormItem>
        <NFormItem
          label="菜单名称"
          path="name"
          :rule="{
            required: true,
            message: '请输入唯一菜单名称',
            trigger: ['input', 'blur'],
          }"
        >
          <NInput v-model:value="modalForm.name" placeholder="请输入唯一菜单名称" />
        </NFormItem>
        <NFormItem
          label="访问路径"
          path="path"
          :rule="{
            required: true,
            message: '请输入访问路径',
            trigger: ['blur'],
          }"
        >
          <NInput v-model:value="modalForm.path" placeholder="请输入访问路径" />
        </NFormItem>
        <NFormItem v-if="modalForm.menu_type === 'menu'" label="组件路径" path="component">
          <NInput
            v-model:value="modalForm.component"
            placeholder="请输入组件路径，例如：/system/user"
          />
        </NFormItem>
        <NFormItem label="跳转路径" path="redirect">
          <NInput
            v-model:value="modalForm.redirect"
            :disabled="modalForm.parent_id !== 0"
            :placeholder="
              modalForm.parent_id !== 0 ? '只有一级菜单可以设置跳转路径' : '请输入跳转路径'
            "
          />
        </NFormItem>
        <NFormItem label="菜单图标" path="icon">
          <IconPicker v-model:value="modalForm.icon" />
        </NFormItem>
        <NFormItem label="显示排序" path="order">
          <NInputNumber v-model:value="modalForm.order" :min="1" />
        </NFormItem>
        <NFormItem label="是否隐藏" path="is_hidden">
          <NSwitch v-model:value="modalForm.is_hidden" />
        </NFormItem>
        <NFormItem label="KeepAlive" path="keepalive">
          <NSwitch v-model:value="modalForm.keepalive" />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
