import { defineStore } from 'pinia'
import { apiService } from '../services/apiService'
import { useTreeStore } from './treeStore'

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
    },

    // 根据ID查找消息
    getMessageById: (state) => {
      return (messageId) => {
        return state.messages.find(msg => msg.id === messageId)
      }
    },

    // 获取未完成的消息
    getIncompleteMessage: (state) => {
      return state.messages.find(msg => msg.status === 'generating')
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
        action_title: message.action_title || '',
        action_params: message.action_params || {},
        created_at: message.created_at || new Date().toISOString(),
        updated_at: message.updated_at || new Date().toISOString(),
        ...message
      }
      
      this.messages.push(fullMessage)
      return fullMessage
    },
    
    // 生成消息ID
    generateMessageId() {
      return 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
    },

    // 更新消息状态
    updateMessageStatus(messageId, status) {
      const message = this.messages.find(msg => msg.id === messageId)
      if (message) {
        message.status = status
        message.updated_at = new Date().toISOString()
      }
    },
    
    // 删除消息
    removeMessage(messageId) {
      const index = this.messages.findIndex(msg => msg.id === messageId)
      if (index !== -1) {
        this.messages.splice(index, 1)
      }
    },

    // 清空所有消息
    clearMessages() {
      this.messages = []
      this.isGenerating = false
      this.currentGeneratingMessageId = null
      this.currentAgentName = null
    },

    /**
     * 处理SSE patch数据
     * 基于test_CLI_frontend.py的handle_patch逻辑
     */
    async handlePatch(patchData) {
      try {
        console.log('📝 处理patch数据:', patchData)

        // 更新快照数据
        if (patchData.snapshot && patchData.snapshot.data) {
          const treeStore = useTreeStore()
          await treeStore.updateCurrentSnapshot(patchData.snapshot.data)
        }

        // 处理回溯操作
        if (patchData.rollback) {
          const messageId = patchData.message_id
          if (!messageId) {
            console.error('❌ 回溯操作必须指定message_id')
            return
          }
          await this.handleRollback(messageId)
          return
        }

        // 处理消息更新
        const messageId = patchData.message_id

        if (messageId === "-") {
          // 更新所有正在生成的消息
          this.updateAllGeneratingMessages(patchData)
        } else {
          const existingMessage = this.getMessageById(messageId)
          
          if (!existingMessage) {
            // 创建新消息
            await this.createMessageFromPatch(patchData)
          } else {
            // 更新现有消息
            this.updateExistingMessage(patchData)
          }
        }
      } catch (error) {
        console.error('❌ 处理patch时出错:', error)
        this.setError(error.message || '处理消息更新失败')
      }
    },

    /**
     * 从patch创建新消息
     */
    async createMessageFromPatch(patchData) {
      // 检查是否有消息正在生成
      const generatingMsg = this.getIncompleteMessage
      if (generatingMsg) {
        console.warn('⚠️ 存在正在生成的消息:', generatingMsg.id)
      }

      // 检查role属性
      const role = patchData.role
      if (!role) {
        console.warn('⚠️ 创建新消息时必须指定role属性')
        return
      }

      // 创建新消息
      const message = {
        id: patchData.message_id,
        role: role,
        publisher: patchData.publisher || null,
        status: patchData.finished ? 'completed' : 'generating',
        title: patchData.title || '',
        thinking: patchData.thinking_delta || '',
        content: patchData.content_delta || '',
        action_title: patchData.action_title || '',
        action_params: patchData.action_params || {},
        snapshot_id: patchData.snapshot_id || '',
        visible_node_ids: patchData.visible_node_ids || [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }

      this.addMessage(message)

      // 更新生成状态
      if (!patchData.finished) {
        this.isGenerating = true
        this.currentGeneratingMessageId = message.id
      }
    },

    /**
     * 更新现有消息
     */
    updateExistingMessage(patchData) {
      const messageId = patchData.message_id
      const message = this.getMessageById(messageId)

      if (!message) {
        console.error('❌ 消息不存在:', messageId)
        return
      }

      this.applyPatchToMessage(patchData, message)
    },

    /**
     * 更新所有正在生成的消息
     */
    updateAllGeneratingMessages(patchData) {
      this.messages.forEach(message => {
        if (message.status === 'generating') {
          this.applyPatchToMessage(patchData, message)
        }
      })
    },

    /**
     * 将patch应用到消息上
     */
    applyPatchToMessage(patchData, message) {
      // 增量更新
      if (patchData.thinking_delta) {
        message.thinking += patchData.thinking_delta
      }
      if (patchData.content_delta) {
        message.content += patchData.content_delta
      }

      // 替换更新
      if (patchData.title !== undefined) {
        message.title = patchData.title
      }
      if (patchData.action_title !== undefined) {
        message.action_title = patchData.action_title
      }
      if (patchData.action_params !== undefined) {
        message.action_params = patchData.action_params
      }
      if (patchData.snapshot_id !== undefined) {
        message.snapshot_id = patchData.snapshot_id
      }
      if (patchData.visible_node_ids !== undefined) {
        message.visible_node_ids = patchData.visible_node_ids
      }

      // 更新状态
      if (patchData.finished) {
        message.status = 'completed'
        this.isGenerating = false
        this.currentGeneratingMessageId = null
        this.currentAgentName = null
      }

      // 更新时间戳
      message.updated_at = new Date().toISOString()
    },

    /**
     * 处理消息回溯
     */
    async handleRollback(messageId) {
      try {
        // 找到消息在列表中的位置
        const rollbackIndex = this.messages.findIndex(msg => msg.id === messageId)
        
        if (rollbackIndex === -1) {
          console.warn('⚠️ 回溯消息不存在:', messageId)
          return
        }

        // 删除从该位置之后的所有消息
        const messagesToRemove = this.messages.slice(rollbackIndex + 1)
        this.messages = this.messages.slice(0, rollbackIndex + 1)

        // 重置目标消息状态
        const targetMessage = this.messages[rollbackIndex]
        if (targetMessage) {
          targetMessage.status = 'generating'
          targetMessage.content = ''
          targetMessage.thinking = ''
          targetMessage.updated_at = new Date().toISOString()
        }

        console.log(`🔄 回溯消息: 删除了 ${messagesToRemove.length} 条消息`)

        // 更新生成状态
        this.isGenerating = true
        this.currentGeneratingMessageId = targetMessage?.id || null

      } catch (error) {
        console.error('❌ 处理回溯时出错:', error)
        this.setError('消息回溯失败')
      }
    },

    /**
     * 发送智能体消息
     * 基于test_CLI_frontend.py的call_agent逻辑
     */
    async sendAgentMessage(agentName, content, title, otherParams = {}) {
      try {
        this.setLoading(true)
        this.clearError()
        
        const requestData = {
          content: content,
          title: title,
          agent_name: agentName,
          other_params: otherParams
        }

        console.log('📤 发送智能体消息:', requestData)

        // 发送POST请求启动智能体
        const response = await fetch(`${process.env.VUE_APP_API_BASE_URL || 'http://localhost:8008'}/agents/messages`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(requestData)
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        console.log('✅ 请求发送成功，开始接收SSE流...')

        // 设置智能体状态
        this.currentAgentName = agentName
        this.isGenerating = true

        // 建立SSE连接接收流式数据
        this.connectToSSE(response, {
          onMessage: this.handleSSEMessage.bind(this),
          onError: this.handleSSEError.bind(this),
          onConnected: () => {
            console.log('✅ SSE连接已建立，开始接收流式数据')
          },
          onDisconnected: () => {
            console.log('🔌 SSE连接已断开')
            this.isGenerating = false
            this.currentAgentName = null
          }
        })

        return true

      } catch (error) {
        console.error('❌ 发送智能体消息失败:', error)
        this.setError(error.message || '发送消息失败')
        this.isGenerating = false
        this.currentAgentName = null
        return false
      } finally {
        this.setLoading(false)
      }
    },
    
    /**
     * 连接到SSE
     * 直接使用响应流，类似CLI前端的handle_sse_stream
     */
    connectToSSE(response, callbacks = {}) {
      this.sseConnection = this.handleSSEStream(response, callbacks)
    },

    /**
     * 处理SSE流
     * 基于test_CLI_frontend.py的handle_sse_stream逻辑
     */
    async handleSSEStream(response, callbacks = {}) {
      try {
        console.log('🌊 开始处理SSE流...')
        
        if (callbacks.onConnected) {
          callbacks.onConnected()
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        // eslint-disable-next-line no-constant-condition
        while (true) {
          const { done, value } = await reader.read()
          
          if (done) {
            console.log('✅ SSE流结束')
            break
          }

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() // 保留不完整的行

          for (const line of lines) {
            if (line.trim() === '') continue

            try {
              // 解析SSE事件格式
              if (line.startsWith('event:')) {
                line.substring(6).trim() // 提取事件类型但不存储
                continue
              } else if (line.startsWith('data:')) {
                const data = line.substring(5).trim()
                
                if (data === '[DONE]') {
                  console.log('✅ 收到完成标志')
                  this.isGenerating = false
                  this.currentAgentName = null
                  this.currentGeneratingMessageId = null
                  break
                }

                const eventData = JSON.parse(data)
                
                // 根据事件类型处理
                if (eventData.event === 'patch') {
                  await this.handlePatch(eventData.data || eventData)
                } else if (eventData.event === 'error') {
                  console.error('❌ 收到错误事件:', eventData.data)
                  if (callbacks.onError) {
                    callbacks.onError(eventData.data)
                  }
                } else if (eventData.event === 'finished') {
                  console.log('✅ 收到完成事件:', eventData.data)
                  this.isGenerating = false
                  this.currentAgentName = null
                  this.currentGeneratingMessageId = null
                } else {
                  // 直接作为patch数据处理
                  await this.handlePatch(eventData)
                }

                if (callbacks.onMessage) {
                  callbacks.onMessage(eventData)
                }

              }
            } catch (error) {
              console.error('❌ 解析SSE数据失败:', error, 'line:', line)
            }
          }
        }

      } catch (error) {
        console.error('❌ 处理SSE流时出错:', error)
        if (callbacks.onError) {
          callbacks.onError(error)
        }
      } finally {
        if (callbacks.onDisconnected) {
          callbacks.onDisconnected()
        }
      }
    },

    /**
     * 处理SSE消息
     */
    handleSSEMessage() {
      // 由handleSSEStream直接处理，这里保留接口兼容性
    },

    /**
     * 处理SSE错误
     */
    handleSSEError(error) {
      console.error('❌ SSE连接错误:', error)
      this.setError('连接中断，正在尝试重连...')
      this.isGenerating = false
      this.currentAgentName = null
    },

    /**
     * 断开SSE连接
     */
    disconnectSSE() {
      if (this.sseConnection) {
        this.sseConnection = null
      }
        this.isGenerating = false
        this.currentAgentName = null
        this.currentGeneratingMessageId = null
    },

    /**
     * 发送中断请求
     */
    async sendInterruptRequest() {
      try {
        console.log('🛑 发送中断请求...')
        
        const response = await fetch(`${process.env.VUE_APP_API_BASE_URL || 'http://localhost:8008'}/agents/messages/stop`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        })

        if (response.ok) {
          console.log('✅ 中断请求发送成功')
          this.isGenerating = false
          this.currentAgentName = null
          this.currentGeneratingMessageId = null
          return true
        } else {
          console.error('❌ 中断请求失败:', response.status)
          return false
        }
      } catch (error) {
        console.error('❌ 发送中断请求失败:', error)
        return false
      }
    },
    
    /**
     * 回溯到指定消息
     */
    async rollbackToMessage(messageId) {
      try {
        this.setLoading(true)
        this.clearError()
        
        console.log('🔄 回溯到消息:', messageId)

        const response = await apiService.post(`/agents/messages/rollback-to/${messageId}`)
        
        if (response.success) {
          console.log('✅ 回溯操作成功')
          // 本地同步删除消息
          await this.handleRollback(messageId)
          return true
        } else {
          throw new Error(response.message || '回溯操作失败')
        }

      } catch (error) {
        console.error('❌ 回溯消息失败:', error)
        this.setError('回溯消息失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },
    
    /**
     * 继续未完成的消息传输
     */
    async continueIncompleteMessage(messageId) {
      try {
        console.log('🔄 继续传输未完成消息:', messageId)

        const response = await fetch(`${process.env.VUE_APP_API_BASE_URL || 'http://localhost:8008'}/agents/messages/continue/${messageId}`, {
          method: 'GET',
          headers: {
            'Accept': 'text/event-stream'
          }
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        console.log('✅ 继续传输连接成功，开始接收SSE流...')
        
        this.isGenerating = true
        this.currentGeneratingMessageId = messageId

        // 处理SSE流
        await this.handleSSEStream(response, {
          onMessage: this.handleSSEMessage.bind(this),
          onError: this.handleSSEError.bind(this),
          onConnected: () => {
            console.log('✅ 继续传输SSE连接已建立')
          },
          onDisconnected: () => {
            console.log('🔌 继续传输SSE连接已断开')
            this.isGenerating = false
          }
        })

        return true

      } catch (error) {
        console.error('❌ 继续传输失败:', error)
        this.setError('继续传输失败')
        return false
      }
    },

    /**
     * 从后端同步消息历史
     * 参考CLI前端的sync_project_data逻辑
     */
    async syncMessagesFromBackend() {
      try {
        this.setLoading(true)
        this.clearError()

        console.log('🔄 正在同步消息历史...')

        // 获取工程完整数据（包括消息历史）
        const response = await apiService.get('/projects/current/full-data')
        
        if (response.success && response.data) {
          const fullData = response.data
          
          // 获取消息历史
          const historyMessages = fullData.messages || []
          const incompleteMessageId = fullData.incomplete_message_id

          console.log(`📊 同步到 ${historyMessages.length} 条消息`)

          // 清空并重新加载消息
      this.messages = []

          // 转换消息格式
          for (const msg of historyMessages) {
            this.addMessage({
              id: msg.id,
              role: msg.role,
              publisher: msg.publisher,
              status: msg.status,
              title: msg.title,
              thinking: msg.thinking || '',
              content: msg.content || '',
              action_title: msg.action_title || '',
              action_params: msg.action_params || {},
              snapshot_id: msg.snapshot_id || '',
              visible_node_ids: msg.visible_node_ids || [],
              created_at: msg.created_at,
              updated_at: msg.updated_at
            })
          }

          // 处理未完成的消息
          if (incompleteMessageId) {
            console.log('⚠️ 发现未完成消息:', incompleteMessageId)
            console.log('🔄 开始继续传输未完成消息...')
            await this.continueIncompleteMessage(incompleteMessageId)
          } else {
            console.log('✅ 没有未完成的消息')
          }

        return true
        } else {
          throw new Error('获取工程数据失败')
        }

      } catch (error) {
        console.error('❌ 同步消息历史失败:', error)
        this.setError('同步消息失败')
        return false
      } finally {
        this.setLoading(false)
      }
    }
  }
})