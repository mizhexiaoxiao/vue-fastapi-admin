import { createI18n } from 'vue-i18n'
import { lStorage } from '@/utils'

import messages from './messages'

const currentLocale = lStorage.get('locale')

const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: currentLocale || 'cn',
  fallbackLocale: 'cn',
  messages: messages,
})

export default i18n
