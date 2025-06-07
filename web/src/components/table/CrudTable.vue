<template>
  <div v-bind="$attrs">
    <QueryBar v-if="$slots.queryBar" mb-30 @search="handleSearch" @reset="handleReset">
      <slot name="queryBar" />
    </QueryBar>

    <n-data-table
      :remote="remote"
      :loading="loading"
      :columns="columns"
      :data="tableData"
      :scroll-x="scrollX"
      :row-key="(row) => row[rowKey]"
      :pagination="isPagination ? pagination : false"
      :default-sort="props.defaultSort"
      :sorter="sorterState"
      @update:checked-row-keys="onChecked"
      @update:page="onPageChange"
      @update:sorter="onSorterChange"
    />
  </div>
</template>

<script setup>
import { onMounted, nextTick } from 'vue'
const props = defineProps({
  /**
   * @remote true: 后端分页  false： 前端分页
   */
  remote: {
    type: Boolean,
    default: true,
  },
  /**
   * @remote 是否分页
   */
  isPagination: {
    type: Boolean,
    default: true,
  },
  scrollX: {
    type: Number,
    default: 450,
  },
  rowKey: {
    type: String,
    default: 'id',
  },
  columns: {
    type: Array,
    required: true,
  },
  /** queryBar中的参数 */
  queryItems: {
    type: Object,
    default: () => ({}),
  },
  /** 额外的参数 */
  extraParams: {
    type: Object,
    default: () => ({}),
  },
  /** 获取数据的方法 */
  getData: {
    type: Function,
    required: true,
  },
  /** 默认排序 */
  defaultSort: {
    type: Object,
    default: () => ({ columnKey: 'created_at', order: 'descend' }),
  },
})

const emit = defineEmits(['update:queryItems', 'onChecked', 'onDataChange', 'update:sorter'])
const loading = ref(false)
const initQuery = { ...props.queryItems }
const tableData = ref([])
const pagination = reactive({
  page: 1,
  page_size: 10,
  pageSizes: [10, 20, 50, 100],
  showSizePicker: true,
  prefix({ itemCount }) {
    return `共 ${itemCount} 条`
  },
  onChange: (page) => {
    pagination.page = page
  },
  onUpdatePageSize: (pageSize) => {
    pagination.page_size = pageSize
    pagination.page = 1
    handleQuery()
  },
})

async function handleQuery() {
  try {
    loading.value = true
    let paginationParams = {}
    // 如果非分页模式或者使用前端分页,则无需传分页参数
    if (props.isPagination && props.remote) {
      paginationParams = { page: pagination.page, page_size: pagination.page_size }
    }
    const { data, total } = await props.getData({
      ...props.queryItems,
      ...props.extraParams,
      ...paginationParams,
    })
    tableData.value = data
    pagination.itemCount = total || 0
  } catch (error) {
    tableData.value = []
    pagination.itemCount = 0
  } finally {
    emit('onDataChange', tableData.value)
    loading.value = false
  }
}
function handleSearch() {
  pagination.page = 1
  handleQuery()
}
async function handleReset() {
  const queryItems = { ...props.queryItems }
  for (const key in queryItems) {
    queryItems[key] = null
  }
  // 强制重置排序状态为默认倒序
  sorterState.value = { ...props.defaultSort };
  emit('update:queryItems', { ...queryItems, ...initQuery })
  emit('update:sorter', sorterState.value);
  await nextTick()
  pagination.page = 1
  // 强制触发搜索以应用排序状态
  handleQuery()
}
function onPageChange(currentPage) {
  pagination.page = currentPage
  if (props.remote) {
    handleQuery()
  }
}
function onChecked(rowKeys) {
  if (props.columns.some((item) => item.type === 'selection')) {
    emit('onChecked', rowKeys)
  }
}

const sorterState = ref(props.defaultSort)

// 处理排序变化
function onSorterChange(sorter) {
  // 如果 sorter.order 为 null (清除排序) 并且是当前默认的排序列
  if (!sorter.order && sorter.columnKey === props.defaultSort.columnKey) {
    // 将 sorterState 恢复为默认排序状态
    sorterState.value = { ...props.defaultSort };
  } else {
    sorterState.value = sorter;
  }
  // 发送更新后的 sorterState 给父组件
  emit('update:sorter', sorterState.value);
}

// 组件挂载时触发初始排序
onMounted(async () => {
  if (props.defaultSort) {
    emit('update:sorter', props.defaultSort);
  }
  // Ensure parent onMounted (which sets initial queryItems) runs before initial search
  await nextTick(); 
  handleQuery();
});

defineExpose({
  handleSearch,
  handleReset,
  tableData,
  sorterState,
})
</script>
