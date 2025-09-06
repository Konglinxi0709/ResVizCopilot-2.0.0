<template>
  <div class="message-item" :class="[`message-${message.role}`, { 'generating': isGenerating }]">
    <!-- 消息头部 -->
    <div class="message-header">
      <div class="message-sender">
        <!-- 发送者信息（移除头像） -->
        <div class="sender-info">
          <div class="sender-name">{{ senderName }}</div>
          <div class="message-time">{{ formattedTime }}</div>
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
                v-if="hasSnapshot" 
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
        v-if="message.title || isGenerating" 
        class="message-title" 
        :class="{ 'collapsed': titleCollapsed }"
        @click="toggleTitleCollapse"
      >
        <el-icon class="collapse-icon">
          <ArrowDown v-if="titleCollapsed" />
          <ArrowUp v-else />
        </el-icon>
        <span class="title-text">
          {{ message.title || (isGenerating ? '正在生成标题...' : '') }}
        </span>
      </div>
      
      <!-- 思考过程 -->
      <div 
        v-if="(message.thinking || isGenerating) && !titleCollapsed" 
        class="message-thinking"
        :class="{ 'collapsed': thinkingCollapsed }"
      >
        <div class="thinking-header" @click="toggleThinkingCollapse">
          <el-icon class="collapse-icon">
            <ArrowDown v-if="thinkingCollapsed" />
            <ArrowUp v-else />
          </el-icon>
          <span class="section-title">思考过程</span>
        </div>
        
        <div v-if="!thinkingCollapsed" class="thinking-body">
          <MarkdownRenderer 
            :content="message.thinking || (isGenerating ? '正在生成思考过程...' : '')" 
          />
        </div>
      </div>
      
      <!-- 消息主体内容 -->
      <div 
        v-if="(message.content || isGenerating) && !titleCollapsed" 
        class="content-body"
      >
        <MarkdownRenderer 
          :content="message.content || (isGenerating ? '正在生成内容...' : '')" 
        />
      </div>
      
      
      

      
      <!-- 可见节点信息 -->
      <div 
        v-if="hasVisibleNodes && !titleCollapsed" 
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
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  More,
  ArrowDown, ArrowUp,
  View
} from '@element-plus/icons-vue'
import MarkdownRenderer from './MarkdownRenderer.vue'
import dayjs from 'dayjs'

export default {
  name: 'MessageItem',
  
  components: {
    MarkdownRenderer,
    More,
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
  
  data() {
    return {
      titleCollapsed: true, // 标题默认折叠（整体关闭）
      contentCollapsed: false,
      thinkingCollapsed: true // 思考过程默认折叠
    }
  },
  
  computed: {
    isGenerating() {
      return this.message.status === 'generating'
    },
    
    senderName() {
      // 直接使用消息对象的agentName属性
      return this.message.agentName || '未知'
    },
    
    // 消息类型样式
    messageTypeClass() {
      switch (this.message.role) {
        case 'user': return 'message-user'
        case 'assistant': return 'message-assistant'
        case 'system': return 'message-system'
        default: return 'message-default'
      }
    },
    
    // 发送者头像
    senderAvatar() {
      switch (this.message.role) {
        case 'user': return 'UserFilled'
        case 'assistant': return 'InfoFilled'
        case 'system': return 'InfoFilled'
        default: return 'User'
      }
    },
    
    // 格式化时间
    formattedTime() {
      if (!this.message.created_at) return ''
      return dayjs(this.message.created_at).format('MM-DD HH:mm:ss')
    },
    
    // 是否有快照
    hasSnapshot() {
      return !!this.message.snapshot_id
    },
    
    // 是否有可见节点
    hasVisibleNodes() {
      return this.message.visible_node_ids && this.message.visible_node_ids.length > 0
    }
  },
  
  methods: {
    
    // 切换标题折叠状态
    toggleTitleCollapse() {
      this.titleCollapsed = !this.titleCollapsed
    },
    
    // 切换内容折叠状态
    toggleContentCollapse() {
      this.contentCollapsed = !this.contentCollapsed
    },
    
    // 切换思考过程折叠状态
    toggleThinkingCollapse() {
      this.thinkingCollapsed = !this.thinkingCollapsed
    },
    
    // 处理操作
    async handleAction(command) {
      try {
        switch (command) {
          case 'view-snapshot':
            await this.handleViewSnapshot()
            break
          case 'copy-content':
            await this.handleCopyContent()
            break
          case 'rollback':
            await this.handleRollback()
            break
          case 'stop':
            this.handleStopGeneration()
            break
        }
      } catch (error) {
        console.error('处理操作失败:', error)
        ElMessage.error('操作失败')
      }
    },
    
    // 查看快照
    async handleViewSnapshot() {
      if (!this.hasSnapshot) {
        ElMessage.warning('该消息没有关联的快照')
        return
      }
      
      this.$emit('view-snapshot', this.message.snapshot_id)
      ElMessage.success('正在加载快照...')
    },
    
    // 复制内容
    async handleCopyContent() {
      try {
        const content = this.message.content || ''
        await navigator.clipboard.writeText(content)
        ElMessage.success('内容已复制到剪贴板')
      } catch (error) {
        console.error('复制失败:', error)
        ElMessage.error('复制失败')
      }
    },
    
    // 回退到此消息
    async handleRollback() {
      try {
        await ElMessageBox.confirm(
          '确定要回退到此消息吗？此操作将删除该消息之后的所有消息。',
          '确认回退',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        this.$emit('rollback', this.message.id)
      } catch (error) {
        if (error !== 'cancel') {
          console.error('回退操作失败:', error)
          ElMessage.error('回退操作失败')
        }
      }
    },
    
    // 停止生成
    handleStopGeneration() {
      this.$emit('stop-generation')
    }
  }
}
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
