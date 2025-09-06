<template>
  <div class="message-list">
    <!-- 消息列表容器 -->
    <div 
      ref="messageContainer" 
      class="message-container"
      @scroll="handleScroll"
    >
      <!-- 加载状态 -->
      <div v-if="isLoading && messages.length === 0" class="loading-state">
        <el-skeleton :rows="3" animated />
        <div class="loading-text">正在加载消息...</div>
      </div>
      
      <!-- 空状态 -->
      <div v-else-if="messages.length === 0" class="empty-state">
        <el-icon size="64" color="#C0C4CC"><ChatDotRound /></el-icon>
        <h3>暂无消息</h3>
        <p>开始与智能体对话吧</p>
      </div>
      
      <!-- 消息列表 -->
      <div v-else class="messages-wrapper">
        <MessageItem
          v-for="message in messages"
          :key="message.id"
          :message="message"
          @view-snapshot="handleViewSnapshot"
          @rollback="handleRollback"
          @stop-generation="handleStopGeneration"
        />
      </div>
      
      <!-- 滚动到底部按钮 -->
      <transition name="fade">
        <div 
          v-if="showScrollToBottom" 
          class="scroll-to-bottom"
          @click="scrollToBottom"
        >
          <el-button type="primary" circle>
            <el-icon><ArrowDown /></el-icon>
          </el-button>
          <span v-if="unreadCount > 0" class="unread-badge">{{ unreadCount }}</span>
        </div>
      </transition>
    </div>
    
    <!-- 生成状态指示器 -->
    <transition name="slide-up">
      <div v-if="isGenerating" class="generating-indicator">
        <div class="indicator-content">
          <el-icon class="loading-icon"><Loading /></el-icon>
          <span class="indicator-text">{{ currentAgentName || '智能体' }} 正在思考和回复...</span>
          <el-button 
            type="danger" 
            size="small" 
            @click="handleStopGeneration"
            :loading="stoppingGeneration"
          >
            <el-icon><VideoPause /></el-icon>
            停止生成
          </el-button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import {
  ChatDotRound, ArrowDown, Loading, VideoPause
} from '@element-plus/icons-vue'
import MessageItem from './MessageItem.vue'

export default {
  name: 'MessageList',
  
  components: {
    MessageItem,
    ChatDotRound, ArrowDown, Loading, VideoPause
    // RecycleScroller // 需要安装 vue-virtual-scroller
  },
  
  props: {
    // 消息列表数据
    messages: {
      type: Array,
      default: () => []
    },

    // 加载状态
    isLoading: {
      type: Boolean,
      default: false
    },

    // 生成状态
    isGenerating: {
      type: Boolean,
      default: false
    },

    // 当前智能体名称
    currentAgentName: {
      type: String,
      default: ''
    },

    // 是否启用虚拟滚动
    enableVirtualScroll: {
      type: Boolean,
      default: false
    },

    // 虚拟滚动阈值
    virtualScrollThreshold: {
      type: Number,
      default: 50
    },

    // 预估项目高度
    estimatedItemSize: {
      type: Number,
      default: 200
    },

    // 是否自动滚动到底部
    autoScrollToBottom: {
      type: Boolean,
      default: true
    }
  },
  
  emits: ['view-snapshot', 'rollback', 'stop-generation'],
  
  data() {
    return {
      messageContainer: null,
      showScrollToBottom: false,
      unreadCount: 0,
      stoppingGeneration: false,
      lastScrollTop: 0,
      userScrolledUp: false
    }
  },
  
  watch: {
    // 监听消息变化，自动滚动/未读计数
    messages(newArr, oldArr) {
      const newLength = (newArr || []).length
      const oldLength = (oldArr || []).length
      if (newLength > oldLength) {
        if (this.autoScrollToBottom && !this.userScrolledUp) {
          this.$nextTick(() => {
            this.scrollToBottom()
          })
        } else if (this.userScrolledUp) {
          this.unreadCount += (newLength - oldLength)
        }
      }
    },

    // 监听生成状态变化
    isGenerating(newVal) {
      if (!newVal) {
        // 生成结束时，自动滚动到底部
        if (this.autoScrollToBottom) {
          this.$nextTick(() => {
            this.scrollToBottom()
          })
        }
      }
    }
  },
  
  async mounted() {
    // 初始滚动到底部
    await this.$nextTick()
    this.scrollToBottom()
    
    // 绑定快捷键
    document.addEventListener('keydown', this.handleKeydown)
  },
  
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleKeydown)
  },
  
  methods: {
    handleScroll() {
      if (!this.messageContainer) return
      const { scrollTop, scrollHeight, clientHeight } = this.messageContainer
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - 50
      this.showScrollToBottom = !isAtBottom
      this.userScrolledUp = scrollTop < this.lastScrollTop
      this.lastScrollTop = scrollTop
      if (isAtBottom) {
        this.unreadCount = 0
      }
    },
    
    async scrollToBottom() {
      await this.$nextTick()
      if (this.messageContainer) {
        this.messageContainer.scrollTo({
          top: this.messageContainer.scrollHeight,
          behavior: 'smooth'
        })
      }
      this.unreadCount = 0
    },
    
    async handleViewSnapshot(snapshotId) {
      this.$emit('view-snapshot', snapshotId)
    },

    async handleRollback(messageId) {
      this.$emit('rollback', messageId)
    },

    async handleStopGeneration() {
      try {
        this.stoppingGeneration = true
        this.$emit('stop-generation')
      } finally {
        this.stoppingGeneration = false
      }
    },
    
    handleKeydown(event) {
      if (event.key === 'End' && event.ctrlKey) {
        this.scrollToBottom()
        event.preventDefault()
      } else if (event.key === 'Home' && event.ctrlKey) {
        if (this.messageContainer) {
          this.messageContainer.scrollTo({ top: 0, behavior: 'smooth' })
        }
        event.preventDefault()
      }
    }
  }
}
</script>

<style scoped>
.message-list {
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
}

.message-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  scroll-behavior: smooth;
}

/* 自定义滚动条 */
.message-container::-webkit-scrollbar {
  width: 6px;
}

.message-container::-webkit-scrollbar-track {
  background: var(--bg-color-light, #f5f5f5);
  border-radius: 3px;
}

.message-container::-webkit-scrollbar-thumb {
  background: var(--border-color, #dcdfe6);
  border-radius: 3px;
}

.message-container::-webkit-scrollbar-thumb:hover {
  background: var(--text-color-placeholder, #c0c4cc);
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  gap: 16px;
}

.loading-text {
  color: var(--text-color);
  opacity: 0.7;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: var(--text-color);
  opacity: 0.7;
}

.empty-state h3 {
  margin: 16px 0 8px 0;
  font-size: 18px;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

/* 消息包装器 */
.messages-wrapper {
  min-height: 100%;
  display: flex;
  flex-direction: column;
}

/* 虚拟滚动器 */
.virtual-scroller {
  height: 100%;
}

/* 滚动到底部按钮 */
.scroll-to-bottom {
  position: fixed;
  bottom: 120px;
  right: 30px;
  z-index: 100;
  cursor: pointer;
}

.scroll-to-bottom .el-button {
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.unread-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  background: var(--danger-color);
  color: white;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
}

/* 生成状态指示器 */
.generating-indicator {
  position: fixed;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  background: var(--warning-color);
  color: white;
  padding: 12px 20px;
  border-radius: 25px;
  box-shadow: 0 4px 12px rgba(230, 162, 60, 0.3);
}

.indicator-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.indicator-text {
  font-size: 14px;
  font-weight: 500;
}

/* 动画效果 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateX(-50%) translateY(20px);
  opacity: 0;
}

/* 响应式设计 */
@media (max-width: 767px) {
  .message-container {
    padding: 12px;
  }
  
  .scroll-to-bottom {
    bottom: 100px;
    right: 20px;
  }
  
  .generating-indicator {
    bottom: 60px;
    left: 20px;
    right: 20px;
    transform: none;
    border-radius: 12px;
  }
  
  .indicator-content {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .indicator-text {
    font-size: 13px;
  }
}

/* 无障碍支持 */
@media (prefers-reduced-motion: reduce) {
  .message-container {
    scroll-behavior: auto;
  }
  
  .loading-icon {
    animation: none;
  }
  
  .generating-indicator {
    animation: none;
  }
}
</style>
