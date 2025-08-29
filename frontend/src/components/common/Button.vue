<template>
  <button 
    class="px-4 py-2 rounded-md font-medium transition duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2"
    :class="buttonClasses"
    :disabled="disabled"
    @click="$emit('click')"
  >
    <slot></slot>
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = {
  // 按钮类型：primary, secondary, success, danger, warning
  type: {
    type: String,
    default: 'primary'
  },
  // 按钮大小：small, medium, large
  size: {
    type: String,
    default: 'medium'
  },
  // 是否禁用
  disabled: {
    type: Boolean,
    default: false
  },
  // 是否为圆角
  rounded: {
    type: Boolean,
    default: false
  }
}

// 计算按钮样式类
const buttonClasses = computed(() => {
  // 基础样式
  let classes = []
  
  // 类型样式
  switch (props.type) {
    case 'primary':
      classes.push('bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500')
      break
    case 'secondary':
      classes.push('bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-500')
      break
    case 'success':
      classes.push('bg-green-600 text-white hover:bg-green-700 focus:ring-green-500')
      break
    case 'danger':
      classes.push('bg-red-600 text-white hover:bg-red-700 focus:ring-red-500')
      break
    case 'warning':
      classes.push('bg-yellow-500 text-white hover:bg-yellow-600 focus:ring-yellow-400')
      break
    default:
      classes.push('bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500')
  }
  
  // 大小样式
  switch (props.size) {
    case 'small':
      classes.push('px-3 py-1 text-sm')
      break
    case 'large':
      classes.push('px-6 py-3 text-lg')
      break
    default:
      classes.push('px-4 py-2')
  }
  
  // 圆角样式
  if (props.rounded) {
    classes.push('rounded-full')
  }
  
  // 禁用样式
  if (props.disabled) {
    classes.push('opacity-50 cursor-not-allowed')
  }
  
  return classes
})
</script>

<style scoped>
/* 按钮组件样式 */
</style>
    