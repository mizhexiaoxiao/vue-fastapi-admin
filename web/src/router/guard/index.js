import { createPageLoadingGuard } from './page-loading-guard'
import { createPageTitleGuard } from './page-title-guard'
import { createAuthGuard } from './auth-guard'

export function setupRouterGuard(router) {
  createPageLoadingGuard(router)
  createAuthGuard(router)
  createPageTitleGuard(router)
}
