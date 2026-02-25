import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/main',
    name: 'Main',
    component: () => import('@/views/TestMain.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/test',
    name: 'TestExecution',
    component: () => import('@/views/TestExecution.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/TestHistory.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/testplan',
    name: 'TestPlan',
    component: () => import('@/views/TestPlanManage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/config',
    name: 'Config',
    component: () => import('@/views/SystemConfig.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/projects',
    name: 'ProjectManage',
    component: () => import('@/views/ProjectManage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/users',
    name: 'UserManage',
    component: () => import('@/views/UserManage.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/main')
  } else {
    next()
  }
})

export default router
