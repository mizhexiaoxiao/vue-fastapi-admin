import axios from 'axios'
import { resReject, resResolve, reqReject, reqResolve } from './interceptors'
import { getProxyConfig } from '../../../settings'

const proxyConfig = getProxyConfig(import.meta.env.VITE_PROXY_TYPE)
const isUseProxy = false

export function createAxios(options = {}) {
  const defaultOptions = {
    timeout: 12000,
  }
  const service = axios.create({
    ...defaultOptions,
    ...options,
  })
  service.interceptors.request.use(reqResolve, reqReject)
  service.interceptors.response.use(resResolve, resReject)
  return service
}

export const request = createAxios({
  baseURL: isUseProxy ? proxyConfig.prefix : proxyConfig.target,
})
