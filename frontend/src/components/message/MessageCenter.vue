<template>
  <div class="message-center">
    
    <!-- 智能体选择区域 -->
    <div class="agent-selection-area">
      <el-select
        v-model="selectedAgent"
        placeholder="选择智能体"
        :disabled="isGenerating"
        style="width: 100%; margin-bottom: 8px;"
        @change="handleAgentChange"
      >
        <el-option
          v-for="agent in availableAgents"
          :key="agent.value"
          :label="agent.label"
          :value="agent.value"
        />
      </el-select>
      
      <el-select
        v-model="selectedNodeTitle"
        placeholder="选择节点"
        :disabled="isGenerating || !selectedAgent"
        style="width: 100%;"
        @change="handleNodeChange"
      >
        <el-option
          v-for="title in filteredTitles"
          :key="title"
          :label="title"
          :value="title"
        />
      </el-select>
    </div>
    
    <!-- 消息列表区域 -->
    <div class="message-list-area">
      <MessageList
        :messages="getMessageList"
        :is-loading="isLoading"
        :is-generating="isGenerating"
        :current-agent-name="getCurrentAgentName"
        @view-snapshot="handleViewSnapshot"
        @rollback="handleRollback"
        @stop-generation="handleStopGeneration"
      />
    </div>
    
    <!-- 输入区域 -->
    <div class="input-area">
      <ChatInput
        v-model="inputContent"
        :disabled="isGenerating || !canInputMessage"
        :is-loading="isGenerating"
        @send="handleSendMessage"
      />
    </div>
    
    <!-- 错误提示 -->
    <transition name="slide-up">
      <div v-if="error" class="error-banner">
        <el-alert
          :title="error"
          type="error"
          :closable="true"
          @close="clearError"
        />
      </div>
    </transition>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus'
import { useMessageStore } from '@/stores/messageStore'
import { useTreeStore } from '@/stores/treeStore'
import { useProjectStore } from '@/stores/projectStore'
import MessageList from './MessageList.vue'
import ChatInput from './ChatInput.vue'

export default {
  name: 'MessageCenter',
  
  components: {
    MessageList,
    ChatInput
  },
  
  emits: [],
  
  data() {
    return {
      messageStore: null,
      treeStore: null,
      projectStore: null,
      selectedAgent: '',
      selectedNodeTitle: '',
      inputContent: ''
    }
  },
  
  computed: {
    messageCount() {
      return this.messageStore?.getMessageCount || 0
    },

    isLoading() {
      return this.messageStore?.getIsLoading || false
    },

    isGenerating() {
      return this.messageStore?.getIsGenerating || false
    },

    error() {
      return this.messageStore?.getError
    },

    currentSnapshot() {
      return this.treeStore?.getCurrentSnapshot
    },

    getMessageList() {
      return this.messageStore?.getMessageList || []
    },

    getCurrentAgentName() {
      return this.treeStore?.getCurrentAgentName
    },
    
    // 可用智能体列表
    availableAgents() {
      return [
        { value: 'auto_research_agent', label: '自动研究智能体', messageTitle: '启动自动研究' },
        { value: 'user_chat_agent', label: '用户对话智能体', messageTitle: '用户消息' }
      ]
    },
    
    // 根据智能体类型过滤标题
    filteredTitles() {
      if (!this.selectedAgent) return []

      if (this.selectedAgent === 'auto_research_agent') {
        // 从treeStore获取实施问题标题列表
        return this.treeStore?.getAllImplementaionProblemTitles() || []
      } else if (this.selectedAgent === 'user_chat_agent') {
        // 从treeStore获取解决方案标题列表
        return this.treeStore?.getAllSolutionTitles() || []
      }

      return []
    },
    
    // 检查是否可以发送消息
    canSendMessage() {
      // 必须选择智能体和节点，且输入内容不为空，并且当前不在生成状态
      return this.selectedAgent && this.selectedNodeTitle && this.inputContent.trim();
    },

    canInputMessage() {
      return this.selectedAgent && this.selectedNodeTitle;
    }
   },
  
  watch: {
    // 监听项目变更
    'projectStore.getCurrentProject': {
      async handler(newProject) {
        if (newProject) {
          // 刷新消息数据
          await this.messageStore.refreshMessages()
          // 重置选择
          this.selectedAgent = ''
          this.selectedNodeTitle = ''
          this.inputContent = ''
        }
      },
      immediate: false
    }
  },
  
  async mounted() {
    this.messageStore = useMessageStore()
    this.treeStore = useTreeStore()
    this.projectStore = useProjectStore()
    await this.messageStore.refreshMessages()

    // 初始化消息列表：getters会自动触发同步
  },
  
  methods: {
    // 处理智能体选择
    handleAgentChange(agentName) {
      this.selectedAgent = agentName
      this.selectedNodeTitle = ''
      this.inputContent = ''
    },

    // 处理节点选择
    handleNodeChange(title) {
      // 直接存储节点标题
      this.selectedNodeTitle = title
    },
    
    
    // 发送消息
    async handleSendMessage() {
      if (!this.canSendMessage) {
        ElMessage.warning('请完善消息内容')
        return
      }

      try {
        // 获取智能体对应的消息标题
        const agentInfo = this.availableAgents.find(agent => agent.value === this.selectedAgent)
        const messageTitle = agentInfo?.messageTitle || '用户消息'

        // 根据标题获取节点ID
        const nodeId = this.treeStore?.getNodeIdByTitle(this.selectedNodeTitle)

        // 调用发送消息方法
        const otherParams = this.selectedAgent === 'auto_research_agent'
          ? { problem_id: nodeId }
          : this.selectedAgent === 'user_chat_agent'
            ? { solution_id: nodeId }
            : {}

        await this.messageStore.sendMessage(
          this.inputContent.trim(),
          messageTitle,
          this.selectedAgent,
          otherParams
        )

        // 清空输入
        this.inputContent = ''

        ElMessage.success('消息发送成功')
      } catch (error) {
        console.error('发送消息失败:', error)
        ElMessage.error('发送消息失败')
      }
    },
    
    // 查看快照
    async handleViewSnapshot(snapshotId) {
      try {
        await this.treeStore.viewSnapshot(snapshotId)
      } catch (error) {
        console.error('查看快照失败:', error)
        ElMessage.error('查看快照失败')
      }
    },

    // 处理消息回溯
    async handleRollback(messageId) {
      try {
        // 如果当前有消息正在生成，先停止生成
        if (this.isGenerating) {
          console.log('⚠️ 检测到正在生成的消息，先停止生成...')
          await this.handleStopGeneration()
        }

        await this.messageStore.rollbackToMessage(messageId)
        await this.treeStore.refreshCurrentSnapshot()
        ElMessage.success('消息回溯成功')
      } catch (error) {
        console.error('消息回溯失败:', error)
        ElMessage.error('消息回溯失败')
      }
    },

    // 处理停止生成
    async handleStopGeneration() {
      try {
        await this.messageStore.stopMessage()
        ElMessage.success('已停止生成')
      } catch (error) {
        console.error('停止生成失败:', error)
        ElMessage.error('停止生成失败')
      }
    }
  }
}
</script>

<style scoped>
.message-center {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-color);
  border-radius: 8px;
  overflow: hidden;
}



/* 智能体选择区域 */
.agent-selection-area {
  padding: 12px 16px;
  background: var(--bg-color);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

/* 消息列表区域 */
.message-list-area {
  flex: 1;
  min-height: 0; /* 重要：允许flex子项缩小 */
  background: var(--bg-color);
}

/* 输入区域 */
.input-area {
  padding: 12px 16px;
  background: var(--bg-color);
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
}

/* 错误横幅 */
.error-banner {
  position: absolute;
  top: 70px;
  left: 20px;
  right: 20px;
  z-index: 100;
  box-shadow: 0 4px 12px rgba(245, 108, 108, 0.3);
}

/* 动画效果 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* 响应式设计 */
@media (max-width: 767px) {
  .message-header {
    padding: 12px 16px;
    flex-wrap: wrap;
  gap: 12px;
  }
  
  .header-left,
  .header-right {
    gap: 8px;
  }
  
  .header-title {
    font-size: 15px;
  }
  
  .connection-status {
    font-size: 11px;
    padding: 3px 6px;
  }
  
  .agent-selection-area {
    padding: 16px;
  }
  
  .input-area {
    padding: 16px;
  }
  
  .error-banner {
    top: 60px;
    left: 16px;
    right: 16px;
  }
}

/* 无障碍支持 */
@media (prefers-reduced-motion: reduce) {
  .status-generating .el-icon {
    animation: none;
  }
  
  .connection-status {
    transition: none;
  }
}

/* 暗色主题适配 */
.dark-theme .status-connected {
  background: rgba(103, 194, 58, 0.1);
}

.dark-theme .status-generating {
  background: rgba(230, 162, 60, 0.1);
}

.dark-theme .status-error {
  background: rgba(245, 108, 108, 0.1);
}

.dark-theme .error-banner {
  box-shadow: 0 4px 12px rgba(245, 108, 108, 0.4);
}
</style>