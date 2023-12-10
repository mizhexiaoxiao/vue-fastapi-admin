export function useResize(el, cb) {
  const observer = new ResizeObserver((entries) => {
    cb(entries[0].contentRect)
  })
  observer.observe(el)
  return observer
}

const install = (app) => {
  let observer

  app.directive('resize', {
    mounted(el, binding) {
      observer = useResize(el, binding.value)
    },
    beforeUnmount() {
      observer?.disconnect()
    },
  })
}

useResize.install = install
