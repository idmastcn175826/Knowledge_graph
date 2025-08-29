import service from './api'

/**
 * 知识图谱相关API
 */
export const kgApi = {
  /**
   * 获取图谱列表
   */
  getGraphList() {
    return service.get('/graphs')
  },
  
  /**
   * 获取单个图谱详情
   * @param {string} id - 图谱ID
   */
  getGraphDetail(id) {
    return service.get(`/graphs/${id}`)
  },
  
  /**
   * 创建新图谱
   * @param {Object} data - 图谱数据
   */
  createGraph(data) {
    return service.post('/graphs', data)
  },
  
  /**
   * 更新图谱
   * @param {string} id - 图谱ID
   * @param {Object} data - 图谱数据
   */
  updateGraph(id, data) {
    return service.put(`/graphs/${id}`, data)
  },
  
  /**
   * 删除图谱
   * @param {string} id - 图谱ID
   */
  deleteGraph(id) {
    return service.delete(`/graphs/${id}`)
  },
  
  /**
   * 向图谱添加节点
   * @param {string} graphId - 图谱ID
   * @param {Object} node - 节点数据
   */
  addNode(graphId, node) {
    return service.post(`/graphs/${graphId}/nodes`, node)
  },
  
  /**
   * 向图谱添加关系
   * @param {string} graphId - 图谱ID
   * @param {Object} relationship - 关系数据
   */
  addRelationship(graphId, relationship) {
    return service.post(`/graphs/${graphId}/relationships`, relationship)
  },
  
  /**
   * 在图谱中搜索
   * @param {string} graphId - 图谱ID
   * @param {string} keyword - 搜索关键词
   */
  searchInGraph(graphId, keyword) {
    return service.get(`/graphs/${graphId}/search`, {
      params: { keyword }
    })
  }
}

export default kgApi
    