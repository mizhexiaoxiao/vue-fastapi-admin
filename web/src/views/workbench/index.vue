<template>
  <AppPage :show-footer="false">
    <div flex-1>
      <n-card rounded-10>
        <div flex items-center justify-between>
          <div flex items-center>
            <img rounded-full width="60" :src="userStore.avatar" />
            <div ml-10>
              <p text-20 font-semibold>hello, {{ userStore.name }}</p>
              <p mt-5 text-14 op-60>今天又是元气满满的一天!</p>
            </div>
          </div>
          <n-space :size="12" :wrap="false">
            <n-statistic v-for="item in statisticData" :key="item.id" v-bind="item"></n-statistic>
          </n-space>
        </div>
      </n-card>

      <n-card title="项目" size="small" :segmented="true" mt-15 rounded-10>
        <template #header-extra>
          <n-button text type="primary">更多</n-button>
        </template>
        <div flex flex-wrap justify-between>
          <n-card
            v-for="i in 9"
            :key="i"
            class="mb-10 mt-10 w-300 cursor-pointer"
            hover:card-shadow
            title="Vue FastAPI Admin"
            size="small"
          >
            <p op-60>一个基于 Vue3.0、FastAPI、Naive UI 的轻量级后台管理模板</p>
          </n-card>
        </div>
      </n-card>
    </div>
  </AppPage>
</template>

<script setup>
import { useUserStore } from '@/store'

const statisticData = [
  {
    id: 0,
    label: '项目数',
    value: '25',
  },
  {
    id: 1,
    label: '待办',
    value: '4/16',
  },
  {
    id: 2,
    label: '消息',
    value: '12',
  },
]

const userStore = useUserStore()
</script>
