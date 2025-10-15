import {createApp} from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn';
import 'element-plus/dist/index.css'
import './assets/fonts.css' // 导入本地字体定义
import './style.css' // 确保全局样式被导入
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import router from './router'

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus,{
    locale: zhCn,
})
app.use(router).mount('#app')