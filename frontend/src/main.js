import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/styles/index.css'

// 创建Pinia实例
const pinia = createPinia()

// 创建应用实例
const app = createApp(App)

// 安装插件
app.use(pinia)
app.use(router)

// 挂载应用
app.mount('#app')
    