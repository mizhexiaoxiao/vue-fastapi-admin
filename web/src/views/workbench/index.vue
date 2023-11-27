<template>
  <AppPage :show-footer="false">
    <div flex-1>
      <n-card rounded-10>
        <div flex items-center justify-between>
          <div flex items-center>
            <img rounded-full width="60" :src="userStore.avatar" />
            <div ml-10>
              <p text-20 font-semibold>
                {{ $t('views.workbench.text_hello', { username: userStore.name }) }}
              </p>
              <p mt-5 text-14 op-60>{{ $t('views.workbench.text_welcome') }}</p>
            </div>
          </div>
          <n-space :size="12" :wrap="false">
            <n-statistic v-for="item in statisticData" :key="item.id" v-bind="item"></n-statistic>
          </n-space>
        </div>
      </n-card>

      <n-card
        :title="$t('views.workbench.label_project')"
        size="small"
        :segmented="true"
        mt-15
        rounded-10
      >
        <template #header-extra>
          <n-button text type="primary">{{ $t('views.workbench.label_more') }}</n-button>
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
            <p op-60>{{ dummyText }}</p>
          </n-card>
        </div>
      </n-card>
    </div>
  </AppPage>
</template>

<script setup>
import { useUserStore } from '@/store'
import { useI18n } from 'vue-i18n'

const dummyText = '一个基于 Vue3.0、FastAPI、Naive UI 的轻量级后台管理模板'
const { t } = useI18n({ useScope: 'global' })

const statisticData = computed(() => [
  {
    id: 0,
    label: t('views.workbench.label_number_of_items'),
    value: '25',
  },
  {
    id: 1,
    label: t('views.workbench.label_upcoming'),
    value: '4/16',
  },
  {
    id: 2,
    label: t('views.workbench.label_information'),
    value: '12',
  },
])

const userStore = useUserStore()
</script>
