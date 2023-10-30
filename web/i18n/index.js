import { createI18n } from 'vue-i18n'

import messages from './messages'


const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: 'en',
  fallbackLocale: 'en',
  messages: messages
})

export default i18n