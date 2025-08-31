<template>
  <div class="chat-input">
    <!-- 输入区域 -->
    <div class="input-container">
      <div class="input-header">
        <div class="input-info">
          <el-icon><EditPen /></el-icon>
          <span class="input-label">{{ inputLabel }}</span>
          <el-tag v-if="wordCount > 0" type="info" size="small">
            {{ wordCount }} 字
          </el-tag>
        </div>
        
        <div class="input-actions">
          <el-button 
            v-if="content.trim()" 
            type="text" 
            size="small"
            @click="clearContent"
          >
            <el-icon><Delete /></el-icon>
            清空
          </el-button>
        </div>
      </div>
      
      <div class="input-wrapper">
        <el-input
          ref="textareaRef"
          v-model="content"
          type="textarea"
          :placeholder="placeholder"
          :rows="rows"
          :maxlength="maxLength"
          :disabled="disabled"
          :autosize="autosize"
          resize="vertical"
          class="input-textarea"
          @keydown="handleKeydown"
          @focus="handleFocus"
          @blur="handleBlur"
          @input="handleInput"
        />
        
        <!-- 快速输入建议 -->
        <transition name="slide-up">
          <div v-if="showSuggestions && suggestions.length > 0" class="suggestions">
            <div class="suggestions-header">
              <span class="suggestions-title">快速输入建议</span>
              <el-button type="text" size="small" @click="hideSuggestions">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
            <div class="suggestions-list">
              <div
                v-for="(suggestion, index) in suggestions"
                :key="index"
                class="suggestion-item"
                @click="applySuggestion(suggestion)"
              >
                <el-icon><ChatDotRound /></el-icon>
                <span>{{ suggestion.text }}</span>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </div>
    
    <!-- 操作按钮区域 -->
    <div class="action-container">
      <div class="action-left">
        <!-- 附加功能按钮 -->
        <el-button 
          type="text" 
          size="small"
          @click="toggleSuggestions"
          :class="{ 'active': showSuggestions }"
        >
          <el-icon><StarFilled /></el-icon>
          建议
        </el-button>
        
        <el-button 
          type="text" 
          size="small"
          @click="showHistory"
        >
          <el-icon><Clock /></el-icon>
          历史
        </el-button>
      </div>
      
      <div class="action-right">
        <!-- 发送按钮 -->
        <el-button
          type="primary"
          size="large"
          :disabled="!canSend"
          :loading="isLoading"
          @click="handleSend"
          class="send-button"
        >
          <el-icon v-if="!isLoading"><Promotion /></el-icon>
          {{ sendButtonText }}
        </el-button>
      </div>
    </div>
    
    <!-- 输入提示 -->
    <div v-if="inputTip" class="input-tip">
      <el-icon><InfoFilled /></el-icon>
      <span>{{ inputTip }}</span>
    </div>
    
    <!-- 字数限制警告 -->
    <transition name="fade">
      <div v-if="isNearMaxLength" class="length-warning">
        <el-icon><WarningFilled /></el-icon>
        <span>
          还可输入 {{ maxLength - wordCount }} 字
          <span v-if="wordCount >= maxLength" class="exceeded">（已超出限制）</span>
        </span>
      </div>
    </transition>
  </div>
</template>

<script>
import { defineComponent, ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  EditPen, Delete, Close, StarFilled, Clock, Promotion,
  ChatDotRound, InfoFilled, WarningFilled 
} from '@element-plus/icons-vue'

export default defineComponent({
  name: 'ChatInput',
  
  components: {
    EditPen, Delete, Close, StarFilled, Clock, Promotion,
    ChatDotRound, InfoFilled, WarningFilled
  },
  
  props: {
    // 输入内容
    modelValue: {
      type: String,
      default: ''
    },
    
    // 标题
    title: {
      type: String,
      default: ''
    },
    
    // 占位符
    placeholder: {
      type: String,
      default: '请输入您的要求或问题...'
    },
    
    // 是否禁用
    disabled: {
      type: Boolean,
      default: false
    },
    
    // 是否加载中
    isLoading: {
      type: Boolean,
      default: false
    },
    
    // 智能体类型
    agentType: {
      type: String,
      default: ''
    },
    
    // 选中的节点信息
    selectedNode: {
      type: Object,
      default: null
    },
    
    // 最大长度
    maxLength: {
      type: Number,
      default: 2000
    },
    
    // 最小行数
    minRows: {
      type: Number,
      default: 3
    },
    
    // 最大行数
    maxRows: {
      type: Number,
      default: 8
    }
  },
  
  emits: ['update:modelValue', 'send', 'title-change'],
  
  setup(props, { emit }) {
    const textareaRef = ref(null)
    const content = ref(props.modelValue)
    const localTitle = ref(props.title)
    const showSuggestions = ref(false)
    const isFocused = ref(false)
    
    // 计算属性
    const wordCount = computed(() => content.value.length)
    
    const isNearMaxLength = computed(() => {
      return wordCount.value > props.maxLength * 0.8
    })
    
    const canSend = computed(() => {
      return content.value.trim().length > 0 && 
             wordCount.value <= props.maxLength && 
             !props.disabled && 
             !props.isLoading
    })
    
    const rows = computed(() => {
      if (content.value.length === 0) return props.minRows
      const lines = content.value.split('\n').length
      return Math.min(Math.max(lines, props.minRows), props.maxRows)
    })
    
    const autosize = computed(() => ({
      minRows: props.minRows,
      maxRows: props.maxRows
    }))
    
    const inputLabel = computed(() => {
      if (props.agentType === 'auto_research_agent') {
        return '研究要求'
      } else if (props.agentType === 'user_chat_agent') {
        return '对话内容'
      }
      return '输入内容'
    })
    
    const sendButtonText = computed(() => {
      if (props.isLoading) {
        return '发送中...'
      }
      return '发送'
    })
    
    const inputTip = computed(() => {
      if (!props.agentType) {
        return '请先选择智能体类型'
      }
      
      if (!props.selectedNode) {
        return `请先选择${props.agentType === 'auto_research_agent' ? '问题' : '解决方案'}节点`
      }
      
      if (props.agentType === 'auto_research_agent') {
        return '描述您希望智能体如何解决这个问题，包括约束条件、技术要求等'
      } else if (props.agentType === 'user_chat_agent') {
        return '向解决方案提问或请求详细说明、优化建议等'
      }
      
      return ''
    })
    
    // 建议列表
    const suggestions = computed(() => {
      if (!props.agentType) return []
      
      if (props.agentType === 'auto_research_agent') {
        return [
          { text: '请提供一个完整的技术解决方案' },
          { text: '请考虑成本效益和可行性' },
          { text: '请详细说明实施步骤和时间安排' },
          { text: '请分析可能的风险和应对策略' },
          { text: '请提供多个备选方案进行比较' }
        ]
      } else if (props.agentType === 'user_chat_agent') {
        return [
          { text: '这个方案的核心原理是什么？' },
          { text: '实施过程中可能遇到哪些挑战？' },
          { text: '有没有更简单的替代方案？' },
          { text: '这个方案的成本大概是多少？' },
          { text: '如何评估方案的实施效果？' }
        ]
      }
      
      return []
    })
    
    // 方法
    const handleInput = (value) => {
      content.value = value
      emit('update:modelValue', value)
    }
    
    const handleFocus = () => {
      isFocused.value = true
    }
    
    const handleBlur = () => {
      isFocused.value = false
    }
    
    const handleKeydown = (event) => {
      // Ctrl+Enter 或 Cmd+Enter 发送
      if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault()
        if (canSend.value) {
          handleSend()
        }
      }
      
      // Tab 键插入缩进
      if (event.key === 'Tab') {
        event.preventDefault()
        const textarea = event.target
        const start = textarea.selectionStart
        const end = textarea.selectionEnd
        
        const before = content.value.substring(0, start)
        const after = content.value.substring(end)
        const indent = '  ' // 两个空格
        
        content.value = before + indent + after
        emit('update:modelValue', content.value)
        
        nextTick(() => {
          textarea.selectionStart = textarea.selectionEnd = start + indent.length
        })
      }
    }
    
    const handleSend = () => {
      if (!canSend.value) return
      
      const trimmedContent = content.value.trim()
      if (!trimmedContent) {
        ElMessage.warning('请输入内容')
        return
      }
      
      // 生成标题（如果没有设置）
      let messageTitle = localTitle.value.trim()
      if (!messageTitle) {
        if (props.agentType === 'auto_research_agent') {
          messageTitle = '自动生成解决方案'
        } else if (props.agentType === 'user_chat_agent') {
          messageTitle = '对话交流'
        } else {
          messageTitle = '用户消息'
        }
      }
      
      emit('send', {
        content: trimmedContent,
        title: messageTitle,
        agentType: props.agentType,
        selectedNode: props.selectedNode
      })
      
      // 清空内容
      clearContent()
    }
    
    const clearContent = () => {
      content.value = ''
      localTitle.value = ''
      emit('update:modelValue', '')
      emit('title-change', '')
      
      // 聚焦到输入框
      nextTick(() => {
        if (textareaRef.value) {
          textareaRef.value.focus()
        }
      })
    }
    
    const toggleSuggestions = () => {
      showSuggestions.value = !showSuggestions.value
    }
    
    const hideSuggestions = () => {
      showSuggestions.value = false
    }
    
    const applySuggestion = (suggestion) => {
      const currentContent = content.value.trim()
      const newContent = currentContent 
        ? `${currentContent}\n\n${suggestion.text}` 
        : suggestion.text
      
      content.value = newContent
      emit('update:modelValue', newContent)
      
      hideSuggestions()
      
      // 聚焦并移动光标到末尾
      nextTick(() => {
        if (textareaRef.value) {
          const textarea = textareaRef.value.textarea || textareaRef.value.$refs.textarea
          textarea.focus()
          textarea.setSelectionRange(newContent.length, newContent.length)
        }
      })
    }
    
    const showHistory = () => {
      // 这里可以实现显示历史输入的功能
      console.log('显示历史输入')
      ElMessage.info('历史输入功能待实现')
    }
    
    // 监听外部变化
    const stopWatchingModelValue = () => {
      // Vue 3 的watch会自动清理
    }
    
    onMounted(() => {
      // 组件挂载后聚焦
      nextTick(() => {
        if (textareaRef.value && !props.disabled) {
          textareaRef.value.focus()
        }
      })
    })
    
    onBeforeUnmount(() => {
      stopWatchingModelValue()
    })
    
    return {
      textareaRef,
      content,
      showSuggestions,
      isFocused,
      wordCount,
      isNearMaxLength,
      canSend,
      rows,
      autosize,
      inputLabel,
      sendButtonText,
      inputTip,
      suggestions,
      handleInput,
      handleFocus,
      handleBlur,
      handleKeydown,
      handleSend,
      clearContent,
      toggleSuggestions,
      hideSuggestions,
      applySuggestion,
      showHistory
    }
  }
})
</script>

<style scoped>
.chat-input {
  background: var(--bg-color);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  overflow: hidden;
}

/* 输入容器 */
.input-container {
  position: relative;
}

.input-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--bg-color-light, #f8f9fa);
  border-bottom: 1px solid var(--border-color);
}

.input-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color);
}

.input-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-wrapper {
  position: relative;
  padding: 16px;
}

.input-textarea {
  border: none;
  box-shadow: none;
}

.input-textarea :deep(.el-textarea__inner) {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px;
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
  transition: border-color 0.3s;
}

.input-textarea :deep(.el-textarea__inner):focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
}

/* 建议面板 */
.suggestions {
  position: absolute;
  top: 100%;
  left: 16px;
  right: 16px;
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 100;
  max-height: 200px;
  overflow-y: auto;
}

.suggestions-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--bg-color-light, #f8f9fa);
  border-bottom: 1px solid var(--border-color);
}

.suggestions-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-color);
  opacity: 0.8;
}

.suggestions-list {
  padding: 4px;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.2s;
  font-size: 13px;
  color: var(--text-color);
}

.suggestion-item:hover {
  background: var(--bg-color-light, #f8f9fa);
}

.suggestion-item:active {
  background: var(--primary-color-light, #ecf5ff);
}

/* 操作容器 */
.action-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--bg-color-light, #f8f9fa);
  border-top: 1px solid var(--border-color);
}

.action-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-left .el-button.active {
  color: var(--primary-color);
  background: var(--primary-color-light, #ecf5ff);
}

.action-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.send-button {
  min-width: 80px;
  font-weight: 500;
}

/* 输入提示 */
.input-tip {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 8px 16px;
  background: var(--info-color-lighter, #f4f9ff);
  border-top: 1px solid var(--border-color);
  font-size: 12px;
  color: var(--info-color);
  line-height: 1.4;
}

/* 字数限制警告 */
.length-warning {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--warning-color-lighter, #fdf6ec);
  border-top: 1px solid var(--border-color);
  font-size: 12px;
  color: var(--warning-color);
}

.exceeded {
  color: var(--danger-color);
  font-weight: 500;
}

/* 动画效果 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式设计 */
@media (max-width: 767px) {
  .input-header {
    padding: 10px 12px;
  }
  
  .input-wrapper {
    padding: 12px;
  }
  
  .action-container {
    padding: 10px 12px;
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .action-left,
  .action-right {
    gap: 6px;
  }
  
  .send-button {
    min-width: 70px;
  }
  
  .suggestions {
    left: 12px;
    right: 12px;
  }
  
  .input-tip,
  .length-warning {
    padding: 6px 12px;
    font-size: 11px;
  }
}

/* 暗色主题适配 */
.dark-theme .suggestions {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.dark-theme .input-textarea :deep(.el-textarea__inner):focus {
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}
</style>
