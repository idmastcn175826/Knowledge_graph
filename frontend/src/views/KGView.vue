<template>
  <div class="kg-view-container">
    <!-- 页面标题和导航 -->
    <div class="page-header">
      <h2>知识图谱展示</h2>
      <button @click="goBack" class="back-btn">返回首页</button>
    </div>

    <!-- 图谱列表和展示区域 -->
    <div class="graph-section mt-4">
      <div class="graph-list">
        <h3>已创建的图谱</h3>
        <div
          v-for="graph in graphList"
          :key="graph.id"
          class="graph-item"
          @click="selectGraph(graph.id)"
          :class="{ active: currentGraphId === graph.id }"
        >
          {{ graph.name }}
        </div>

        <!-- 无图谱时的提示 -->
        <div v-if="graphList.length === 0" class="no-graph">
          暂无创建的知识图谱，请先去创建
        </div>
      </div>

      <!-- 图谱展示区域 -->
      <div class="graph-display">
        <h3>{{ currentGraphName || '请选择一个图谱' }}</h3>

        <!-- 加载中提示 -->
        <div v-if="loading" class="loading">加载中...</div>

        <!-- 无图谱选择时的占位 -->
        <div
          v-else-if="!currentGraphId && !loading"
          class="placeholder"
        >
          请从左侧选择一个图谱查看
        </div>

        <!-- 图谱容器 -->
        <div
          v-else
          id="view-graph-container"
          class="graph-container"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 1. 引入依赖
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Network } from 'vis-network'
import { DataSet } from 'vis-data'

// 2. 路由实例
const router = useRouter()

// 3. 响应式数据
const graphList = ref([
  // 模拟已创建的图谱列表（实际项目中从后端接口获取）
  { id: 1, name: '人工智能知识图谱' },
  { id: 2, name: '计算机科学图谱' }
])
const currentGraphId = ref(null) // 当前选中的图谱 ID
const currentGraphName = ref('') // 当前选中的图谱名称
const nodes = ref(new DataSet([])) // 图谱节点数据
const edges = ref(new DataSet([])) // 图谱关系数据
let network = ref(null) // 图谱实例
const loading = ref(false) // 加载状态

// 4. 监听当前图谱 ID 变化，切换图谱
watch(currentGraphId, (newId) => {
  if (newId) {
    // 获取当前图谱名称
    const currentGraph = graphList.value.find(g => g.id === newId)
    currentGraphName.value = currentGraph ? currentGraph.name : ''
    // 加载图谱数据
    loadGraphData(newId)
  } else {
    // 未选中图谱时，清空数据和图谱
    currentGraphName.value = ''
    clearGraph()
  }
}, { immediate: true })

// 5. 页面挂载时初始化图谱容器
onMounted(() => {
  initNetworkContainer()
})

// 6. 页面卸载时销毁图谱
onUnmounted(() => {
  if (network.value) {
    network.value.destroy()
  }
})

// 7. 初始化图谱容器（创建空容器，等待数据加载）
const initNetworkContainer = () => {
  const container = document.getElementById('view-graph-container')
  if (!container) return

  // 初始空数据
  const emptyData = { nodes: [], edges: [] }
  const options = {
    nodes: {
      shape: 'ellipse',
      size: 25,
      font: { size: 14, color: '#fff' },
      color: { background: '#3498db', border: '#2980b9' }
    },
    edges: {
      font: { size: 12, color: '#333' },
      color: '#999',
      arrows: { to: { enabled: true } }
    },
    interaction: { dragNodes: true, zoomView: true, panView: true },
    layout: { randomSeed: 3, improvedLayout: true }
  }

  // 创建空图谱实例
  network.value = new Network(container, emptyData, options)
}

// 8. 加载图谱数据（模拟后端接口请求）
const loadGraphData = (graphId) => {
  loading.value = true
  clearGraph() // 先清空现有数据

  // 模拟接口请求延迟（实际项目中替换为 axios 调用）
  setTimeout(() => {
    // 根据图谱 ID 返回不同的模拟数据
    let graphData = { nodes: [], edges: [] }

    if (graphId === 1) {
      // 人工智能知识图谱示例数据
      graphData = {
        nodes: [
          { id: 1, label: '人工智能', type: '领域' },
          { id: 2, label: '机器学习', type: '技术' },
          { id: 3, label: '深度学习', type: '技术' },
          { id: 4, label: '神经网络', type: '模型' },
          { id: 5, label: '计算机视觉', type: '应用' }
        ],
        edges: [
          { from: 1, to: 2, label: '包含' },
          { from: 2, to: 3, label: '包含' },
          { from: 3, to: 4, label: '使用' },
          { from: 1, to: 5, label: '包含' },
          { from: 5, to: 3, label: '基于' }
        ]
      }
    } else if (graphId === 2) {
      // 计算机科学图谱示例数据
      graphData = {
        nodes: [
          { id: 10, label: '计算机科学', type: '学科' },
          { id: 11, label: '数据结构', type: '基础' },
          { id: 12, label: '算法', type: '基础' },
          { id: 13, label: '操作系统', type: '核心课程' },
          { id: 14, label: '计算机网络', type: '核心课程' }
        ],
        edges: [
          { from: 10, to: 11, label: '包含' },
          { from: 10, to: 12, label: '包含' },
          { from: 12, to: 11, label: '依赖' },
          { from: 10, to: 13, label: '包含' },
          { from: 10, to: 14, label: '包含' }
        ]
      }
    }

    // 更新节点和关系数据
    nodes.value.add(graphData.nodes)
    edges.value.add(graphData.edges)

    // 更新图谱展示
    updateNetwork()

    // 关闭加载状态
    loading.value = false
  }, 800)
}

// 9. 更新图谱展示
const updateNetwork = () => {
  const container = document.getElementById('view-graph-container')
  if (!container || !network.value) return

  // 更新图谱数据
  const data = {
    nodes: nodes.value,
    edges: edges.value
  }

  // 销毁现有网络
  if (network.value) {
    network.value.destroy()
  }

  // 创建新网络
  network.value = new Network(container, data, {
    nodes: {
      shape: 'ellipse',
      size: 25,
      font: { size: 14, color: '#fff' },
      color: { background: '#3498db', border: '#2980b9' }
    },
    edges: {
      font: { size: 12, color: '#333' },
      color: '#999',
      arrows: { to: { enabled: true } }
    },
    interaction: { dragNodes: true, zoomView: true, panView: true },
    layout: { randomSeed: 3, improvedLayout: true }
  })
}

// 10. 清空图谱数据
const clearGraph = () => {
  nodes.value.clear()
  edges.value.clear()
  if (network.value) {
    network.value.setData({ nodes: [], edges: [] })
  }
}

// 11. 选择图谱
const selectGraph = (graphId) => {
  currentGraphId.value = graphId
}

// 12. 返回首页
const goBack = () => {
  router.push('/')
}
</script>

<style scoped>
.kg-view-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.back-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #3498db;
  border-radius: 4px;
  background: transparent;
  color: #3498db;
  cursor: pointer;
  transition: all 0.3s;
}

.back-btn:hover {
  background: #3498db;
  color: #fff;
}

.graph-section {
  display: flex;
  gap: 2rem;
}

.graph-list {
  width: 250px;
  border: 1px solid #eee;
  border-radius: 4px;
  padding: 1rem;
  height: 600px;
  overflow-y: auto;
}

.graph-item {
  padding: 0.8rem;
  margin-bottom: 0.5rem;
  border-radius: 4px;
  background: #f5f7fa;
  cursor: pointer;
  transition: all 0.2s;
}

.graph-item:hover {
  background: #e8f4fd;
}

.graph-item.active {
  background: #3498db;
  color: white;
}

.no-graph {
  padding: 2rem 0;
  text-align: center;
  color: #999;
  font-style: italic;
}

.graph-display {
  flex: 1;
  border: 1px solid #eee;
  border-radius: 4px;
  padding: 1rem;
  height: 600px;
  display: flex;
  flex-direction: column;
}

.graph-container {
  flex: 1;
  width: 100%;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}

.placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  border: 1px dashed #ddd;
  border-radius: 4px;
}

.mt-4 {
  margin-top: 1rem;
}
</style>
