import axios from 'axios'

// 创建axios实例
const apiClient = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 在发送请求之前做些什么
    console.log(`API请求: ${config.method?.toUpperCase()} ${config.url}`)
    
    // 添加时间戳避免缓存
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now()
      }
    }
    
    return config
  },
  (error) => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    // 对响应数据做点什么
    console.log(`API响应: ${response.config.method?.toUpperCase()} ${response.config.url}`, response.status)
    
    // 检查响应状态
    if (response.status >= 200 && response.status < 300) {
      return response
    } else {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
  },
  (error) => {
    console.error('API响应错误:', error)
    
    // 处理不同类型的错误
    let errorMessage = '网络错误，请检查连接'
    
    if (error.response) {
      // 服务器响应了错误状态码
      const { status, data } = error.response
      
      switch (status) {
        case 400:
          errorMessage = data?.detail || '请求参数错误'
          break
        case 401:
          errorMessage = '未授权访问'
          break
        case 403:
          errorMessage = '访问被禁止'
          break
        case 404:
          errorMessage = '请求的资源不存在'
          break
        case 422:
          errorMessage = data?.detail || '数据验证失败'
          break
        case 500:
          errorMessage = '服务器内部错误'
          break
        case 502:
          errorMessage = '网关错误'
          break
        case 503:
          errorMessage = '服务暂时不可用'
          break
        default:
          errorMessage = data?.detail || `服务器错误 (${status})`
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应
      if (error.code === 'ECONNABORTED') {
        errorMessage = '请求超时，请稍后重试'
      } else {
        errorMessage = '网络连接失败，请检查网络'
      }
    } else {
      // 其他错误
      errorMessage = error.message || '未知错误'
    }
    
    // 显示错误消息（可选，根据需要启用）
    // ElMessage.error(errorMessage)
    
    // 创建统一的错误对象
    const apiError = new Error(errorMessage)
    apiError.status = error.response?.status
    apiError.code = error.code
    apiError.originalError = error
    
    return Promise.reject(apiError)
  }
)

// API服务类
class ApiService {
  // GET请求
  async get(url, params = {}, config = {}) {
    try {
      const response = await apiClient.get(url, {
        params,
        ...config
      })
      return response.data
    } catch (error) {
      throw this.handleError(error, 'GET', url)
    }
  }
  
  // POST请求
  async post(url, data = {}, config = {}) {
    try {
      const response = await apiClient.post(url, data, config)
      return response.data
    } catch (error) {
      throw this.handleError(error, 'POST', url)
    }
  }
  
  // PUT请求
  async put(url, data = {}, config = {}) {
    try {
      const response = await apiClient.put(url, data, config)
      return response.data
    } catch (error) {
      throw this.handleError(error, 'PUT', url)
    }
  }
  
  // PATCH请求
  async patch(url, data = {}, config = {}) {
    try {
      const response = await apiClient.patch(url, data, config)
      return response.data
    } catch (error) {
      throw this.handleError(error, 'PATCH', url)
    }
  }
  
  // DELETE请求
  async delete(url, config = {}) {
    try {
      const response = await apiClient.delete(url, config)
      return response.data
    } catch (error) {
      throw this.handleError(error, 'DELETE', url)
    }
  }
  
  // 处理错误
  handleError(error, method, url) {
    console.error(`API ${method} ${url} 失败:`, error.message)
    return error
  }
  
  // 健康检查
  async healthCheck() {
    try {
      const response = await this.get('/healthz')
      return response
    } catch (error) {
      console.error('健康检查失败:', error)
      throw error
    }
  }
  
  // 设置请求头
  setHeader(key, value) {
    apiClient.defaults.headers.common[key] = value
  }
  
  // 移除请求头
  removeHeader(key) {
    delete apiClient.defaults.headers.common[key]
  }
  
  // 设置基础URL
  setBaseURL(baseURL) {
    apiClient.defaults.baseURL = baseURL
  }
  
  // 设置请求超时时间
  setTimeout(timeout) {
    apiClient.defaults.timeout = timeout
  }
  
  // 获取当前配置
  getConfig() {
    return {
      baseURL: apiClient.defaults.baseURL,
      timeout: apiClient.defaults.timeout,
      headers: { ...apiClient.defaults.headers }
    }
  }
}

// 创建API服务实例
export const apiService = new ApiService()

// 导出axios实例（如果需要直接使用）
export { apiClient }

// 默认导出
export default apiService
