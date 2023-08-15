import { lStorage } from '@/utils'

const TOKEN_CODE = 'access_token'

export function getToken() {
  return lStorage.get(TOKEN_CODE)
}

export function setToken(token) {
  lStorage.set(TOKEN_CODE, token)
}

export function removeToken() {
  lStorage.remove(TOKEN_CODE)
}

// export async function refreshAccessToken() {
//   const tokenItem = lStorage.getItem(TOKEN_CODE)
//   if (!tokenItem) {
//     return
//   }
//   const { time } = tokenItem
//   // token生成或者刷新后30分钟内不执行刷新
//   if (new Date().getTime() - time <= 1000 * 60 * 30) return
//   try {
//     const res = await api.refreshToken()
//     setToken(res.data.token)
//   } catch (error) {
//     console.error(error)
//   }
// }
