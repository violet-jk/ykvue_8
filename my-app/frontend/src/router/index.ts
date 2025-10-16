import {createRouter, createWebHistory} from 'vue-router'
import type {RouteRecordRaw} from 'vue-router'

// 使用懒加载替代静态导入
const Charts = () => import('../components/Charts.vue')

const routes: RouteRecordRaw[] = [
    {path: '/', name: 'home', component: Charts},
    {path: '/charts', name: 'charts', component: Charts},
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

// 路由守卫


export default router
