<template>
  <div class="message-item" :class="[`message-${message.role}`, { 'generating': isGenerating }]">
    <!-- 消息头部 -->
    <div class="message-header">
      <div class="message-sender">
        <!-- 发送者头像 -->
        <div class="sender-avatar" :class="`avatar-${message.role}`">
          <el-icon v-if="message.role === 'user'">
            <User />
          </el-icon>
          <el-icon v-else-if="message.role === 'assistant'">
            <UserFilled />
          </el-icon>
          <el-icon v-else>
            <InfoFilled />
          </el-icon>
        </div>
        
        <!-- 发送者信息 -->
        <div class="sender-info">
          <div class="sender-name">{{ senderName }}</div>
          <div class="message-time">{{ formatTime(message.created_at) }}</div>
        </div>
      </div>
      
      <!-- 消息状态指示 -->
      <div class="message-status">
        <el-tag 
          v-if="isGenerating" 
          type="warning" 
          size="small"
          :icon="Loading"
        >
          生成中...
        </el-tag>
        <el-tag 
          v-else-if="message.status === 'completed'" 
          type="success" 
          size="small"
        >
          已完成
        </el-tag>
        <el-tag 
          v-else-if="message.status === 'failed'" 
          type="danger" 
          size="small"
        >
          失败
        </el-tag>
      </div>
      
      <!-- 消息操作按钮 -->
      <div class="message-actions">
        <el-dropdown 
          @command="handleAction"
          trigger="click"
          placement="bottom-end"
        >
          <el-button type="text" size="small" class="action-btn">
            <el-icon><More /></el-icon>
          </el-button>
          
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item 
                v-if="message.snapshot_id" 
                command="view-snapshot"
                :icon="Camera"
              >
                查看快照
              </el-dropdown-item>
              <el-dropdown-item 
                command="copy-content"
                :icon="CopyDocument"
              >
                复制内容
              </el-dropdown-item>
              <el-dropdown-item 
                command="rollback"
                :icon="RefreshLeft"
                divided
              >
                回溯到此消息
              </el-dropdown-item>
              <el-dropdown-item 
                v-if="isGenerating"
                command="stop"
                :icon="VideoPause"
              >
                停止生成
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    
    <!-- 消息内容区域 -->
    <div class="message-content">
      <!-- 消息标题 -->
      <div 
        v-if="message.title" 
        class="message-title" 
        :class="{ 'collapsed': titleCollapsed }"
        @click="titleCollapsed = !titleCollapsed"
      >
        <el-icon class="collapse-icon">
          <ArrowDown v-if="titleCollapsed" />
          <ArrowUp v-else />
        </el-icon>
        <span class="title-text">{{ message.title }}</span>
      </div>
      
      <!-- 消息主体内容 -->
      <div 
        v-if="message.content && !titleCollapsed" 
        class="message-body"
        :class="{ 'collapsed': contentCollapsed }"
      >
        <div class="content-header" @click="contentCollapsed = !contentCollapsed">
          <el-icon class="collapse-icon">
            <ArrowDown v-if="contentCollapsed" />
            <ArrowUp v-else />
          </el-icon>
          <span class="section-title">内容</span>
        </div>
        
        <div v-if="!contentCollapsed" class="content-body">
          <MarkdownRenderer :content="message.content" />
        </div>
      </div>
      
      <!-- 思考过程 -->
      <div 
        v-if="message.thinking && !titleCollapsed" 
        class="message-thinking"
        :class="{ 'collapsed': thinkingCollapsed }"
      >
        <div class="thinking-header" @click="thinkingCollapsed = !thinkingCollapsed">
          <el-icon class="collapse-icon">
            <ArrowDown v-if="thinkingCollapsed" />
            <ArrowUp v-else />
          </el-icon>
          <span class="section-title">思考过程</span>
        </div>
        
        <div v-if="!thinkingCollapsed" class="thinking-body">
          <MarkdownRenderer :content="message.thinking" />
        </div>
      </div>
      

      
      <!-- 可见节点信息 -->
      <div 
        v-if="message.visible_node_ids && message.visible_node_ids.length > 0 && !titleCollapsed" 
        class="visible-nodes"
      >
        <div class="nodes-info">
          <el-icon><View /></el-icon>
          <span>可见节点: {{ message.visible_node_ids.length }} 个</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  User, UserFilled, InfoFilled, More,
  ArrowDown, ArrowUp,
  View
} from '@element-plus/icons-vue'
import { useTreeStore } from '@/stores/treeStore'
import MarkdownRenderer from './MarkdownRenderer.vue'
import dayjs from 'dayjs'

export default defineComponent({
  name: 'MessageItem',
  
  components: {
    MarkdownRenderer,
    User, UserFilled, InfoFilled, More,
    ArrowDown, ArrowUp,
    View
  },
  
  props: {
    message: {
      type: Object,
      required: true
    }
  },
  
  emits: ['view-snapshot', 'rollback', 'stop-generation'],
  
  setup(props, { emit }) {
    const treeStore = useTreeStore()
    
    // 展开/折叠状态
    const titleCollapsed = ref(false)
    const contentCollapsed = ref(false)
    const thinkingCollapsed = ref(true) // 思考过程默认折叠
    
    // 计算属性
    const isGenerating = computed(() => {
      return props.message.status === 'generating'
    })
    
    const senderName = computed(() => {
      const message = props.message
      
      if (message.role === 'user') {
        return '用户'
      } else if (message.role === 'system') {
        return '系统'
      } else if (message.role === 'assistant') {
        // 根据publisher获取发送者信息
        const publisherId = message.publisher
        if (!publisherId) {
          return '智能体'
        }
        
        // 从研究树获取节点信息
        const currentSnapshot = treeStore.currentSnapshot
        if (!currentSnapshot) {
          return '智能体'
        }
        
        const publisherNode = findNodeById(currentSnapshot.roots || [], publisherId)
        if (!publisherNode) {
          return '智能体'
        }
        
        if (publisherNode.type === 'solution') {
          // 获取父问题节点
          const parentProblem = findParentNode(currentSnapshot.roots || [], publisherId)
          if (parentProblem) {
            return `「${parentProblem.title}」问题的负责专家`
          }
        } else if (publisherNode.type === 'problem') {
          return `「${publisherNode.title}」问题的负责专家`
        }
        
        return '智能体'
      }
      
      return '未知'
    })
    
    // 辅助函数：根据ID查找节点
    const findNodeById = (nodes, nodeId) => {
      for (const node of nodes) {
        if (node.id === nodeId) {
          return node
        }
        if (node.children) {
          const found = findNodeById(node.children, nodeId)
          if (found) return found
        }
      }
      return null
    }
    
    // 辅助函数：查找父节点
    const findParentNode = (nodes, targetId, parent = null) => {
      for (const node of nodes) {
        if (node.id === targetId) {
          return parent
        }
        if (node.children) {
          const found = findParentNode(node.children, targetId, node)
          if (found) return found
        }
      }
      return null
    }
    
    // 格式化时间
    const formatTime = (time) => {
      if (!time) return ''
      return dayjs(time).format('MM-DD HH:mm:ss')
    }
    
    // 处理操作
    const handleAction = async (command) => {
      try {
        switch (command) {
          case 'view-snapshot':
            await handleViewSnapshot()
            break
          case 'copy-content':
            await handleCopyContent()
            break
          case 'rollback':
            await handleRollback()
            break
          case 'stop':
            await handleStopGeneration()
            break
        }
      } catch (error) {
        console.error('处理操作失败:', error)
        ElMessage.error('操作失败')
      }
    }
    
    // 查看快照
    const handleViewSnapshot = async () => {
      if (!props.message.snapshot_id) {
        ElMessage.warning('该消息没有关联的快照')
        return
      }
      
      emit('view-snapshot', props.message.snapshot_id)
      ElMessage.success('正在加载快照...')
    }
    
    // 复制内容
    const handleCopyContent = async () => {
      try {
        const content = [
          props.message.title && `标题: ${props.message.title}`,
          props.message.content && `内容:\n${props.message.content}`,
          props.message.thinking && `思考:\n${props.message.thinking}`
        ].filter(Boolean).join('\n\n')
        
        await navigator.clipboard.writeText(content)
        ElMessage.success('内容已复制到剪贴板')
      } catch (error) {
        console.error('复制失败:', error)
        ElMessage.error('复制失败')
      }
    }
    
    // 回溯消息
    const handleRollback = async () => {
      try {
        await ElMessageBox.confirm(
          `确定要回溯到此消息吗？此操作将删除该消息之后的所有消息，且不可恢复。`,
          '确认回溯',
          {
            confirmButtonText: '确定回溯',
            cancelButtonText: '取消',
            type: 'warning',
            confirmButtonClass: 'el-button--danger'
          }
        )
        
        emit('rollback', props.message.id)
        
      } catch (error) {
        // 用户取消操作
        if (error === 'cancel') {
          return
        }
        throw error
      }
    }
    
    // 停止生成
    const handleStopGeneration = async () => {
      emit('stop-generation')
    }
    
    return {
      titleCollapsed,
      contentCollapsed,
      thinkingCollapsed,
      isGenerating,
      senderName,
      formatTime,
      handleAction
    }
  }
})
</script>

<style scoped>
.message-item {
  margin-bottom: 24px;
  background: var(--bg-color);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.2s ease;
}

/* 用户消息样式 */
.message-user {
  background: linear-gradient(135deg, #409eff 0%, #66b3ff 100%);
  color: white;
  margin-left: 60px;
}

.message-user .message-header {
  background: rgba(255, 255, 255, 0.1);
}

.message-user .sender-avatar {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

/* 智能体消息样式 */
.message-assistant {
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  margin-right: 60px;
}

/* 系统消息样式 */
.message-system {
  background: var(--bg-color-light, #f6f8fa);
  border: 1px dashed var(--border-color);
  margin: 0 30px;
}

/* 生成中的消息样式 */
.generating {
  box-shadow: 0 0 20px rgba(64, 158, 255, 0.3);
  animation: generating-pulse 2s infinite;
}

@keyframes generating-pulse {
  0%, 100% { 
    box-shadow: 0 0 20px rgba(64, 158, 255, 0.3);
  }
  50% { 
    box-shadow: 0 0 30px rgba(64, 158, 255, 0.5);
  }
}

/* 消息头部 */
.message-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: var(--bg-color-light, #f8f9fa);
  border-bottom: 1px solid var(--border-color);
}

.message-sender {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sender-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-color);
  color: white;
  font-size: 18px;
}

.avatar-user {
  background: #409eff;
}

.avatar-assistant {
  background: #67c23a;
}

.avatar-system {
  background: #909399;
}

.sender-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sender-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-color);
}

.message-time {
  font-size: 12px;
  color: var(--text-color);
  opacity: 0.7;
}

.message-status {
  display: flex;
  align-items: center;
}

.message-actions {
  display: flex;
  align-items: center;
}

.action-btn {
  padding: 4px 8px;
  color: var(--text-color);
  opacity: 0.7;
}

.action-btn:hover {
  opacity: 1;
}

/* 消息内容 */
.message-content {
  padding: 0;
}

/* 消息标题 */
.message-title {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 20px;
  cursor: pointer;
  background: var(--bg-color);
  border-bottom: 1px solid var(--border-color);
  transition: background 0.2s;
}

.message-title:hover {
  background: var(--bg-color-light, #f8f9fa);
}

.message-title.collapsed {
  border-bottom: none;
}

.collapse-icon {
  font-size: 14px;
  color: var(--text-color);
  opacity: 0.7;
  transition: transform 0.2s;
}

.title-text {
  font-weight: 600;
  font-size: 16px;
  color: var(--text-color);
}

/* 消息主体 */
.message-body {
  border-bottom: 1px solid var(--border-color);
}

.content-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  cursor: pointer;
  background: var(--bg-color-light, #f8f9fa);
  transition: background 0.2s;
}

.content-header:hover {
  background: var(--bg-color-hover, #e9ecef);
}

.section-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color);
  opacity: 0.8;
}

.content-body {
  padding: 20px;
}

/* 思考过程 */
.message-thinking {
  border-bottom: 1px solid var(--border-color);
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  cursor: pointer;
  background: var(--warning-color-light, #fdf6ec);
  transition: background 0.2s;
}

.thinking-header:hover {
  background: var(--warning-color-lighter, #fcf0d9);
}

.thinking-body {
  padding: 20px;
  background: var(--warning-color-lighter, #fefcf9);
  font-style: italic;
  opacity: 0.9;
}



/* 可见节点 */
.visible-nodes {
  padding: 12px 20px;
  background: var(--success-color-lighter, #f0f9ff);
}

.nodes-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--success-color);
}

/* 响应式设计 */
@media (max-width: 767px) {
  .message-user {
    margin-left: 20px;
  }
  
  .message-assistant {
    margin-right: 20px;
  }
  
  .message-system {
    margin: 0 10px;
  }
  
  .message-header {
    padding: 12px 16px;
  }
  
  .message-title,
  .content-header,
  .thinking-header {
    padding: 12px 16px;
  }
  
  .content-body,
  .thinking-body {
    padding: 16px;
  }
  
  .sender-avatar {
    width: 32px;
    height: 32px;
    font-size: 14px;
  }
  
  .sender-name {
    font-size: 13px;
  }
  
  .message-time {
    font-size: 11px;
  }
}
</style>
