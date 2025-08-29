import axios from 'axios'
import { useMainStore } from '../store'

// 创建axios实例
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    const mainStore = useMainStore()
    // 显示加载状态
    mainStore.setLoading(true)
    
    // 可以在这里添加token等认证信息
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    
    return config
  },
  (error) => {
    const mainStore = useMainStore()
    // 隐藏加载状态
    mainStore.setLoading(false)
    // 设置错误信息
    mainStore.setError(error.message)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response) => {
    const mainStore = useMainStore()
    // 隐藏加载状态
    mainStore.setLoading(false)
    
    // 假设后端返回格式为 { code, data, message }
    const res = response.data
    if (res.code !== 200) {
      mainStore.setError(res.message || '操作失败')
      return Promise.reject(new Error(res.message || 'Error'))
    }
    return res.data
  },
  (error) => {
    const mainStore = useMainStore()
    // 隐藏加载状态
    mainStore.setLoading(false)
    
    // 处理不同错误情况
    if (error.response) {
      switch (error.response.status) {
        case 401:
          mainStore.setError('未授权，请重新登录')
          // 可以在这里添加跳转到登录页的逻辑
          break
        case 404:
          mainStore.setError('请求的资源不存在')
          break
        case 500:
          mainStore.setError('服务器内部错误')
          break
        default:
          mainStore.setError(`请求错误: ${error.response.status}`)
      }
    } else if (error.request) {
      mainStore.setError('请求超时，请稍后重试')
    } else {
      mainStore.setError(`请求失败: ${error.message}`)
    }
    
    return Promise.reject(error)
  }
)

export default service
    