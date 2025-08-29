<template>
  <div class="home">
    <div class="hero bg-gradient-to-r from-blue-500 to-purple-600 text-white py-16 px-4">
      <div class="container mx-auto text-center">
        <h1 class="text-4xl md:text-5xl font-bold mb-6">知识图谱系统</h1>
        <p class="text-xl md:text-2xl mb-8 max-w-3xl mx-auto">
          构建、可视化和探索复杂的知识关系网络，让数据之间的联系一目了然
        </p>
        <div class="flex flex-col sm:flex-row gap-4 justify-center">
          <router-link
            to="/kg/create"
            class="bg-white text-blue-600 hover:bg-gray-100 px-6 py-3 rounded-lg font-semibold transition duration-300"
          >
            创建新图谱
          </router-link>
          <router-link
            to="/kg/view"
            class="bg-transparent border-2 border-white hover:bg-white/10 px-6 py-3 rounded-lg font-semibold transition duration-300"
          >
            查看已有图谱
          </router-link>
        </div>
      </div>
    </div>

    <div class="features py-16 px-4">
      <div class="container mx-auto">
        <h2 class="text-3xl font-bold text-center mb-12">系统功能</h2>
        <div class="grid md:grid-cols-3 gap-8">
          <div class="feature-card bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition duration-300">
            <div class="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
              <span class="text-blue-600 text-xl">✏️</span>
            </div>
            <h3 class="text-xl font-semibold mb-2">图谱创建</h3>
            <p class="text-gray-600">
              轻松创建自定义知识图谱，添加节点和关系，定义实体属性，构建专属知识网络。
            </p>
          </div>

          <div class="feature-card bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition duration-300">
            <div class="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <span class="text-green-600 text-xl">👁️</span>
            </div>
            <h3 class="text-xl font-semibold mb-2">可视化展示</h3>
            <p class="text-gray-600">
              直观展示知识图谱结构，支持缩放、平移和节点交互，让复杂关系一目了然。
            </p>
          </div>

          <div class="feature-card bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition duration-300">
            <div class="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mb-4">
              <span class="text-purple-600 text-xl">🔍</span>
            </div>
            <h3 class="text-xl font-semibold mb-2">智能搜索</h3>
            <p class="text-gray-600">
              快速搜索图谱中的实体和关系，支持模糊查询，帮助您快速定位所需信息。
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 首页组件逻辑
</script>

<style scoped>
.hero {
  margin-bottom: 2rem;
}

.features {
  background-color: #f9fafb;
}
</style>
