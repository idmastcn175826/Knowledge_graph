// 1. 引入 Vue Router 核心函数（Vue 3 + Vue Router 4 必须这样引入）
import { createRouter, createWebHistory } from 'vue-router'

// 2. 引入你的页面组件（确保这些组件文件存在于 src/views 下，路径不能错）
// 注意：如果你的页面文件名字/路径不同，需要对应修改这里的 import 路径
import Home from '../views/Home.vue'       // 首页
import KGCreate from '../views/KGCreate.vue' // 图谱创建页
import KGView from '../views/KGView.vue'   // 图谱展示页

// 3. 配置路由规则（每个路由对应一个页面）
const routes = [
  {
    path: '/',               // 访问路径（首页）
    name: 'Home',            // 路由名称（可选，用于编程式导航）
    component: Home          // 对应渲染的组件
  },
  {
    path: '/kg/create',      // 图谱创建页路径
    name: 'KGCreate',
    component: KGCreate
  },
  {
    path: '/kg/view',        // 图谱展示页路径
    name: 'KGView',
    component: KGView
  },
  // 404 路由：匹配不到任何路径时，重定向到首页（避免空白页）
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

// 4. 创建路由实例
const router = createRouter({
  // 路由模式：HTML5 History 模式（无 # 号）
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: routes             // 传入上面定义的路由规则
})

// 5. 导出路由实例（供 main.js 引入）
export default router