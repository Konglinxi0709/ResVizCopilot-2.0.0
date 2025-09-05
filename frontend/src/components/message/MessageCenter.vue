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
        v-model="selectedNode"
        placeholder="选择节点"
        :disabled="isGenerating || !selectedAgent"
        style="width: 100%;"
        @change="handleNodeChange"
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
        :disabled="isGenerating"
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
  
  props: {
    // 是否启用虚拟滚动
    enableVirtualScroll: {
      type: Boolean,
      default: false
    }
  },
  
  emits: ['view-snapshot'],
  
  data() {
    return {
      messageStore: null,
      treeStore: null,
      projectStore: null,
      selectedAgent: '',
      selectedNode: '',
      selectedNodeInfo: null,
      selectedAgentInfo: null,
      inputContent: '',
      inputTitle: ''
    }
  },
  
  computed: {
    messageCount() {
      return this.messageStore?.messageCount || 0
    },
    
    isLoading() {
      return this.messageStore?.isLoading || false
    },
    
    isGenerating() {
      return this.messageStore?.isGenerating || false
    },
    
    error() {
      return this.messageStore?.error
    },
    
    currentSnapshot() {
      return this.treeStore?.currentSnapshot
    },
    
    // 可用智能体列表
    availableAgents() {
      return [
        { value: 'auto_research_agent', label: '自动研究智能体' },
        { value: 'user_chat_agent', label: '用户对话智能体' }
      ]
    },
    
    // 可用节点列表
    availableNodes() {
      const snapshot = this.currentSnapshot
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
    },
    
    // 根据智能体类型过滤节点
    filteredNodes() {
      if (!this.selectedAgent) return []
      
      const nodes = this.availableNodes
      
      if (this.selectedAgent === 'auto_research_agent') {
        // 只显示实施问题节点
        return nodes.filter(node => 
          node.type === 'problem' && node.problem_type === 'implementation'
        )
      } else if (this.selectedAgent === 'user_chat_agent') {
        // 只显示解决方案节点
        return nodes.filter(node => node.type === 'solution')
      }
      
      return []
    },
    
    // 检查是否可以发送消息
    canSendMessage() {
      return this.selectedAgent && 
             this.selectedNode && 
             this.inputContent.trim() && 
             !this.isGenerating
    }
  },
  
  watch: {
    // 监听项目变更
    'projectStore.currentProject': {
      async handler(newProject) {
        if (newProject) {
          // 清空消息列表
          this.messageStore.clearMessages()
          // 重置选择
          this.selectedAgent = ''
          this.selectedNode = ''
          this.selectedNodeInfo = null
          this.selectedAgentInfo = null
          this.inputContent = ''
          this.inputTitle = ''
        }
      },
      immediate: false
    }
  },
  
  async mounted() {
    this.messageStore = useMessageStore()
    this.treeStore = useTreeStore()
    this.projectStore = useProjectStore()
    
    // 初始化消息列表：每次挂载（v-if展开）都强制从后端同步
    await this.messageStore.syncMessagesFromBackend()
  },
  
  methods: {
    // 处理智能体选择
    handleAgentChange(agentName) {
      this.selectedAgent = agentName
      this.selectedNode = ''
      this.selectedNodeInfo = null
      this.selectedAgentInfo = null
      
      // 更新智能体信息
      this.selectedAgentInfo = this.availableAgents.find(
        agent => agent.value === agentName
      )
    },
    
    // 处理节点选择
    handleNodeChange(nodeId) {
      this.selectedNode = nodeId
      
      // 更新节点信息
      this.selectedNodeInfo = this.filteredNodes.find(
        node => node.id === nodeId
      )
    },
    
    // 处理输入内容变更
    handleContentChange(content) {
      this.inputContent = content
    },
    
    // 处理标题变更
    handleTitleChange(title) {
      this.inputTitle = title
    },
    
    // 发送消息
    async handleSendMessage() {
      if (!this.canSendMessage) {
        ElMessage.warning('请完善消息内容')
        return
      }
      
      try {
        // 直接调用基于CLI语义的sendAgentMessage
        const otherParams = this.selectedAgent === 'auto_research_agent'
          ? { problem_id: this.selectedNode }
          : this.selectedAgent === 'user_chat_agent'
            ? { solution_id: this.selectedNode }
            : {}
        await this.messageStore.sendAgentMessage(
          this.selectedAgent,
          this.inputContent.trim(),
          this.inputTitle.trim() || '用户消息',
          otherParams
        )
        
        // 清空输入
        this.inputContent = ''
        this.inputTitle = ''
        
        ElMessage.success('消息发送成功')
      } catch (error) {
        console.error('发送消息失败:', error)
        ElMessage.error('发送消息失败')
      }
    },
    
    // 查看快照
    handleViewSnapshot(snapshotId) {
      this.$emit('view-snapshot', snapshotId)
    },
    
    // 停止生成
    async handleStopGeneration() {
      try {
        await this.messageStore.stopGeneration()
        ElMessage.success('已停止生成')
      } catch (error) {
        console.error('停止生成失败:', error)
        ElMessage.error('停止生成失败')
      }
    },
    
    // 清空消息
    async handleClearMessages() {
      try {
        await this.messageStore.clearMessages()
        ElMessage.success('消息已清空')
      } catch (error) {
        console.error('清空消息失败:', error)
        ElMessage.error('清空消息失败')
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