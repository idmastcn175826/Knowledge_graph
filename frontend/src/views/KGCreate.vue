<template>
  <div class="kg-create-container">
    <!-- 页面标题和导航 -->
    <div class="page-header">
      <h2>创建知识图谱</h2>
      <button @click="goBack" class="back-btn">返回首页</button>
    </div>

    <!-- 图谱配置区域 -->
    <div class="config-section mt-4">
      <div class="form-group">
        <label>图谱名称：</label>
        <input
          v-model="graphName"
          type="text"
          placeholder="请输入图谱名称"
          class="input-field"
        >
      </div>

      <!-- 节点添加区域 -->
      <div class="node-section mt-4">
        <h3>添加节点</h3>
        <div class="form-group">
          <label>节点标签：</label>
          <input
            v-model="newNode.label"
            type="text"
            placeholder="比如：人工智能"
            class="input-field"
          >
        </div>
        <div class="form-group">
          <label>节点类型：</label>
          <input
            v-model="newNode.type"
            type="text"
            placeholder="比如：概念"
            class="input-field"
          >
        </div>
        <button @click="addNode" class="operate-btn">添加节点</button>
      </div>

      <!-- 关系添加区域 -->
      <div class="edge-section mt-4">
        <h3>添加关系</h3>
        <div class="form-group">
          <label>源节点：</label>
          <select v-model="newEdge.from" class="select-field">
            <option value="">选择源节点</option>
            <option v-for="node in nodes" :key="node.id" :value="node.id">
              {{ node.label }} ({{ node.type }})
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>关系标签：</label>
          <input
            v-model="newEdge.label"
            type="text"
            placeholder="比如：包含"
            class="input-field"
          >
        </div>
        <div class="form-group">
          <label>目标节点：</label>
          <select v-model="newEdge.to" class="select-field">
            <option value="">选择目标节点</option>
            <option v-for="node in nodes" :key="node.id" :value="node.id">
              {{ node.label }} ({{ node.type }})
            </option>
          </select>
        </div>
        <button @click="addEdge" class="operate-btn">添加关系</button>
      </div>

      <!-- 提交图谱按钮 -->
      <button
        @click="submitGraph"
        class="submit-btn mt-6"
        :disabled="!graphName || nodes.length === 0"
      >
        保存知识图谱
      </button>
    </div>

    <!-- 图谱预览区域 -->
    <div class="graph-preview mt-6">
      <h3>图谱预览</h3>
      <div id="graph-container" class="graph-container"></div>
    </div>
  </div>
</template>

<script setup>
// 1. 引入依赖
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Network } from 'vis-network' // 引入 vis-network 的 Network 类
import { DataSet } from 'vis-data'    // 引入 vis-data 的 DataSet 类（用于管理节点/关系数据）

// 2. 路由实例（用于页面跳转）
const router = useRouter()

// 3. 响应式数据（图谱配置相关）
const graphName = ref('') // 图谱名称
const nodes = ref(new DataSet([])) // 节点数据集（vis-data 的 DataSet 类型）
const edges = ref(new DataSet([])) // 关系数据集
let network = ref(null) // 图谱实例（用 let 而非 ref，因为是复杂对象）

// 新节点表单数据
const newNode = ref({
  label: '',
  type: ''
})

// 新关系表单数据
const newEdge = ref({
  from: '',
  to: '',
  label: ''
})

// 4. 页面挂载时初始化图谱
onMounted(() => {
  initNetwork()
})

// 5. 页面卸载时销毁图谱（避免内存泄漏）
onUnmounted(() => {
  if (network.value) {
    network.value.destroy()
  }
})

// 6. 图谱初始化函数
const initNetwork = () => {
  // 获取图谱容器 DOM 元素
  const container = document.getElementById('graph-container')
  if (!container) return

  // 图谱数据（关联 nodes 和 edges 的 DataSet）
  const data = {
    nodes: nodes.value,
    edges: edges.value
  }

  // 图谱配置项（样式、交互等）
  const options = {
    nodes: {
      shape: 'ellipse',
      size: 25,
      font: {
        size: 14,
        color: '#fff'
      },
      color: {
        background: '#42b983',
        border: '#359469'
      }
    },
    edges: {
      font: {
        size: 12,
        color: '#333'
      },
      color: '#999',
      arrows: {
        to: { enabled: true, type: 'arrow' }
      }
    },
    interaction: {
      dragNodes: true,    // 允许拖动节点
      zoomView: true,     // 允许缩放视图
      panView: true       // 允许平移视图
    },
    layout: {
      randomSeed: 2,      // 固定布局种子（避免每次加载位置变化）
      improvedLayout: true
    }
  }

  // 创建图谱实例
  network.value = new Network(container, data, options)
}

// 7. 添加节点函数
const addNode = () => {
  if (!newNode.value.label || !newNode.value.type) {
    alert('请填写节点标签和类型！')
    return
  }

  // 生成唯一节点 ID（用时间戳确保不重复）
  const nodeId = Date.now()
  // 添加节点到 DataSet
  nodes.value.add({
    id: nodeId,
    label: newNode.value.label,
    type: newNode.value.type
  })

  // 重置表单
  newNode.value = { label: '', type: '' }
}

// 8. 添加关系函数
const addEdge = () => {
  if (!newEdge.value.from || !newEdge.value.to || !newEdge.value.label) {
    alert('请选择源节点、目标节点，并填写关系标签！')
    return
  }

  // 生成唯一关系 ID
  const edgeId = `edge_${Date.now()}`
  // 添加关系到 DataSet
  edges.value.add({
    id: edgeId,
    from: Number(newEdge.value.from), // 转成数字（和节点 ID 类型一致）
    to: Number(newEdge.value.to),
    label: newEdge.value.label
  })

  // 重置表单
  newEdge.value = { from: '', to: '', label: '' }
}

// 9. 提交图谱函数（这里仅做前端演示，实际需调用后端接口）
const submitGraph = () => {
  // 模拟提交成功（实际项目中替换为 axios 调用后端 API）
  alert(`图谱 "${graphName.value}" 创建成功！`)
  // 提交后跳转到图谱查看页
  router.push('/kg/view')
}

// 10. 返回首页函数
const goBack = () => {
  router.push('/')
}
</script>

<style scoped>
/* 页面容器样式 */
.kg-create-container {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

/* 页面头部样式 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.back-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #42b983;
  border-radius: 4px;
  background: transparent;
  color: #42b983;
  cursor: pointer;
  transition: all 0.3s;
}

.back-btn:hover {
  background: #42b983;
  color: #fff;
}

/* 表单区域样式 */
.form-group {
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.form-group label {
  width: 100px;
  text-align: right;
  font-weight: 500;
}

.input-field, .select-field {
  flex: 1;
  max-width: 300px;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

/* 按钮样式 */
.operate-btn {
  padding: 0.5rem 1rem;
  background: #42b983;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.3s;
}

.operate-btn:hover {
  background: #359469;
}

.submit-btn {
  padding: 0.6rem 1.2rem;
  background: #2c3e50;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.submit-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

/* 图谱预览容器样式 */
.graph-container {
  width: 100%;
  height: 500px;
  border: 1px solid #eee;
  border-radius: 4px;
  margin-top: 1rem;
}

/* 辅助类 */
.mt-4 {
  margin-top: 1rem;
}

.mt-6 {
  margin-top: 1.5rem;
}
</style>