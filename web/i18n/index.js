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

/**
 * 如果从来没有切换过i18的语言 那么存储里面会缺少*locale*这个变量
 * 我也不晓得为啥子上面 createI18n 不设置这个初始变量
 * 所以用下面的代码来凑合解决一下
 **/
if (!lStorage.get('locale')) {
  lStorage.set('locale', currentLocale || 'cn')
}

export default i18n
