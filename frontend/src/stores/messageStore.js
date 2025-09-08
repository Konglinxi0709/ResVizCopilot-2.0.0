import { defineStore } from 'pinia'
import { apiService } from '../services/apiService'
import { useTreeStore } from './treeStore'

export const useMessageStore = defineStore('message', {
  state: () => ({
    // 消息列表
    messages: null,

    // 是否正在生成
    isGenerating: false,

    // SSE连接
    sseConnection: null,

    // 当前生成的消息ID
    currentGeneratingMessageId: null,

    // 加载状态
    isLoading: false,

    // 错误信息
    error: null
  }),

  getters: {
    /**
     * 返回消息数组
     * 若本地无数据（为null的时候）则自动触发同步，立即返回null
     */
    getMessageList: (state) => {
      if (state.messages === null) {
        // 触发同步但立即返回null
        const store = useMessageStore()
        store._syncMessages()
        return null
      }
      return state.messages
    },

    /**
     * 返回消息数量
     */
    getMessageCount: (state) => {
      if (state.messages === null) {
        const store = useMessageStore()
        store._syncMessages()
        return 0
      }
      return state.messages.length
    },

    /**
     * 获取状态为generating的消息
     */
    getIncompleteMessage: (state) => {
      if (state.messages === null) {
        const store = useMessageStore()
        store._syncMessages()
        return null
      }
      return state.messages.find(msg => msg.status === 'generating')
    },

    /**
     * 是否正在生成
     */
    getIsGenerating: (state) => state.isGenerating,

    /**
     * 加载状态
     */
    getIsLoading: (state) => state.isLoading,

    /**
     * 错误信息
     */
    getError: (state) => state.error
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

    /**
     * 工具方法：将后端消息转为前端消息
     */
    _convertBackendMessage(msg) {
      return {
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
        updated_at: msg.updated_at,
        agentName: this._getAgentNameForMessage(msg.role, msg.publisher)
      }
    },

    /**
     * 同步消息历史（内部接口）
     * 1. GET /projects/current/full-data，读取messages与incomplete_message_id
     * 2. 转换为前端消息结构并覆盖messages
     * 3. 若存在incomplete_message_id则自动调用续传接口建立SSE
     */
    async _syncMessages() {
      // 如果正在同步中，直接返回
      if (this.isLoading) {
        return
      }

      try {
        this.setLoading(true)
        this.clearError()

        // 1. 获取工程完整数据
        const response = await apiService.get('/projects/current/full-data')
        
        if (response.success && response.data) {
          const fullData = response.data
          const historyMessages = fullData.messages || []
          const incompleteMessageId = fullData.incomplete_message_id

          // 2. 转换为前端消息结构并覆盖messages
          this.messages = []
          for (const msg of historyMessages) {
            this.messages.push(this._convertBackendMessage(msg))
          }
          this.setLoading(false)

          // 3. 若存在incomplete_message_id则自动调用续传接口建立SSE
          if (incompleteMessageId) {
            console.log('⚠️ 发现未完成消息:', incompleteMessageId)
            console.log('🔄 开始继续传输未完成消息...')
            await this._continueIncompleteMessage(incompleteMessageId)
          } else {
            console.log('✅ 没有未完成的消息')
          }
        } else {
          this.messages = []
          this.setLoading(false)
        }

      } catch (error) {
        console.error('同步消息历史失败:', error)
        this.setError('同步消息失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    /**
     * 继续未完成的消息传输
     */
    async _continueIncompleteMessage(incompleteMessageId) {
      try {
        console.log('🔄 连接到继续传输接口:', incompleteMessageId)

        // 调用继续传输接口
        const response = await fetch(`${process.env.VUE_APP_API_BASE_URL || '/api'}/agents/messages/continue/${incompleteMessageId}`, {
          method: 'GET',
          headers: {
            'Accept': 'text/event-stream'
          }
        })

        if (response.status === 200) {
          console.log('✅ 继续传输连接成功，开始接收SSE流...')
          await this._handleSSEStream(response)
        } else {
          console.error('❌ 继续传输失败: HTTP', response.status)
        }

      } catch (error) {
        console.error('❌ 继续传输时出错:', error)
      }
    },

    /**
     * 发送消息，开始流式传输
     */
    async sendMessage(content, title, agentName, otherParams = {}) {
      try {
        this.clearError()

        const requestData = {
          content: content,
          title: title,
          agent_name: agentName,
          other_params: otherParams
        }

        console.log('📤 发送智能体消息:', requestData)

        // 发送POST请求启动智能体
        const response = await fetch(`${process.env.VUE_APP_API_BASE_URL || '/api'}/agents/messages`, {
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

        // 处理SSE流
        this._handleSSEStream(response) // 不再等待SSE流处理完成，让其在后台异步进行

      } catch (error) {
        console.error('❌ 发送消息失败:', error)
        this.setError(error.message || '发送消息失败')
        throw error
      }
    },

    /**
     * 中断流式传输
     */
    async stopMessage() {
      try {
        this.clearError()

        console.log('🛑 发送中断请求...')

        const response = await apiService.post('/agents/messages/stop')

        if (response.status === "success") {
          console.log('✅ 中断请求发送成功')
        } else {
          console.error('❌ 中断请求失败: HTTP', response.status)
        }

      } catch (error) {
        console.error('❌ 发送中断请求失败:', error)
        this.setError('中断请求失败')
        throw error
      }
    },

    /**
     * 处理SSE流（参考test_CLI_frontend.py的handle_sse_stream逻辑）
     */
    async _handleSSEStream(response) {
      try {
        console.log('🌊 开始处理SSE流...')
        // 设置生成状态
        this.isGenerating = true

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        let reading = true
        while (reading) {
          const { done, value } = await reader.read()

          if (done) {
            console.log('✅ SSE流结束')
            reading = false
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
                // 提取事件类型但不存储
                continue
              } else if (line.startsWith('data:')) {
                const data = line.substring(5).trim()

                if (data === '[DONE]') {
                  console.log('✅ 收到完成标志')
                  break
                }

                const eventData = JSON.parse(data)

                // 处理patch事件
                if (eventData.event === 'patch') {
                  await this._handlePatch(eventData.data || eventData)
                } else if (eventData.event === 'error') {
                  console.error('❌ 收到错误事件:', eventData.data)
                  this.setError('SSE连接错误')
                  break
                } else if (eventData.event === 'finished') {
                  console.log('✅ 收到完成事件:', eventData.data)
                  // 仅更新最后一个消息的状态
                  if (this.messages && this.messages.length > 0) {
                    const lastMessage = this.messages[this.messages.length - 1]
                    if (lastMessage) {
                      lastMessage.status = 'completed'
                    }
                  }
                } else {
                  // 直接作为patch数据处理
                  await this._handlePatch(eventData)
                }
              }
            } catch (error) {
              console.error('❌ 解析SSE数据失败:', error, 'line:', line)
            }
          }
        }
      } catch (error) {
        console.error('❌ 处理SSE流时出错:', error)
        this.setError('SSE连接错误')
      } finally {
        this.isGenerating = false
        this.currentGeneratingMessageId = null
        this.sseConnection = null
        const treeStore = useTreeStore()
        treeStore.setAgentOperatingNode(null)
      }
    },

    /**
     * 处理patch数据（参考test_CLI_frontend.py的handle_patch逻辑）
     */
    async _handlePatch(patchData) {
      try {
        //console.log('🔄 处理patch数据:', patchData)

        // 1. 用patch_data的role和publisher字段判断当前是否为智能体操作
        const treeStore = useTreeStore()
        let nodeId = null

        if (patchData.role === 'assistant' && patchData.publisher) {
          nodeId = patchData.publisher
        } else if (patchData.role === 'assistant' && !patchData.publisher) {
          nodeId = "-"
        } else if (patchData.role === 'user') {
          nodeId = null
        }

        if (nodeId) {
          treeStore.setAgentOperatingNode(nodeId)
        }

        // 2. 如果patch_data的snapshot字段不为空，调用treeStore的updateCurrentSnapshot
        if (patchData.snapshot && patchData.snapshot.data) {
          treeStore.updateCurrentSnapshot(patchData.snapshot.data)
        }

        // 3. 如果patch_data的rollback字段不为空且为true，执行回溯操作
        if (patchData.rollback === true) {
          const messageId = patchData.message_id
          if (!messageId) {
            console.error('❌ 回溯操作必须指定message_id')
            return
          }
          await this._handleRollback(messageId)
          return
        }

        // 4. 处理消息更新
        const messageId = patchData.message_id

        if (messageId === "-") {
          // 更新所有正在生成的消息
          this._updateAllGeneratingMessages(patchData)
        } else {
          if (this.messages === null) {
            this.messages = []
          }

          const existingMessage = this.messages.find(msg => msg.id === messageId)

          if (!existingMessage) {
            // 创建新消息
            await this._createMessageFromPatch(patchData)
          } else {
            // 更新现有消息
            this._updateExistingMessage(patchData)
          }
        }

      } catch (error) {
        console.error('❌ 处理patch时出错:', error)
        this.setError('处理消息更新失败')
      }
    },

    /**
     * 从patch创建新消息
     */
    async _createMessageFromPatch(patchData) {
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
        updated_at: new Date().toISOString(),
        agentName: this._getAgentNameForMessage(role, patchData.publisher)
      }

      if (this.messages === null) {
        this.messages = []
      }

      this.messages.push(message)

      // 更新生成状态
      if (!patchData.finished) {
        this.currentGeneratingMessageId = message.id
      }
    },

    /**
     * 获取消息的智能体名称
     */
    _getAgentNameForMessage(role, publisher) {
      if (role === 'user') {
        return '用户'
      } else if (role === 'system') {
        return '系统'
      } else if (role === 'assistant') {
        // 使用treeStore的工具函数获取智能体名称
        const treeStore = useTreeStore()
        return treeStore.getAgentNameByNodeId(publisher)
      }
      return '智能体'
    },

    /**
     * 更新现有消息
     */
    _updateExistingMessage(patchData) {
      const messageId = patchData.message_id
      const message = this.messages.find(msg => msg.id === messageId)

      if (!message) {
        console.error('❌ 消息不存在:', messageId)
        return
      }

      this._applyPatchToMessage(patchData, message)
    },

    /**
     * 更新所有正在生成的消息
     */
    _updateAllGeneratingMessages(patchData) {
      if (this.messages === null) {
        this.messages = []
        return
      }

      for (const message of this.messages) {
        if (message.status === 'generating') {
          this._applyPatchToMessage(patchData, message)
        }
      }
    },

    /**
     * 将patch应用到消息上
     */
    _applyPatchToMessage(patchData, message) {
      // 增量更新
      if (patchData.thinking_delta) {
        message.thinking += patchData.thinking_delta
      }
      if (patchData.content_delta) {
        message.content += patchData.content_delta
      }

      // 替换更新
      if (patchData.title != null) {
        message.title = patchData.title
      }
      if (patchData.action_title != null) {
        message.action_title = patchData.action_title
      }
      if (patchData.action_params != null) {
        message.action_params = patchData.action_params
      }
      if (patchData.snapshot_id != null) {
        message.snapshot_id = patchData.snapshot_id
      }
      if (patchData.visible_node_ids != null) {
        message.visible_node_ids = patchData.visible_node_ids
      }

      // 更新状态
      if (patchData.finished) {
        message.status = 'completed'
        this.currentGeneratingMessageId = null
      }

      // 更新时间戳
      message.updated_at = new Date().toISOString()
    },

    /**
     * 处理消息回溯
     */
    async _handleRollback(messageId) {
      try {
        if (this.messages === null) {
          console.warn('⚠️ 消息列表为空，无法执行回溯')
          return
        }

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
          targetMessage.content = ''
          targetMessage.thinking = ''
          targetMessage.status = 'generating'
          targetMessage.updated_at = new Date().toISOString()
        }

        console.log(`🔄 回溯消息: 删除了 ${messagesToRemove.length} 条消息`)

      } catch (error) {
        console.error('❌ 处理回溯时出错:', error)
        this.setError('消息回溯失败')
      }
    },

    /**
     * 回溯到指定消息（写入方法）
     * 删除指定消息之后的所有消息，并回退快照
     */
    async rollbackToMessage(messageId) {
      try {
        this.clearError()

        console.log('🔄 回溯到消息:', messageId)

        const response = await apiService.post(`/agents/messages/rollback-to/${messageId}`)

        if (response.success) {
          console.log('✅ 回溯操作成功')
          // 重新同步消息数据
          await this._syncMessages()
          return true
        } else {
          throw new Error(response.message || '回溯操作失败')
        }

      } catch (error) {
        console.error('❌ 回溯消息失败:', error)
        this.setError('回溯消息失败')
        throw error
      }
    },

    /**
     * 强制重新同步消息数据
     * 用于需要强制刷新消息数据的场景
     */
    async refreshMessages() {
      await this._syncMessages()
    },

    /**
     * 创建根问题
     * @param {Object} problemData - 问题数据（ProblemRequest格式）
     */
    async createRootProblem(problemData) {
      try {
        this.clearError()

        const response = await apiService.post('/research-tree/problems/root', problemData)

        if (response.success) {
          // 同步消息和树数据
          await this._syncMessages()
          const treeStore = useTreeStore()
          await treeStore.refreshCurrentSnapshot()
          return response.data
        } else {
          throw new Error(response.message || '创建根问题失败')
        }

      } catch (error) {
        console.error('创建根问题失败:', error)
        this.setError(error.message || '创建根问题失败')
        throw error
      }
    },

    /**
     * 更新根问题
     * @param {string} problemId - 问题ID
     * @param {Object} problemData - 问题数据（ProblemRequest格式）
     */
    async updateRootProblem(problemId, problemData) {
      try {
        this.clearError()

        const response = await apiService.patch(`/research-tree/problems/root/${problemId}`, problemData)

        if (response.success) {
          // 同步消息和树数据
          await this._syncMessages()
          const treeStore = useTreeStore()
          await treeStore.refreshCurrentSnapshot()
          return response.data
        } else {
          throw new Error(response.message || '更新根问题失败')
        }

      } catch (error) {
        console.error('更新根问题失败:', error)
        this.setError(error.message || '更新根问题失败')
        throw error
      }
    },

    /**
     * 删除根问题
     * @param {string} problemId - 问题ID
     */
    async deleteRootProblem(problemId) {
      try {
        this.clearError()

        const response = await apiService.delete(`/research-tree/problems/root/${problemId}`)

        if (response.success) {
          // 同步消息和树数据
          await this._syncMessages()
          const treeStore = useTreeStore()
          await treeStore.refreshCurrentSnapshot()
          return response.data
        } else {
          throw new Error(response.message || '删除根问题失败')
        }

      } catch (error) {
        console.error('删除根问题失败:', error)
        this.setError(error.message || '删除根问题失败')
        throw error
      }
    },

    /**
     * 创建解决方案
     * @param {string} problemId - 父问题ID
     * @param {Object} solutionData - 解决方案数据（SolutionRequest格式）
     */
    async createSolution(problemId, solutionData) {
      try {
        this.clearError()

        const response = await apiService.post(`/research-tree/problems/${problemId}/solutions`, solutionData)

        if (response.success) {
          // 同步消息和树数据
          await this._syncMessages()
          const treeStore = useTreeStore()
          await treeStore.refreshCurrentSnapshot()
          return response.data
        } else {
          throw new Error(response.message || '创建解决方案失败')
        }

      } catch (error) {
        console.error('创建解决方案失败:', error)
        this.setError(error.message || '创建解决方案失败')
        throw error
      }
    },

    /**
     * 更新解决方案
     * @param {string} solutionId - 解决方案ID
     * @param {Object} solutionData - 解决方案数据（SolutionRequest格式）
     */
    async updateSolution(solutionId, solutionData) {
      try {
        this.clearError()

        const response = await apiService.patch(`/research-tree/solutions/${solutionId}`, solutionData)

        if (response.success) {
          // 同步消息和树数据
          await this._syncMessages()
          const treeStore = useTreeStore()
          await treeStore.refreshCurrentSnapshot()
          return response.data
        } else {
          throw new Error(response.message || '更新解决方案失败')
        }

      } catch (error) {
        console.error('更新解决方案失败:', error)
        this.setError(error.message || '更新解决方案失败')
        throw error
      }
    },

    /**
     * 删除解决方案
     * @param {string} solutionId - 解决方案ID
     */
    async deleteSolution(solutionId) {
      try {
        this.clearError()

        const response = await apiService.delete(`/research-tree/solutions/${solutionId}`)

        if (response.success) {
          // 同步消息和树数据
          await this._syncMessages()
          const treeStore = useTreeStore()
          await treeStore.refreshCurrentSnapshot()
          return response.data
        } else {
          throw new Error(response.message || '删除解决方案失败')
        }

      } catch (error) {
        console.error('删除解决方案失败:', error)
        this.setError(error.message || '删除解决方案失败')
        throw error
      }
    },

    /**
     * 设置选中解决方案
     * @param {string} problemId - 问题ID
     * @param {string|null} solutionId - 解决方案ID
     */
    async setSelectedSolution(problemId, solutionId) {
      try {
        this.clearError()

        const requestData = {
          solution_id: solutionId
        }

        const response = await apiService.post(`/research-tree/problems/${problemId}/selected-solution`, requestData)

        if (response.success) {
          // 同步消息和树数据
          await this._syncMessages()
          const treeStore = useTreeStore()
          await treeStore.refreshCurrentSnapshot()
          return response.data
        } else {
          throw new Error(response.message || '设置选中解决方案失败')
        }

      } catch (error) {
        console.error('设置选中解决方案失败:', error)
        this.setError(error.message || '设置选中解决方案失败')
        throw error
      }
    },
  }
})
