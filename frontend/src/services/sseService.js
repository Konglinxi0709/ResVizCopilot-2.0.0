/**
 * SSE流式数据服务
 * 基于test_CLI_frontend.py的实现逻辑
 */

export class SSEService {
  constructor() {
    this.eventSource = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectInterval = 1000 // 1秒
    this.isConnected = false
    this.isReconnecting = false
    this.callbacks = {
      onMessage: null,
      onError: null,
      onConnected: null,
      onDisconnected: null,
      onReconnecting: null
    }
  }

  /**
   * 建立SSE连接
   * @param {string} url - SSE端点URL
   * @param {Object} callbacks - 回调函数集合
   */
  connect(url, callbacks = {}) {
    // 设置回调函数
    this.callbacks = { ...this.callbacks, ...callbacks }
    
    try {
      console.log('🔗 正在建立SSE连接:', url)
      
      // 创建EventSource连接
      this.eventSource = new EventSource(url)
      
      // 连接打开事件
      this.eventSource.onopen = (event) => {
        console.log('✅ SSE连接已建立')
        this.isConnected = true
        this.isReconnecting = false
        this.reconnectAttempts = 0
        
        if (this.callbacks.onConnected) {
          this.callbacks.onConnected(event)
        }
      }
      
      // 接收消息事件
      this.eventSource.onmessage = (event) => {
        try {
          console.log('📡 收到SSE消息:', event.type)
          
          if (this.callbacks.onMessage) {
            this.callbacks.onMessage(event)
          }
        } catch (error) {
          console.error('❌ 处理SSE消息时出错:', error)
          if (this.callbacks.onError) {
            this.callbacks.onError(error)
          }
        }
      }
      
      // 错误事件
      this.eventSource.onerror = (event) => {
        console.error('❌ SSE连接错误:', event)
        this.isConnected = false
        
        if (this.callbacks.onError) {
          this.callbacks.onError(event)
        }
        
        // 自动重连
        this.handleReconnect(url)
      }
      
      // 监听自定义事件类型
      this.setupCustomEventListeners()
      
    } catch (error) {
      console.error('❌ 建立SSE连接失败:', error)
      if (this.callbacks.onError) {
        this.callbacks.onError(error)
      }
    }
  }

  /**
   * 设置自定义事件监听器
   */
  setupCustomEventListeners() {
    if (!this.eventSource) return

    // 监听patch事件（增量更新）
    this.eventSource.addEventListener('patch', (event) => {
      try {
        const patchData = JSON.parse(event.data)
        console.log('📝 收到patch事件:', patchData)
        
        if (this.callbacks.onMessage) {
          this.callbacks.onMessage({
            type: 'patch',
            data: patchData,
            originalEvent: event
          })
        }
      } catch (error) {
        console.error('❌ 解析patch事件失败:', error)
      }
    })

    // 监听error事件
    this.eventSource.addEventListener('error', (event) => {
      try {
        const errorData = JSON.parse(event.data)
        console.error('❌ 收到error事件:', errorData)
        
        if (this.callbacks.onError) {
          this.callbacks.onError({
            type: 'sse_error',
            data: errorData,
            originalEvent: event
          })
        }
      } catch (error) {
        console.error('❌ 解析error事件失败:', error)
      }
    })

    // 监听finished事件（完成）
    this.eventSource.addEventListener('finished', (event) => {
      try {
        const finishedData = JSON.parse(event.data)
        console.log('✅ 收到finished事件:', finishedData)
        
        if (this.callbacks.onMessage) {
          this.callbacks.onMessage({
            type: 'finished',
            data: finishedData,
            originalEvent: event
          })
        }
      } catch (error) {
        console.error('❌ 解析finished事件失败:', error)
      }
    })
  }

  /**
   * 处理自动重连
   * @param {string} url - 原始URL
   */
  handleReconnect(url) {
    if (this.isReconnecting || this.reconnectAttempts >= this.maxReconnectAttempts) {
      return
    }

    this.isReconnecting = true
    this.reconnectAttempts++

    console.log(`🔄 尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
    
    if (this.callbacks.onReconnecting) {
      this.callbacks.onReconnecting(this.reconnectAttempts, this.maxReconnectAttempts)
    }

    setTimeout(() => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.connect(url, this.callbacks)
      } else {
        console.error('❌ 达到最大重连次数，停止重连')
        this.isReconnecting = false
        
        if (this.callbacks.onError) {
          this.callbacks.onError({
            type: 'max_reconnect_attempts',
            message: '达到最大重连次数'
          })
        }
      }
    }, this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1)) // 指数回退
  }

  /**
   * 发送中断请求
   */
  async sendInterruptRequest() {
    try {
      console.log('🛑 发送中断请求...')
      
      const response = await fetch('/agents/messages/stop', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        console.log('✅ 中断请求发送成功')
        return true
      } else {
        console.error('❌ 中断请求失败:', response.status)
        return false
      }
    } catch (error) {
      console.error('❌ 发送中断请求时出错:', error)
      return false
    }
  }

  /**
   * 关闭SSE连接
   */
  disconnect() {
    console.log('🔌 关闭SSE连接')
    
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }
    
    this.isConnected = false
    this.isReconnecting = false
    this.reconnectAttempts = 0
    
    if (this.callbacks.onDisconnected) {
      this.callbacks.onDisconnected()
    }
  }

  /**
   * 检查连接状态
   */
  isConnectedToSSE() {
    return this.isConnected && this.eventSource && this.eventSource.readyState === EventSource.OPEN
  }

  /**
   * 获取连接状态
   */
  getConnectionState() {
    if (!this.eventSource) {
      return 'disconnected'
    }
    
    switch (this.eventSource.readyState) {
      case EventSource.CONNECTING:
        return 'connecting'
      case EventSource.OPEN:
        return 'connected'
      case EventSource.CLOSED:
        return 'disconnected'
      default:
        return 'unknown'
    }
  }
}

// 创建单例实例
export const sseService = new SSEService()
