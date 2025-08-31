<template>
  <div class="message-center">
    <!-- 消息中心头部 -->
    <div class="message-header">
      <div class="header-left">
        <el-icon><ChatDotRound /></el-icon>
        <span class="header-title">智能体对话</span>
        <el-tag v-if="messageCount > 0" type="info" size="small">
          {{ messageCount }} 条消息
        </el-tag>
      </div>
      
      <div class="header-right">
        <!-- 连接状态指示 -->
        <div class="connection-status" :class="connectionStatusClass">
          <el-icon><component :is="connectionStatusIcon" /></el-icon>
          <span class="status-text">{{ connectionStatusText }}</span>
        </div>
        
        <!-- 操作按钮 -->
        <el-dropdown @command="handleHeaderAction" trigger="click">
          <el-button type="text" size="small">
            <el-icon><More /></el-icon>
          </el-button>
          
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item 
                command="sync-messages"
                :icon="Refresh"
                :disabled="isLoading"
              >
                同步消息
              </el-dropdown-item>
              <el-dropdown-item 
                command="clear-messages"
                :icon="Delete"
                divided
              >
                清空消息
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    
    <!-- 智能体选择区域 -->
    <div class="agent-selection-area">
      <AgentSelector
        v-model="selectedAgent"
        :disabled="isGenerating"
        :available-nodes="availableNodes"
        @agent-changed="handleAgentChanged"
      />
      
      <NodeSelector
        v-model="selectedNode"
        :agent-type="selectedAgent"
        :available-nodes="availableNodes"
        :disabled="isGenerating"
        @node-changed="handleNodeChanged"
      />
    </div>
    
    <!-- 消息列表区域 -->
    <div class="message-list-area">
      <MessageList
        :enable-virtual-scroll="enableVirtualScroll"
        @view-snapshot="handleViewSnapshot"
      />
    </div>
    
    <!-- 输入区域 -->
    <div class="input-area">
      <ChatInput
        v-model="inputContent"
        :title="inputTitle"
        :agent-type="selectedAgent"
        :selected-node="selectedNodeInfo"
        :disabled="!canSendMessage"
        :is-loading="isGenerating"
        @send="handleSendMessage"
        @title-change="handleTitleChange"
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
import { defineComponent, ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ChatDotRound, More, Refresh, Delete, 
  Connection, Loading, Check
} from '@element-plus/icons-vue'
import { useMessageStore } from '@/stores/messageStore'
import { useTreeStore } from '@/stores/treeStore'
import { useProjectStore } from '@/stores/projectStore'
import AgentSelector from './AgentSelector.vue'
import NodeSelector from './NodeSelector.vue'
import MessageList from './MessageList.vue'
import ChatInput from './ChatInput.vue'

export default defineComponent({
  name: 'MessageCenter',
  
  components: {
    AgentSelector,
    NodeSelector,
    MessageList,
    ChatInput,
    ChatDotRound, More, Refresh, Delete,
    Connection, Loading, Check
  },
  
  props: {
    // 是否启用虚拟滚动
    enableVirtualScroll: {
      type: Boolean,
      default: false
    }
  },
  
  emits: ['view-snapshot'],
  
  setup(props, { emit }) {
    const messageStore = useMessageStore()
    const treeStore = useTreeStore()
    const projectStore = useProjectStore()
    
    // 响应式数据
    const selectedAgent = ref('')
    const selectedNode = ref('')
    const selectedNodeInfo = ref(null)
    const selectedAgentInfo = ref(null)
    const inputContent = ref('')
    const inputTitle = ref('')
    
    // 计算属性
    const messageCount = computed(() => messageStore.messageCount)
    const isLoading = computed(() => messageStore.isLoading)
    const isGenerating = computed(() => messageStore.isGenerating)
    const error = computed(() => messageStore.error)
    const currentSnapshot = computed(() => treeStore.currentSnapshot)
    
    // 可用节点列表
    const availableNodes = computed(() => {
      const snapshot = currentSnapshot.value
      if (!snapshot || !snapshot.roots) {
        return []
      }
      
      // 递归收集所有节点
      const collectNodes = (nodes, parentPath = []) => {
        const result = []
        
        for (const node of nodes) {
          const nodeWithPath = {
            ...node,
            path: [...parentPath, node.title]
          }
          result.push(nodeWithPath)
          
          if (node.children && node.children.length > 0) {
            result.push(...collectNodes(node.children, nodeWithPath.path))
          }
        }
        
        return result
      }
      
      return collectNodes(snapshot.roots)
    })
    
    // 是否可以发送消息
    const canSendMessage = computed(() => {
      return selectedAgent.value && 
             selectedNode.value && 
             !isGenerating.value && 
             inputContent.value.trim().length > 0
    })
    
    // 连接状态
    const connectionStatus = computed(() => {
      if (isGenerating.value) {
        return 'generating'
      } else if (error.value) {
        return 'error'
      } else {
        return 'connected'
      }
    })
    
    const connectionStatusClass = computed(() => {
      return `status-${connectionStatus.value}`
    })
    
    const connectionStatusIcon = computed(() => {
      switch (connectionStatus.value) {
        case 'generating': return 'Loading'
        case 'error': return 'Connection'
        case 'connected': return 'Connection'
        default: return 'Check'
      }
    })
    
    const connectionStatusText = computed(() => {
      switch (connectionStatus.value) {
        case 'generating': return '正在生成...'
        case 'error': return '连接错误'
        case 'connected': return '已连接'
        default: return '就绪'
      }
    })
    
    // 方法
    const handleAgentChanged = (agentInfo) => {
      selectedAgentInfo.value = agentInfo
      selectedNode.value = ''
      selectedNodeInfo.value = null
      
      console.log('智能体已切换:', agentInfo)
    }
    
    const handleNodeChanged = (nodeInfo) => {
      selectedNodeInfo.value = nodeInfo
      
      console.log('节点已切换:', nodeInfo)
    }
    
    const handleSendMessage = async (messageData) => {
      try {
        if (!selectedAgent.value) {
          ElMessage.warning('请先选择智能体')
          return
        }
        
        if (!selectedNode.value) {
          ElMessage.warning('请先选择节点')
          return
        }
        
        console.log('发送消息:', messageData)
        
        // 准备智能体参数
        const otherParams = {}
        
        if (selectedAgent.value === 'auto_research_agent') {
          otherParams.problem_id = selectedNode.value
        } else if (selectedAgent.value === 'user_chat_agent') {
          otherParams.solution_id = selectedNode.value
        }
        
        // 发送消息
        const success = await messageStore.sendAgentMessage(
          selectedAgent.value,
          messageData.content,
          messageData.title,
          otherParams
        )
        
        if (success) {
          console.log('消息发送成功')
          // 清空输入内容在ChatInput组件中处理
        } else {
          ElMessage.error('消息发送失败')
        }
        
      } catch (error) {
        console.error('发送消息失败:', error)
        ElMessage.error('发送消息失败')
      }
    }
    
    const handleTitleChange = (title) => {
      inputTitle.value = title
    }
    
    const handleViewSnapshot = (snapshotId) => {
      console.log('查看快照:', snapshotId)
      emit('view-snapshot', snapshotId)
    }
    
    const handleHeaderAction = async (command) => {
      try {
        switch (command) {
          case 'sync-messages':
            await syncMessages()
            break
          case 'clear-messages':
            await clearMessages()
            break
        }
      } catch (error) {
        console.error('操作失败:', error)
        ElMessage.error('操作失败')
      }
    }
    
    const syncMessages = async () => {
      try {
        const success = await messageStore.syncMessagesFromBackend()
        if (success) {
          ElMessage.success('消息同步成功')
        } else {
          ElMessage.error('消息同步失败')
        }
      } catch (error) {
        console.error('同步消息失败:', error)
        ElMessage.error('同步消息失败')
      }
    }
    
    const clearMessages = async () => {
      try {
        await ElMessageBox.confirm(
          '确定要清空所有消息吗？此操作不可恢复。',
          '确认清空',
          {
            confirmButtonText: '确定清空',
            cancelButtonText: '取消',
            type: 'warning',
            confirmButtonClass: 'el-button--danger'
          }
        )
        
        messageStore.clearMessages()
        ElMessage.success('消息已清空')
        
      } catch (error) {
        // 用户取消操作
        if (error === 'cancel') {
          return
        }
        throw error
      }
    }
    
    const clearError = () => {
      messageStore.clearError()
    }
    
    // 初始化
    const initialize = async () => {
      try {
        console.log('初始化消息中心...')
        
        // 同步消息历史
        await messageStore.syncMessagesFromBackend()
        
        console.log('消息中心初始化完成')
      } catch (error) {
        console.error('初始化消息中心失败:', error)
        ElMessage.error('初始化失败')
      }
    }
    
    // 监听工程变化，重新初始化
    watch(() => projectStore.currentProject, async (newProject) => {
      if (newProject) {
        await initialize()
      }
    })
    
    // 生命周期
    onMounted(async () => {
      await initialize()
    })
    
    onBeforeUnmount(() => {
      // 断开SSE连接
      messageStore.disconnectSSE()
    })
    
    return {
      selectedAgent,
      selectedNode,
      selectedNodeInfo,
      selectedAgentInfo,
      inputContent,
      inputTitle,
      messageCount,
      isLoading,
      isGenerating,
      error,
      availableNodes,
      canSendMessage,
      connectionStatusClass,
      connectionStatusIcon,
      connectionStatusText,
      handleAgentChanged,
      handleNodeChanged,
      handleSendMessage,
      handleTitleChange,
      handleViewSnapshot,
      handleHeaderAction,
      clearError
    }
  }
})
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

/* 消息头部 */
.message-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: var(--bg-color-light, #f8f9fa);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 连接状态 */
.connection-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 12px;
  transition: all 0.3s;
}

.status-connected {
  color: var(--success-color);
  background: var(--success-color-lighter, #f0f9ff);
}

.status-generating {
  color: var(--warning-color);
  background: var(--warning-color-lighter, #fdf6ec);
}

.status-generating .el-icon {
  animation: spin 1s linear infinite;
}

.status-error {
  color: var(--danger-color);
  background: var(--danger-color-lighter, #fef0f0);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.status-text {
  font-weight: 500;
}

/* 智能体选择区域 */
.agent-selection-area {
  padding: 20px;
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
  padding: 20px;
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