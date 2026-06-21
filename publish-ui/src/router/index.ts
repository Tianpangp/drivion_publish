import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/facilities'
      },
      {
        path: '/facilities',
        name: 'Facilities',
        component: () => import('../views/Facilities.vue'),
        meta: { title: 'facilities' }
      },
      {
        path: '/drivers',
        name: 'Drivers',
        component: () => import('../views/Drivers.vue'),
        meta: { title: 'drivers' }
      },
      {
        path: '/autounit',
        name: 'AutoUnit',
        component: () => import('../views/AutoUnit.vue'),
        meta: { title: 'autounit' }
      },
      {
        path: '/interfaces',
        name: 'Interfaces',
        component: () => import('../views/Interfaces.vue'),
        meta: { title: 'interfaces' }
      },
      {
        path: '/deployment',
        name: 'Deployment',
        component: () => import('../views/Deployment.vue'),
        meta: { title: 'deployment' }
      },
      {
        path: '/logs',
        name: 'Logs',
        component: () => import('../views/Logs.vue'),
        meta: { title: 'logs' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  
  if (to.meta.requiresAuth !== false && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
