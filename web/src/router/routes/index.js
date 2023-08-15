const Layout = () => import('@/layout/index.vue')

export const basicRoutes = [
  {
    name: '工作台',
    path: '/',
    component: Layout,
    redirect: '/workbench', // 默认跳转到首页
    children: [
      {
        path: 'workbench',
        component: () => import('@/views/workbench/index.vue'),
        name: '工作台',
        meta: {
          title: '工作台',
          icon: 'icon-park-outline:workbench',
          affix: true,
        },
      },
    ],
    meta: { order: 0 },
  },
  {
    name: '个人中心',
    path: '/profile',
    component: Layout,
    isHidden: true,
    children: [
      {
        path: '/profile',
        component: () => import('@/views/profile/index.vue'),
        name: '个人中心',
        meta: {
          title: '个人中心',
          icon: 'user',
          affix: true,
        },
      },
    ],
    meta: { order: 99 },
  },
  {
    name: '403',
    path: '/403',
    component: () => import('@/views/error-page/403.vue'),
    isHidden: true,
  },
  {
    name: '404',
    path: '/404',
    component: () => import('@/views/error-page/404.vue'),
    isHidden: true,
  },
  {
    name: 'Login',
    path: '/login',
    component: () => import('@/views/login/index.vue'),
    isHidden: true,
    meta: {
      title: '登录页',
    },
  },
]

export const NOT_FOUND_ROUTE = {
  name: 'NotFound',
  path: '/:pathMatch(.*)*',
  redirect: '/404',
  isHidden: true,
}

export const EMPTY_ROUTE = {
  name: 'Empty',
  path: '/:pathMatch(.*)*',
  component: null,
}

const modules = import.meta.glob('@/views/**/route.js', { eager: true })
const asyncRoutes = []
Object.keys(modules).forEach((key) => {
  asyncRoutes.push(modules[key].default)
})

// 加载 views 下每个模块的 index.vue 文件
const vueModules = import.meta.glob('@/views/**/index.vue')

export { asyncRoutes, vueModules }
