<template>
  <div class="message-center">
    
    <!-- 智能体选择区域 -->
    <div class="agent-selection-area">
      <el-select
        v-model="selectedAgent"
        placeholder="选择智能体"
        :disabled="isGenerating"
        style="width: 100%; margin-bottom: 8px;"
        @change="handleAgentChanged"
      >
        <el-option
          v-for="agent in availableAgents"
          :key="agent.value"
          :label="agent.label"
          :value="agent.value"
        />
      </el-select>
      
      <el-select
        v-model="selectedNode"
        placeholder="选择节点"
        :disabled="isGenerating || !selectedAgent"
        style="width: 100%;"
        @change="handleNodeChanged"
      >
        <el-option
          v-for="node in filteredNodes"
          :key="node.id"
          :label="node.title"
          :value="node.id"
        />
      </el-select>
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
import { ElMessage } from 'element-plus'
import { useMessageStore } from '@/stores/messageStore'
import { useTreeStore } from '@/stores/treeStore'
import { useProjectStore } from '@/stores/projectStore'
import MessageList from './MessageList.vue'
import ChatInput from './ChatInput.vue'

export default defineComponent({
  name: 'MessageCenter',
  
  components: {
    MessageList,
    ChatInput
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
    
    // 可用智能体列表
    const availableAgents = computed(() => [
      { value: 'auto_research_agent', label: '自动研究智能体' },
      { value: 'user_chat_agent', label: '用户对话智能体' }
    ])
    
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
    
    // 根据智能体类型过滤节点
    const filteredNodes = computed(() => {
      if (!selectedAgent.value) return []
      
      const nodes = availableNodes.value
      
      if (selectedAgent.value === 'auto_research_agent') {
        // 只显示实施问题节点
        return nodes.filter(node => 
          node.type === 'problem' && node.problem_type === 'implementation'
        )
      } else if (selectedAgent.value === 'user_chat_agent') {
        // 只显示解决方案节点
        return nodes.filter(node => node.type === 'solution')
      }
      
      return []
    })
    
    // 是否可以发送消息
    const canSendMessage = computed(() => {
      return selectedAgent.value && 
             selectedNode.value && 
             !isGenerating.value && 
             inputContent.value.trim().length > 0
    })
    

    

    
    // 方法
    const handleAgentChanged = (agentValue) => {
      selectedAgent.value = agentValue
      selectedNode.value = ''
      selectedNodeInfo.value = null
      
      console.log('智能体已切换:', agentValue)
    }
    
    const handleNodeChanged = (nodeId) => {
      selectedNode.value = nodeId
      // 根据节点ID找到节点信息
      const node = availableNodes.value.find(n => n.id === nodeId)
      selectedNodeInfo.value = node || null
      
      console.log('节点已切换:', nodeId, node)
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
      availableAgents,
      filteredNodes,
      canSendMessage,
      handleAgentChanged,
      handleNodeChanged,
      handleSendMessage,
      handleTitleChange,
      handleViewSnapshot,
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