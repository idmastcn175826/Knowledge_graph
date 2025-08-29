/**
 * 通用工具函数
 */
export const utils = {
  /**
   * 生成唯一ID
   * @returns {string} 唯一ID字符串
   */
  generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2, 5)
  },
  
  /**
   * 格式化日期
   * @param {Date|string} date - 日期对象或字符串
   * @param {string} format - 格式化字符串，例如：'yyyy-MM-dd HH:mm:ss'
   * @returns {string} 格式化后的日期字符串
   */
  formatDate(date, format = 'yyyy-MM-dd HH:mm:ss') {
    if (!date) return ''
    if (typeof date === 'string') {
      date = new Date(date)
    }
    if (!(date instanceof Date) || isNaN(date.getTime())) {
      return ''
    }
    
    const o = {
      'M+': date.getMonth() + 1, // 月份
      'd+': date.getDate(), // 日
      'H+': date.getHours(), // 小时
      'm+': date.getMinutes(), // 分
      's+': date.getSeconds(), // 秒
      'q+': Math.floor((date.getMonth() + 3) / 3), // 季度
      'S': date.getMilliseconds() // 毫秒
    }
    
    if (/(y+)/.test(format)) {
      format = format.replace(RegExp.$1, (date.getFullYear() + '').substr(4 - RegExp.$1.length))
    }
    
    for (const k in o) {
      if (new RegExp('(' + k + ')').test(format)) {
        format = format.replace(RegExp.$1, (RegExp.$1.length === 1) ? (o[k]) : (('00' + o[k]).substr(('' + o[k]).length)))
      }
    }
    
    return format
  },
  
  /**
   * 深拷贝对象
   * @param {Object} obj - 要拷贝的对象
   * @returns {Object} 拷贝后的新对象
   */
  deepClone(obj) {
    if (obj === null || typeof obj !== 'object') {
      return obj
    }
    
    let cloneObj
    if (obj instanceof Array) {
      cloneObj = []
    } else {
      cloneObj = {}
    }
    
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        cloneObj[key] = this.deepClone(obj[key])
      }
    }
    
    return cloneObj
  },
  
  /**
   * 防抖函数
   * @param {Function} func - 要执行的函数
   * @param {number} wait - 等待时间，毫秒
   * @returns {Function} 防抖后的函数
   */
  debounce(func, wait) {
    let timeout
    return function(...args) {
      const context = this
      clearTimeout(timeout)
      timeout = setTimeout(() => {
        func.apply(context, args)
      }, wait)
    }
  },
  
  /**
   * 节流函数
   * @param {Function} func - 要执行的函数
   * @param {number} interval - 间隔时间，毫秒
   * @returns {Function} 节流后的函数
   */
  throttle(func, interval) {
    let lastTime = 0
    return function(...args) {
      const now = Date.now()
      if (now - lastTime >= interval) {
        func.apply(this, args)
        lastTime = now
      }
    }
  }
}

export default utils
    