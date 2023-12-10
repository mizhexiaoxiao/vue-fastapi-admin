<template>
  <n-dropdown trigger="click"  :options="options" @select="handleChangeLocale">
    <n-icon mr-20 size="18" style="cursor: pointer">
      <icon-mdi:globe />
    </n-icon>
  </n-dropdown>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/store';
import { useRouter } from 'vue-router';
import { renderIcon } from '@/utils';

const router = useRouter()
const appStore = useAppStore()
const { availableLocales, t } = useI18n()

const options = computed(() => {
  let select = []
  availableLocales.forEach((locale) => {
    select.push({
      label: t('lang', 1, { locale: locale }),
      key: locale,
      icon: renderIcon(locale === appStore.locale ? 'mdi:check' : '')
    })
  })
  return select
})

const handleChangeLocale = (value) => {
  if (value !== appStore.locale) {
    appStore.setLocale(value)
    // reload page to apply change
    router.go()
  }
}
</script>
