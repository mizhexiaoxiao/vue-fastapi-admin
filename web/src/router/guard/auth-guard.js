import { getToken, isNullOrWhitespace } from '@/utils'

const WHITE_LIST = ['/login', '/404', '/forgot-password', /^\/reset-password\/.*/]
export function createAuthGuard(router) {
  router.beforeEach(async (to) => {
    const token = getToken()
    /** 没有token的情况 */
    /** 添加了正则路由 **/
    if (isNullOrWhitespace(token)) {
      // 检查目标路径是否在白名单中
      const isInWhiteList = WHITE_LIST.some((pattern) => {
        if (typeof pattern === 'string') {
          return pattern === to.path // 匹配普通路径
        }
        return pattern.test(to.path) // 匹配正则表达式
      })
      if (isInWhiteList) return true
      return { path: 'login', query: { ...to.query, redirect: to.path } }
    }

    /** 有token的情况 */
    if (to.path === '/login') return { path: '/' }
    /** 所有拼接的没有权限的非法路由都会跳转到 404, 而不是一个白板*/
    if (router.getRoutes().some((route) => route.path === to.path)) {
      return true
    }
    return true
  })
}
