import {createRouter, createWebHistory} from 'vue-router'
import type {RouteRecordRaw} from 'vue-router'

// 使用懒加载替代静态导入
const Charts = () => import('../components/Charts.vue')

const routes: RouteRecordRaw[] = [
    {path: '/', name: 'home', component: Charts, meta: {requiresAuth: true}},
    {path: '/charts/:device_id?', name: 'charts', component: Charts, meta: {requiresAuth: true}},
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

// 路由守卫
router.beforeEach((to, _from, next) => {
    // 使用新的token验证逻辑
    const isTokenValid = (): boolean => {
        const token = localStorage.getItem('access_token');
        const timestamp = localStorage.getItem('token_timestamp');
        const lastActivity = localStorage.getItem('last_activity');

        if (!token || !timestamp || !lastActivity) {
            return false;
        }

        const now = Date.now();
        const tokenAge = now - parseInt(timestamp);
        const inactivityTime = now - parseInt(lastActivity);

        // 检查token是否超过30天
        if (tokenAge > 30 * 24 * 60 * 60 * 1000) {
            console.log('Token已过期（超过30天）');
            clearAuthData();
            return false;
        }

        // 检查是否超过7天未活动
        if (inactivityTime > 7 * 24 * 60 * 60 * 1000) {
            console.log('登录状态已过期（7天未活动）');
            clearAuthData();
            return false;
        }

        // Token有效，更新最后活动时间
        localStorage.setItem('last_activity', Date.now().toString());
        return true;
    };

    // 清除认证数据
    const clearAuthData = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('token_timestamp');
        localStorage.removeItem('last_activity');
        localStorage.removeItem('user');
    };

    const token = localStorage.getItem('access_token');
    const userStr = localStorage.getItem('user');
    const user = userStr ? JSON.parse(userStr) : null;

    // 检查是否需要认证
    if (to.meta.requiresAuth) {
        if (!token || !isTokenValid()) {
            next('/login');
            return;
        }
    }

    // 检查是否需要管理员权限
    if (to.meta.requiresAdmin && (!user || user.role !== 'admin')) {
        next('/');
        return;
    }

    // 如果已登录且访问登录页，重定向到首页
    if (to.name === 'login' && token && isTokenValid()) {
        next('/');
        return;
    }

    next();
});

export default router
