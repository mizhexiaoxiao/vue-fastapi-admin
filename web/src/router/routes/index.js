import i18n from '~/i18n'
const { t } = i18n.global

const Layout = () => import('@/layout/index.vue')

export const basicRoutes = [
  {
    path: '/',
    redirect: '/workbench', // 默认跳转到首页
    meta: { order: 0 },
  },
  {
    name: t('views.workbench.label_workbench'),
    path: '/workbench',
    component: Layout,
    children: [
      {
        path: '',
        component: () => import('@/views/workbench/index.vue'),
        name: `${t('views.workbench.label_workbench')}Default`,
        meta: {
          title: t('views.workbench.label_workbench'),
          icon: 'icon-park-outline:workbench',
          affix: true,
        },
      },
    ],
    meta: { order: 1 },
  },
  {
    name: t('views.profile.label_profile'),
    path: '/profile',
    component: Layout,
    isHidden: true,
    children: [
      {
        path: '',
        component: () => import('@/views/profile/index.vue'),
        name: `${t('views.profile.label_profile')}Default`,
        meta: {
          title: t('views.profile.label_profile'),
          icon: 'user',
          affix: true,
        },
      },
    ],
    meta: { order: 99 },
  },
  {
    name: 'ErrorPage',
    path: '/error-page',
    component: Layout,
    redirect: '/error-page/404',
    meta: {
      title: t('views.errors.label_error'),
      icon: 'mdi:alert-circle-outline',
      order: 99,
    },
    children: [
      {
        name: 'ERROR-401',
        path: '401',
        component: () => import('@/views/error-page/401.vue'),
        meta: {
          title: '401',
          icon: 'material-symbols:authenticator',
        },
      },
      {
        name: 'ERROR-403',
        path: '403',
        component: () => import('@/views/error-page/403.vue'),
        meta: {
          title: '403',
          icon: 'solar:forbidden-circle-line-duotone',
        },
      },
      {
        name: 'ERROR-404',
        path: '404',
        component: () => import('@/views/error-page/404.vue'),
        meta: {
          title: '404',
          icon: 'tabler:error-404',
        },
      },
      {
        name: 'ERROR-500',
        path: '500',
        component: () => import('@/views/error-page/500.vue'),
        meta: {
          title: '500',
          icon: 'clarity:rack-server-outline-alerted',
        },
      },
    ],
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
  // --- Certificate Services Routes (User) ---
  {
    name: 'CertificateServices',
    path: '/certificate',
    component: Layout,
    redirect: '/certificate/request',
    meta: { 
      title: 'Certificate Services', 
      icon: 'mdi:security', // Match backend icon if possible
      roles: ['user', 'admin'], // Accessible by both, specific endpoints might further restrict
      order: 2, // Example order, adjust as needed
    },
    children: [
      {
        path: 'request',
        name: 'CertificateRequestForm',
        component: () => import('@/views/certificate/RequestForm.vue'),
        meta: { title: 'Request New Certificate', icon: 'mdi:file-document-plus-outline', roles: ['user', 'admin'] },
      },
      {
        path: 'my-requests',
        name: 'MyCertificateRequestsList',
        component: () => import('@/views/certificate/MyRequestsList.vue'),
        meta: { title: 'My Certificate Requests', icon: 'mdi:list-box-outline', roles: ['user', 'admin'] },
      },
    ],
  },
  // --- Tools Routes (User) ---
  {
    name: 'Tools',
    path: '/tools',
    component: Layout,
    redirect: '/tools/pem-to-pfx',
    meta: { 
      title: 'Tools', 
      icon: 'mdi:tools', 
      roles: ['user', 'admin'],
      order: 3, 
    },
    children: [
      {
        path: 'pem-to-pfx',
        name: 'PemToPfxConverter',
        component: () => import('@/views/tools/PemToPfxConverter.vue'),
        meta: { title: 'PEM to PFX Converter', icon: 'mdi:key-swap', roles: ['user', 'admin'] },
      },
    ],
  },
  // --- Admin Certificate Management Routes (nested under System Management) ---
  // Assuming '/system' is already defined for admin layout.
  // These routes will be added to the children of the existing '/system' route if needed,
  // or defined similarly if they are top-level from an admin perspective.
  // For now, adding as a new top-level admin section for clarity.
  // If sidebar auto-generation depends on parent-child structure matching backend,
  // these should be children of the "System Management" route object if it exists.
  // Let's assume for now they are added to an admin layout.
  // The backend menu structure has "Certificate Admin" under "System Management".
  // So, the path should be /system/certificate-admin/...
  // We need to find the existing '/system' route and add children to it.
  // This part is tricky with a simple diff. I will define them separately and then
  // conceptually they should be merged into the children of the '/system' route.
  // For now, I'll add them as if they could be top-level admin routes for structure.
  // The actual integration into the nested layout might require manual merge or a more complex diff.

  // The backend component paths are:
  // "/admin/certificate/RequestManagement"
  // "/admin/certificate/CAManagement"
  // The frontend paths should match these for consistency.
  // The backend path for parent is "/system/certificate-admin"
  
  // This requires modifying an existing route object's children, which is hard with replace_with_git_merge_diff
  // I will define the routes here, and in the summary mention they need to be correctly nested.
  // Adding Admin Certificate Management routes.
  // The backend Menu structure implies these are under "/system".
  // We will create a /system parent if one isn't already obviously in basicRoutes,
  // or add to an existing one if found and modifiable by this tool.
  // Given no /system in basicRoutes shown, creating a new top-level /system for these.
  {
    name: 'SystemManagementCertAdmin', // A unique name for this section if it's new top-level
    path: '/system', // Base for system related admin functions
    component: Layout,
    redirect: '/system/certificate-admin/requests', // Default redirect for this new section
    meta: { 
      title: 'System Management', // Assuming a general title for /system if it wasn't there
      icon: 'carbon:gui-management', // Match backend icon for "System Management"
      roles: ['admin'], // Only admins should see this system section
      order: 1, // Ensure it's ordered similar to backend
    },
    children: [
      {
        path: 'certificate-admin', // Path: /system/certificate-admin
        name: 'CertificateAdmin',
        // component: () => import('@/layout/components/RouterParentView.vue'), // Common pattern for nested menu
        // For simplicity, if RouterParentView or similar isn't confirmed, use a redirect or a dummy component.
        // Using redirect to its first child.
        redirect: '/system/certificate-admin/requests',
        meta: { title: 'Certificate Admin', icon: 'mdi:shield-key', roles: ['admin'] },
        children: [
          {
            path: 'requests', // Full path: /system/certificate-admin/requests
            name: 'AdminCertificateRequestManagement',
            component: () => import('@/views/admin/certificate/RequestManagement.vue'),
            meta: { title: 'Manage Cert Requests', icon: 'mdi:clipboard-list-outline', roles: ['admin'] },
          },
          {
            path: 'cas', // Full path: /system/certificate-admin/cas
            name: 'AdminCAManagement',
            component: () => import('@/views/admin/certificate/CAManagement.vue'),
            meta: { title: 'Manage CAs', icon: 'mdi:shield-crown-outline', roles: ['admin'] },
          },
        ]
      }
      // Other existing /system children (like user, role, menu management) would ideally be here.
      // This diff only adds the certificate admin part.
    ]
  }
]

// Removed the separate adminCertificateRoutes export as it's merged above.

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
