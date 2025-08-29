<template>
  <div class="graph-display">
    <div ref="graphContainer" class="w-full h-full"></div>
    
    <div v-if="loading" class="absolute inset-0 bg-white/70 flex items-center justify-center">
      <div class="loading-spinner w-10 h-10 border-4 border-blue-200 border-t-blue-500 rounded-full animate-spin"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { Network } from 'vis-network'

const props = {
  // 图谱数据
  graphData: {
    type: Object,
    default: () => ({ nodes: [], edges: [] })
  },
  // 加载状态
  loading: {
    type: Boolean,
    default: false
  },
  // 配置选项
  options: {
    type: Object,
    default: () => ({})
  }
}

// 容器引用
const graphContainer = ref(null)

// 网络实例
let network = null

// 初始化网络
const initNetwork = () => {
  if (!graphContainer.value) return
  
  // 合并默认配置和用户配置
  const defaultOptions = {
    nodes: {
      shape: 'ellipse',
      font: {
        size: 14,
        color: '#000'
      },
      size: 25
    },
    edges: {
      font: {
        size: 12,
        align: 'middle'
      },
      color: '#999',
      width: 2
    },
    interaction: {
      dragNodes: true,
      dragView: true,
      zoomView: true
    },
    layout: {
      randomSeed: 2,
      improvedLayout: true
    }
    
    const mergedOptions = { ...defaultOptions, ...props.options }
    
    // 销毁现有网络
    if (network) {
      network.destroy()
    }
    
    // 创建新网络
    network = new Network(graphContainer.value, props.graphData, mergedOptions)
    
    // 触发节点点击事件
    network.on('click', params => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0]
        const node = props.graphData.nodes.find(n => n.id === nodeId)
        if (node) {
          emit('node-click', node)
        }
      }
    })
    
    // 触发边点击事件
    network.on('click', params => {
      if (params.edges.length > 0) {
        const edgeId = params.edges[0]
        const edge = props.graphData.edges.find(e => e.id === edgeId)
        if (edge) {
          emit('edge-click', edge)
        }
      }
    })
  }

// 事件发射器
const emit = defineEmits(['node-click', 'edge-click'])

// 当图谱数据变化时更新网络
watch(
  () => props.graphData,
  (newData) => {
    if (network) {
      network.setData(newData)
    } else {
      initNetwork()
    }
  },
  { deep: true }
)

// 当容器挂载时初始化网络
onMounted(() => {
  initNetwork()
})

// 组件卸载时销毁网络
onUnmounted(() => {
  if (network) {
    network.destroy()
    network = null
  }
})
</script>

<style scoped>
.graph-display {
  position: relative;
  width: 100%;
  height: 100%;
}

.loading-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
    