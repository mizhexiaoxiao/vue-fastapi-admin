import { lStorage } from '@/utils'

export const activeTag = lStorage.get('activeTag')
export const tags = lStorage.get('tags')

export const WITHOUT_TAG_PATHS = ['/404', '/login']
