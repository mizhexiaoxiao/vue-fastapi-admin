import { createI18n } from 'vue-i18n'
import { sStorage } from '@/utils'

import messages from './messages'

const currentLocale = sStorage.get('locale')

const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: currentLocale || 'en',
  fallbackLocale: 'en',
  messages: messages,
})

export default i18n
