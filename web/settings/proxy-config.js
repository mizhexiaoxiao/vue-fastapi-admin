const proxyConfigMappings = {
  dev: {
    prefix: '/url-patten',
    target: 'http://127.0.0.1:9999/api/v1',
  },
  test: {
    prefix: '/url-patten',
    target: 'http://127.0.0.1:9999',
  },
  prod: {
    prefix: '/url-patten',
    target: 'http://127.0.0.1:9999',
  },
}

export function getProxyConfig(envType = 'dev') {
  return proxyConfigMappings[envType]
}
