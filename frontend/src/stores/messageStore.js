import { defineStore } from 'pinia'
import { apiService } from '../services/apiService'

export const useMessageStore = defineStore('message', {
  state: () => ({
    // 消息列表
    messages: [],
    
    // 是否正在生成消息
    isGenerating: false,
    
    // 当前智能体名称
    currentAgentName: null,
    
    // SSE连接状态
    sseConnection: null,
    
    // 当前生成的消息ID
    currentGeneratingMessageId: null,
    
    // 加载状态
    isLoading: false,
    
    // 错误信息
    error: null
  }),
  
  getters: {
    // 获取消息数量
    messageCount: (state) => {
      return state.messages.length
    },
    
    // 获取最新消息
    latestMessage: (state) => {
      return state.messages.length > 0 ? state.messages[state.messages.length - 1] : null
    },
    
    // 检查是否有消息
    hasMessages: (state) => {
      return state.messages.length > 0
    },
    
    // 获取用户消息
    userMessages: (state) => {
      return state.messages.filter(msg => msg.role === 'user')
    },
    
    // 获取智能体消息
    agentMessages: (state) => {
      return state.messages.filter(msg => msg.role === 'assistant')
    },
    
    // 获取系统消息
    systemMessages: (state) => {
      return state.messages.filter(msg => msg.role === 'system')
    },
    
    // 检查是否可以发送消息（没有正在生成的消息）
    canSendMessage: (state) => {
      return !state.isGenerating
    }
  },
  
  actions: {
    // 设置加载状态
    setLoading(loading) {
      this.isLoading = loading
    },
    
    // 设置错误信息
    setError(error) {
      this.error = error
    },
    
    // 清除错误信息
    clearError() {
      this.error = null
    },
    
    // 添加消息
    addMessage(message) {
      // 确保消息有必要的字段
      const fullMessage = {
        id: message.id || this.generateMessageId(),
        role: message.role || 'user',
        title: message.title || '',
        content: message.content || '',
        thinking: message.thinking || '',
        status: message.status || 'completed',
        publisher: message.publisher || null,
        snapshot_id: message.snapshot_id || null,
        visible_node_ids: message.visible_node_ids || [],
        created_at: message.created_at || new Date().toISOString(),
        updated_at: message.updated_at || new Date().toISOString(),
        ...message
      }
      
      this.messages.push(fullMessage)
      return fullMessage
    },
    
    // 更新消息
    updateMessage(messageId, updates) {
      const messageIndex = this.messages.findIndex(msg => msg.id === messageId)
      if (messageIndex !== -1) {
        this.messages[messageIndex] = {
          ...this.messages[messageIndex],
          ...updates,
          updated_at: new Date().toISOString()
        }
        return this.messages[messageIndex]
      }
      return null
    },
    
    // 删除消息
    removeMessage(messageId) {
      const messageIndex = this.messages.findIndex(msg => msg.id === messageId)
      if (messageIndex !== -1) {
        this.messages.splice(messageIndex, 1)
        return true
      }
      return false
    },
    
    // 获取消息
    getMessage(messageId) {
      return this.messages.find(msg => msg.id === messageId) || null
    },
    
    // 应用patch更新
    applyPatch(patch) {
      try {
        const { message_id, patch_type, data } = patch
        
        switch (patch_type) {
          case 'message_created':
            this.addMessage(data)
            break
            
          case 'message_updated':
            this.updateMessage(message_id, data)
            break
            
          case 'title_updated':
            this.updateMessage(message_id, { title: data.title })
            break
            
          case 'content_updated':
            this.updateMessage(message_id, { content: data.content })
            break
            
          case 'thinking_updated':
            this.updateMessage(message_id, { thinking: data.thinking })
            break
            
          case 'status_updated':
            this.updateMessage(message_id, { status: data.status })
            break
            
          case 'snapshot_updated':
            this.updateMessage(message_id, { 
              snapshot_id: data.snapshot_id,
              visible_node_ids: data.visible_node_ids || []
            })
            break
            
          default:
            console.warn('未知的patch类型:', patch_type)
        }
      } catch (error) {
        console.error('应用patch失败:', error)
      }
    },
    
    // 发送消息
    async sendMessage(agentName, content, params = {}) {
      try {
        this.setLoading(true)
        this.clearError()
        
        // 设置生成状态
        this.isGenerating = true
        this.currentAgentName = agentName
        
        const response = await apiService.post('/agents/messages', {
          agent_name: agentName,
          content: content,
          ...params
        })
        
        // 开始SSE连接接收流式数据
        this.startSSEConnection()
        
        return response.data
      } catch (error) {
        console.error('发送消息失败:', error)
        this.setError('发送消息失败')
        this.isGenerating = false
        this.currentAgentName = null
        throw error
      } finally {
        this.setLoading(false)
      }
    },
    
    // 停止生成
    async stopGeneration() {
      try {
        await apiService.post('/agents/messages/stop')
        this.isGenerating = false
        this.currentAgentName = null
        this.currentGeneratingMessageId = null
        
        // 关闭SSE连接
        this.closeSSEConnection()
      } catch (error) {
        console.error('停止生成失败:', error)
        throw error
      }
    },
    
    // 回溯消息
    async rollbackToMessage(messageId) {
      try {
        this.setLoading(true)
        this.clearError()
        
        await apiService.post(`/agents/messages/rollback-to/${messageId}`)
        
        // 删除指定消息之后的所有消息
        const messageIndex = this.messages.findIndex(msg => msg.id === messageId)
        if (messageIndex !== -1) {
          this.messages.splice(messageIndex + 1)
        }
        
        return true
      } catch (error) {
        console.error('回溯消息失败:', error)
        this.setError('回溯消息失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },
    
    // 开始SSE连接
    startSSEConnection() {
      // 如果已有连接，先关闭
      this.closeSSEConnection()
      
      try {
        const sseUrl = `${process.env.VUE_APP_API_BASE_URL}/agents/messages/continue`
        this.sseConnection = new EventSource(sseUrl)
        
        this.sseConnection.onmessage = (event) => {
          try {
            const patch = JSON.parse(event.data)
            this.applyPatch(patch)
            
            // 如果是finished事件，停止生成
            if (patch.patch_type === 'finished') {
              this.isGenerating = false
              this.currentAgentName = null
              this.currentGeneratingMessageId = null
              this.closeSSEConnection()
            }
          } catch (error) {
            console.error('处理SSE消息失败:', error)
          }
        }
        
        this.sseConnection.onerror = (error) => {
          console.error('SSE连接错误:', error)
          this.handleSSEError()
        }
        
        this.sseConnection.onopen = () => {
          console.log('SSE连接已建立')
        }
      } catch (error) {
        console.error('建立SSE连接失败:', error)
        this.handleSSEError()
      }
    },
    
    // 关闭SSE连接
    closeSSEConnection() {
      if (this.sseConnection) {
        this.sseConnection.close()
        this.sseConnection = null
      }
    },
    
    // 处理SSE错误
    handleSSEError() {
      this.closeSSEConnection()
      
      // 如果正在生成，尝试重连
      if (this.isGenerating) {
        setTimeout(() => {
          console.log('尝试重新连接SSE...')
          this.startSSEConnection()
        }, 2000)
      }
    },
    
    // 生成消息ID
    generateMessageId() {
      return 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
    },
    
    // 清除所有消息
    clearAllMessages() {
      this.messages = []
      this.isGenerating = false
      this.currentAgentName = null
      this.currentGeneratingMessageId = null
      this.closeSSEConnection()
    },
    
    // 复制消息内容
    copyMessageContent(messageId) {
      const message = this.getMessage(messageId)
      if (!message) return false
      
      try {
        const content = [
          message.title && `标题: ${message.title}`,
          message.content && `内容: ${message.content}`,
          message.thinking && `思考: ${message.thinking}`
        ].filter(Boolean).join('\n\n')
        
        navigator.clipboard.writeText(content)
        return true
      } catch (error) {
        console.error('复制失败:', error)
        return false
      }
    }
  },
  
  // 持久化配置
  persist: {
    key: 'resviz-message-store',
    storage: sessionStorage,
    paths: ['messages']
  }
})
