<template>
  <div class="sub-problem-panel-container">
    <!-- 背景遮罩 -->
    <div class="overlay" @click.self="handleClose"></div>
    <!-- 面板主体 -->
    <div class="sub-problem-panel">
      <!-- 头部 -->
      <div class="panel-header">
        <!-- 标题部分 -->
        <div class="header-title">
          <h2 class="title-text">
            {{ currentData.title || '问题详情' }}
          </h2>
        </div>

        <!-- 状态和操作区域 -->
        <div class="header-actions">
          <!-- 问题类型显示 -->
          <div class="status-section">
            <el-tag 
              :type="getProblemTypeTagType(currentData.problem_type)" 
              size="large"
              class="status-tag"
            >
              {{ getProblemTypeText(currentData.problem_type) }}
            </el-tag>
          </div>

          <!-- 操作按钮 -->
          <div class="action-buttons">
            <el-button @click="handleClose">
              关闭
            </el-button>
          </div>
        </div>
      </div>

      <!-- 主内容区域 -->
      <div class="panel-content">
        <!-- 重要性 -->
        <div class="content-column">
          <div class="column-header">重要性</div>
          <div class="column-content">
            <MarkdownRenderer
              :content="currentData.significance || ''"
              class="content-markdown"
            />
          </div>
        </div>

        <!-- 评判标准 -->
        <div class="content-column">
          <div class="column-header">评判标准</div>
          <div class="column-content">
            <MarkdownRenderer
              :content="currentData.criteria || ''"
              class="content-markdown"
            />
          </div>
        </div>
      </div>

    <!-- 消息输入区域 -->
    <div class="message-input-area">
      <el-input
        v-model="messageContent"
        :placeholder="messagePlaceholder"
        @keyup.enter="handleSendMessage"
        :disabled="isSendingMessage || isMessageInputDisabled"
        class="chat-input"
      >
        <template #prepend>
          <span class="message-prefix">{{ messagePrefix }}</span>
        </template>
        <template #append>
          <el-button 
            type="primary" 
            
            circle 
            @click="handleSendMessage"
            :loading="isSendingMessage"
            :disabled="!messageContent.trim() || isMessageInputDisabled"
          >
            <el-icon><ChatSquare /></el-icon>
          </el-button>
        </template>
      </el-input>
    </div>

    </div>
  </div>
</template>

<script>
import { ElButton, ElTag, ElInput, ElMessage } from 'element-plus'
import { ChatSquare } from '@element-plus/icons-vue' // 重新导入 ChatSquare
import MarkdownRenderer from '@/components/message/MarkdownRenderer.vue'
import { useTreeStore } from '@/stores/treeStore'
import { useMessageStore } from '@/stores/messageStore'

export default {
  name: 'SubProblemPanel',

  components: {
    ElButton,
    ElTag,
    ElInput,
    MarkdownRenderer,
    ChatSquare // 在 components 中注册 ChatSquare
  },

  props: {
    // 选中的节点ID（非根问题ID）
    selectedNodeId: {
      type: String,
      default: null
    }
  },

  emits: ['close'],

  data() {
    return {
      treeStore: null,
      messageStore: null,
      messageContent: '',
      isSendingMessage: false,
    }
  },

  computed: {
    // 当前显示的数据
    currentData() {
      return this.treeStore?.getSubProblemPanelData(this.selectedNodeId) || {}
    },

    // 消息输入框占位符
    messagePlaceholder() {
      if (!this.currentData.parentSolutionId) return '无法发送消息'
      return `向${this.treeStore?.getAgentNameByNodeId(this.currentData.parentSolutionId)}发送消息`
    },

    // 消息前缀
    messagePrefix() {
      if (!this.currentData.problemTitle) return ''
      return `对于你方案中的子问题「${this.currentData.problemTitle}」:\n`
    },

    // 是否可以编辑
    canEdit() {
      // 如果正在查看快照，不能编辑
      if (this.treeStore?.getIsViewingSnapshot) {
        return false
      }
      
      // 如果智能体正在操作，不能编辑
      if (this.treeStore?.getAgentOperatingNodeId) {
        return false
      }

      // 弃用节点不能编辑
      if (this.currentData.id && this.treeStore?.getIsNodeEnabled(this.currentData.id) !== true) {
        return false
      }
      
      return true
    },
    // 消息输入是否禁用
    isMessageInputDisabled() {
      // 如果当前节点没有父解决方案ID，或者节点未启用，则禁用消息输入
      return !this.currentData.parentSolutionId || !this.canEdit;
    }
  },

  mounted() {
    this.treeStore = useTreeStore()
    this.messageStore = useMessageStore()
  },

  methods: {
    // 获取问题类型显示文本
    getProblemTypeText(type) {
      const typeMap = {
        implementation: '实施问题',
        conditional: '条件问题'
      }
      return typeMap[type] || '实施问题'
    },

    // 获取问题类型标签类型
    getProblemTypeTagType(type) {
      const typeMap = {
        implementation: 'primary',
        conditional: 'warning'
      }
      return typeMap[type] || 'primary'
    },

    // 关闭面板
    handleClose() {
      this.$emit('close')
    },

    // 发送消息
    async handleSendMessage() {
      if (!this.messageContent.trim() || this.isSendingMessage) {
        ElMessage.warning('请输入消息内容')
        return
      }

      this.isSendingMessage = true // 发送前短暂设置为true，禁用按钮
      try {
        await this.messageStore.sendMessage(
          this.messagePrefix + this.messageContent.trim(),
          "用户消息",
          "user_chat_agent",
          { solution_id: this.currentData.parentSolutionId }
        )
        ElMessage.success('消息发送成功')
        this.handleClose() // 发送前关闭面板
      } catch (error) {
        console.error('发送消息失败:', error)
        ElMessage.error('发送消息失败')
      }
    },
  }
}
</script>

<style scoped>
.sub-problem-panel-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1100; /* 高层级确保在最上层 */
}

/* 背景遮罩 */
.overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5); /* 半透明黑色背景 */
  z-index: 1; /* 确保在面板下方 */
}

/* 面板主体 */
.sub-problem-panel {
  position: relative;
  width: calc(100% - 120px); /* 左右各60px的边距 */
  height: calc(100% - 120px); /* 上下各60px的边距 */
  background: var(--bg-color, #ffffff);
  border: 1px solid var(--border-color, #dcdfe6);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2); /* 增强阴影效果 */
  display: flex;
  flex-direction: column;
  z-index: 2; /* 确保在遮罩上方 */
  max-width: 1000px; /* 子问题面板比根问题面板稍窄 */
  margin: 0 auto; /* 水平居中 */
}

/* 头部 */
.panel-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color, #dcdfe6);
  background: var(--bg-color-light, #f5f7fa);
  border-radius: 12px 12px 0 0;
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: start;
  column-gap: 24px;
  row-gap: 8px;
}

.header-title {
  min-width: 0;
}

.title-text {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--text-color, #303133);
  word-break: break-word;
  overflow-wrap: anywhere;
  max-width: 100%;
}

.header-actions {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.status-section {
  display: flex;
  gap: 12px;
  align-items: center;
}

.status-tag {
  font-weight: 600;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-left: 0;
}

/* 消息输入区域 */
.message-input-area {
  padding: 16px 24px;
  border-top: 1px solid var(--border-color, #dcdfe6);
  background: var(--bg-color-light, #f5f7fa);
  border-radius: 0 0 12px 12px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-input {
  flex: 1;
}

.el-button.is-circle {
  border-radius: 50%;
  padding: 8px; /* Adjust padding for circular button */
}

.message-prefix {
  white-space: pre-wrap; /* Preserve whitespace and allow wrapping */
  color: var(--text-color-secondary, #909399);
  font-size: 14px;
  line-height: 1.5;
}

/* 主内容区域 */
.panel-content {
  flex: 1;
  min-height: 0; /* 允许内容区在父 flex 容器中收缩，给头部让位 */
  display: grid;
  grid-template-columns: 1fr 1fr; /* 两列布局 */
  gap: 1px;
  background: var(--border-color, #dcdfe6);
  overflow: hidden;
}

.content-column {
  background: var(--bg-color, #ffffff);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.column-header {
  padding: 16px 20px;
  background: var(--bg-color-light, #f5f7fa);
  border-bottom: 1px solid var(--border-color, #dcdfe6);
  font-weight: 600;
  font-size: 16px;
  color: var(--text-color, #303133);
  text-align: center;
  flex-shrink: 0;
}

.column-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.content-markdown {
  min-height: 100%;
  padding: 16px;
  border: 1px solid var(--border-color-light, #e4e7ed);
  border-radius: 8px;
  background: var(--bg-color-light, #f5f7fa);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sub-problem-panel {
    width: calc(100% - 40px); /* 左右各20px的边距 */
    height: calc(100% - 40px); /* 上下各20px的边距 */
  }
  
  .panel-header {
    padding: 16px 20px;
  }
  
  .header-actions {
    gap: 16px;
    flex-direction: column;
    align-items: stretch;
  }
  
  .action-buttons {
    margin-left: 0;
  }
  
  .panel-content {
    grid-template-columns: 1fr; /* 单列布局 */
  }
  
  .column-content {
    padding: 16px;
  }
}

/* 深色主题适配 */
:root[data-theme="dark"] .sub-problem-panel {
  background: var(--bg-color-dark, #1d1d1d);
  border-color: var(--border-color-dark, #414243);
}

:root[data-theme="dark"] .panel-header {
  background: var(--bg-color-darker, #2d2d2d);
  border-color: var(--border-color-dark, #414243);
}

:root[data-theme="dark"] .content-column {
  background: var(--bg-color-dark, #1d1d1d);
}

:root[data-theme="dark"] .column-header {
  background: var(--bg-color-darker, #2d2d2d);
  border-color: var(--border-color-dark, #414243);
}

:root[data-theme="dark"] .content-markdown {
  background: var(--bg-color-darker, #2d2d2d);
  border-color: var(--border-color-dark, #414243);
}

:root[data-theme="dark"] .message-input-area {
  background: var(--bg-color-darker, #2d2d2d);
  border-color: var(--border-color-dark, #414243);
}
</style>
