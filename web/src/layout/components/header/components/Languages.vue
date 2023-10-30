<template>
  <n-dropdown :options="options" @select="handleChangeLocale" v-model="locale">
    <n-icon mr-20 size="18" style="cursor: pointer">
      <icon-mdi:globe/>
    </n-icon>
  </n-dropdown>
</template>

<script setup>
import {useI18n} from 'vue-i18n'

const {availableLocales, locale,} = useI18n()

const options = []
availableLocales.forEach(locale => {
  options.push({
    label: locale,
    key: locale
  })
})

const handleChangeLocale = (value) => {
  locale.value = value
}
</script>
