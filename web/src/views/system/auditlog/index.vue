<script setup>
import { onMounted, ref } from 'vue'
import { NInput, NSelect, NPopover } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'

import api from '@/api'

defineOptions({ name: '审计日志' })

const $table = ref(null)
const queryItems = ref({})

onMounted(() => {
  $table.value?.handleSearch()
})

function formatTimestamp(timestamp) {
  const date = new Date(timestamp)

  const pad = (num) => num.toString().padStart(2, '0')

  const year = date.getFullYear()
  const month = pad(date.getMonth() + 1) // 月份从0开始，所以需要+1
  const day = pad(date.getDate())
  const hours = pad(date.getHours())
  const minutes = pad(date.getMinutes())
  const seconds = pad(date.getSeconds())

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

// 获取当天的开始时间的时间戳
function getStartOfDayTimestamp() {
  const now = new Date()
  now.setHours(0, 0, 0, 0) // 将小时、分钟、秒和毫秒都设置为0
  return now.getTime()
}

// 获取当天的结束时间的时间戳
function getEndOfDayTimestamp() {
  const now = new Date()
  now.setHours(23, 59, 59, 999) // 将小时设置为23，分钟设置为59，秒设置为59，毫秒设置为999
  return now.getTime()
}

const startOfDayTimestamp = getStartOfDayTimestamp()
const endOfDayTimestamp = getEndOfDayTimestamp()

queryItems.value.start_time = formatTimestamp(startOfDayTimestamp)
queryItems.value.end_time = formatTimestamp(endOfDayTimestamp)

const datetimeRange = ref([startOfDayTimestamp, endOfDayTimestamp])
const handleDateRangeChange = (value) => {
  if (value == null) {
    queryItems.value.start_time = null
    queryItems.value.end_time = null
  } else {
    queryItems.value.start_time = formatTimestamp(value[0])
    queryItems.value.end_time = formatTimestamp(value[1])
  }
}

const methodOptions = [
  {
    label: 'GET',
    value: 'GET',
  },
  {
    label: 'POST',
    value: 'POST',
  },
  {
    label: 'DELETE',
    value: 'DELETE',
  },
]

function formatJSON(data) {
  try {
    return typeof data === 'string' 
      ? JSON.stringify(JSON.parse(data), null, 2)
      : JSON.stringify(data, null, 2)
  } catch (e) {
    return data || '无数据'
  }
}

const columns = [
  {
    title: '用户名称',
    key: 'username',
    width: 'auto',
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '接口概要',
    key: 'summary',
    align: 'center',
    width: 'auto',
    ellipsis: { tooltip: true },
  },
  {
    title: '功能模块',
    key: 'module',
    align: 'center',
    width: 'auto',
    ellipsis: { tooltip: true },
  },
  {
    title: '请求方法',
    key: 'method',
    align: 'center',
    width: 'auto',
    ellipsis: { tooltip: true },
  },
  {
    title: '请求路径',
    key: 'path',
    align: 'center',
    width: 'auto',
    ellipsis: { tooltip: true },
  },
  {
    title: '状态码',
    key: 'status',
    align: 'center',
    width: 'auto',
    ellipsis: { tooltip: true },
  },
  {
    title: '请求体',
    key: 'request_body',
    align: 'center',
    width: 80,
    render: (row) => {
      return h(
        NPopover,
        {
          trigger: 'hover',
          placement: 'right',
        },
        {
          trigger: () =>
            h('div', { style: 'cursor: pointer;' }, [h(TheIcon, { icon: 'carbon:data-view' })]),
          default: () =>
            h(
              'pre',
              {
                style:
                  'max-height: 400px; overflow: auto; background-color: #f5f5f5; padding: 8px; border-radius: 4px;',
              },
              formatJSON(row.request_args)
            ),
        }
      )
    },
  },
  {
    title: '响应体',
    key: 'response_body',
    align: 'center',
    width: 80,
    render: (row) => {
      return h(
        NPopover,
        {
          trigger: 'hover',
          placement: 'right',
        },
        {
          trigger: () =>
            h('div', { style: 'cursor: pointer;' }, [h(TheIcon, { icon: 'carbon:data-view' })]),
          default: () =>
            h(
              'pre',
              {
                style:
                  'max-height: 400px; overflow: auto; background-color: #f5f5f5; padding: 8px; border-radius: 4px;',
              },
              formatJSON(row.response_body)
            ),
        }
      )
    },
  },
  {
    title: '响应时间(s)',
    key: 'response_time',
    align: 'center',
    width: 'auto',
    ellipsis: { tooltip: true },
  },
  {
    title: '操作时间',
    key: 'created_at',
    align: 'center',
    width: 'auto',
    ellipsis: { tooltip: true },
  },
]
</script>

<template>
  <!-- 业务页面 -->
  <CommonPage>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getAuditLogList"
    >
      <template #queryBar>
        <QueryBarItem label="用户名称" :label-width="70">
          <NInput
            v-model:value="queryItems.username"
            clearable
            type="text"
            placeholder="请输入用户名称"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="功能模块" :label-width="70">
          <NInput
            v-model:value="queryItems.module"
            clearable
            type="text"
            placeholder="请输入功能模块"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="接口概要" :label-width="70">
          <NInput
            v-model:value="queryItems.summary"
            clearable
            type="text"
            placeholder="请输入接口概要"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="请求方法" :label-width="70">
          <NSelect
            v-model:value="queryItems.method"
            style="width: 180px"
            :options="methodOptions"
            clearable
            placeholder="请选择请求方法"
          />
        </QueryBarItem>
        <QueryBarItem label="请求路径" :label-width="70">
          <NInput
            v-model:value="queryItems.path"
            clearable
            type="text"
            placeholder="请输入请求路径"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="状态码" :label-width="60">
          <NInput
            v-model:value="queryItems.status"
            clearable
            type="text"
            placeholder="请输入状态码"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="操作时间" :label-width="70">
          <NDatePicker
            v-model:value="datetimeRange"
            type="datetimerange"
            clearable
            placeholder="请选择时间范围"
            @update:value="handleDateRangeChange"
          />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>
</template>
