import { getToken } from '@/utils'
import { resolveResError } from './helpers'

export function reqResolve(config) {
  // 处理不需要token的请求
  if (config.noNeedToken) {
    return config
  }

  const token = getToken()
  if (token) {
    config.headers.token = config.headers.token || token
  }

  return config
}

export function reqReject(error) {
  return Promise.reject(error)
}

export function resResolve(response) {
  const { data, status, statusText } = response
  if (data?.code !== 200) {
    const code = data?.code ?? status
    /** 根据code处理对应的操作，并返回处理后的message */
    const message = resolveResError(code, data?.msg ?? statusText)
    window.$message?.error(message, { keepAliveOnHover: true })
    return Promise.reject({ code, message, error: data || response })
  }
  return Promise.resolve(data)
}

let isDialogShow = false //解决多个请求弹出多个dialog

export async function resReject(error) {
  if (!error || !error.response) {
    const code = error?.code
    /** 根据code处理对应的操作，并返回处理后的message */
    const message = resolveResError(code, error.message)
    window.$message?.error(message)
    return Promise.reject({ code, message, error })
  }
  const { data, status } = error.response
  if (data?.code === 401) {
    if (isDialogShow) return
    try {
      isDialogShow = true
      await new Promise((resolve, reject) => {
        $dialog.confirm({
          title: '系统提示',
          type: 'warning',
          content: '账号登录已过期，您可以继续留在该页面，或者重新登录',
          positiveText: '重新登录',
          negativeText: '取消',
          confirm() {
            isDialogShow = false
            location.reload()
            resolve() // 解决 Promise 以继续执行
          },
          cancel() {
            isDialogShow = false
            reject(new Error('对话框已取消')) // 拒绝 Promise 以停止执行
          },
        })
      })
    } catch (error) {
      isDialogShow = false
      console.log('resReject error', error)
      return
    }
  }
  // 后端返回的response数据
  const code = data?.code ?? status
  const message = resolveResError(code, data?.msg ?? error.message)
  window.$message?.error(message, { keepAliveOnHover: true })
  return Promise.reject({ code, message, error: error.response?.data || error.response })
}
