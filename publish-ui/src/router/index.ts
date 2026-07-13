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
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/equipment'
      },
      {
        path: '/equipment',
        name: 'Equipment',
        component: () => import('../views/Equipment.vue'),
        meta: { title: 'equipment' }
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
        path: '/approvals',
        name: 'Approvals',
        component: () => import('../views/Approvals.vue'),
        meta: { title: 'approvals' }
      },
      {
        path: '/logs',
        name: 'Logs',
        component: () => import('../views/Logs.vue'),
        meta: { title: 'logs' }
      },
      {
        path: '/users',
        name: 'Users',
        component: () => import('../views/Users.vue'),
        meta: { title: 'users', permission: 'user:manage' }
      },
      {
        path: '/profile',
        name: 'Profile',
        component: () => import('../views/Profile.vue'),
        meta: { title: 'profile' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  
  if (to.meta.requiresAuth !== false && !token) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && token) {
    next('/')
  } else if (to.meta.permission) {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    if (!(user.permissions || []).includes(to.meta.permission)) next('/')
    else next()
  } else {
    next()
  }
})

export default router
