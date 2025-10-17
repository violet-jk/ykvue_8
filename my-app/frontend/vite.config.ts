import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url)),
        }
    },
    server: {
        port: 5174,
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:8001',
                changeOrigin: true,
            },
        },
    },
    build: {
        // 提高块大小警告限制
        chunkSizeWarningLimit: 1000,
        rollupOptions: {
            output: {
                // 手动分包配置
                manualChunks: {
                    // Vue 核心库
                    vue: ['vue', 'vue-router'],
                    // Element Plus UI 库
                    'element-plus': ['element-plus', '@element-plus/icons-vue'],
                    // Highcharts 图表库
                    highcharts: ['highcharts', 'highcharts-boost'],
                    // 工具库
                    utils: ['axios']
                }
            }
        },
        // 启用压缩
        minify: true,
        // 启用源码映射（生产环境可关闭）
        sourcemap: false,
        // 构建目标
        target: 'esnext',
        // CSS 代码分割
        cssCodeSplit: true,
    },
    // 优化依赖预构建
    optimizeDeps: {
        include: ['vue', 'vue-router', 'axios','highcharts'],
    }
})