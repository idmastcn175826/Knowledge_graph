<template>
  <header class="bg-white shadow-sm">
    <div class="container mx-auto px-4">
      <div class="flex justify-between items-center py-4">
        <div class="flex items-center">
          <router-link to="/" class="text-2xl font-bold text-blue-600">
            知识图谱系统
          </router-link>
        </div>
        
        <nav class="hidden md:flex space-x-8">
          <router-link 
            to="/" 
            class="text-gray-700 hover:text-blue-600 font-medium transition duration-200"
            :class="{ 'text-blue-600': $route.path === '/' }"
          >
            首页
          </router-link>
          <router-link 
            to="/kg/create" 
            class="text-gray-700 hover:text-blue-600 font-medium transition duration-200"
            :class="{ 'text-blue-600': $route.path === '/kg/create' }"
          >
            创建图谱
          </router-link>
          <router-link 
            to="/kg/view" 
            class="text-gray-700 hover:text-blue-600 font-medium transition duration-200"
            :class="{ 'text-blue-600': $route.path === '/kg/view' }"
          >
            查看图谱
          </router-link>
        </nav>
        
        <div class="md:hidden">
          <button class="text-gray-700 focus:outline-none">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
// 头部组件逻辑
</script>

<style scoped>
/* 头部样式 */
</style>
    