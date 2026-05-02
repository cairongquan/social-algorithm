import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue')
  },
  {
    path: '/',
    name: 'Articles',
    component: () => import('@/views/ArticlesView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/articles/create',
    name: 'ArticleCreate',
    component: () => import('@/views/ArticleEditView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/articles/:id/edit',
    name: 'ArticleEdit',
    component: () => import('@/views/ArticleEditView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/tags',
    name: 'Tags',
    component: () => import('@/views/TagsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/square',
    name: 'Square',
    component: () => import('@/views/SquareView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/topology',
    name: 'Topology',
    component: () => import('@/views/TopologyView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/algorithm',
    name: 'AdminAlgorithm',
    component: () => import('@/views/AdminAlgorithmView.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if ((to.name === 'Topology' || to.name === 'AdminAlgorithm') && !authStore.isAdmin) {
    next('/')
  } else {
    next()
  }
})

export default router
