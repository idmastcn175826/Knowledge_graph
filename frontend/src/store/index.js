import { defineStore } from 'pinia'

// 主store
export const useMainStore = defineStore('main', {
  state: () => ({
    // 加载状态
    loading: false,
    // 错误信息
    error: null,
    // 当前用户信息
    user: null
  }),
  actions: {
    // 设置加载状态
    setLoading(status) {
      this.loading = status
    },
    // 设置错误信息
    setError(message) {
      this.error = message
    },
    // 清除错误信息
    clearError() {
      this.error = null
    },
    // 设置用户信息
    setUser(userInfo) {
      this.user = userInfo
    },
    // 退出登录
    logout() {
      this.user = null
      // 可以在这里添加清除本地存储等操作
    }
  }
})

// 知识图谱相关store
export const useKgStore = defineStore('knowledgeGraph', {
  state: () => ({
    // 当前图谱数据
    currentGraph: null,
    // 图谱列表
    graphList: []
  }),
  actions: {
    // 设置当前图谱
    setCurrentGraph(graphData) {
      this.currentGraph = graphData
    },
    // 更新图谱列表
    updateGraphList(list) {
      this.graphList = list
    },
    // 添加新图谱到列表
    addGraph(graph) {
      this.graphList.push(graph)
    }
  }
})
    