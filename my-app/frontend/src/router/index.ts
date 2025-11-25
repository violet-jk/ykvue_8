import {createRouter, createWebHistory} from 'vue-router'
import type {RouteRecordRaw} from 'vue-router'
import { ElMessage } from 'element-plus'

// 使用懒加载替代静态导入
const Charts = () => import('../components/Charts.vue')
const Login = () => import('../components/Login.vue')
const Home = () => import('../components/Home.vue')
const DataTable = () => import('../components/DataTable.vue')

const routes: RouteRecordRaw[] = [
    {path: '/', name: 'root', component: Home, meta: { requiresAuth: true }},
    {path: '/home', name: 'home', component: Home, meta: { requiresAuth: true }},
    {path: '/charts', name: 'charts', component: Charts, meta: { requiresAuth: true }},
    {path: '/data-table', name: 'data-table', component: DataTable, meta: { requiresAuth: true }},
    {path: '/login', name: 'login', component: Login, meta: { requiresAuth: false }},
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

// 路由守卫
router.beforeEach((to, _from, next) => {
    const token = localStorage.getItem('auth_token')

    // 如果路由需要认证
    if (to.meta.requiresAuth) {
        if (token) {
            // 有token，验证token是否有效
            fetch('/api/auth/verify', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            })
            .then(response => {
                if (response.ok) {
                    next()
                } else {
                    // token无效，清除并跳转到登录页
                    localStorage.removeItem('auth_token')
                    ElMessage.warning('登录已过期，请重新登录')
                    next('/login')
                }
            })
            .catch(() => {
                localStorage.removeItem('auth_token')
                ElMessage.error('验证失败，请重新登录')
                next('/login')
            })
        } else {
            // 没有token，跳转到登录页
            ElMessage.warning('请先登录')
            next('/login')
        }
    } else {
        // 不需要认证的页面
        if (to.path === '/login' && token) {
            // 已登录用户访问登录页，重定向到首页
            next('/home')
        } else {
            next()
        }
    }
})


export default router
