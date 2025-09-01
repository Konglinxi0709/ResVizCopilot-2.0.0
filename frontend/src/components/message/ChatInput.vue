<template>
  <div class="chat-input">
    <!-- 简化的输入区域 -->
    <div class="input-container">
      <div class="input-wrapper">
        <el-input
          ref="textareaRef"
          v-model="content"
          type="textarea"
          :placeholder="placeholder"
          :rows="3"
          :maxlength="maxLength"
          :disabled="disabled"
          resize="vertical"
          class="input-textarea"
          @keydown="handleKeydown"
          @input="handleInput"
        />
        
        <!-- 发送按钮 -->
        <el-button
          type="primary"
          size="default"
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
  </div>
</template>

<script>
import { defineComponent, ref, computed, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Promotion } from '@element-plus/icons-vue'

export default defineComponent({
  name: 'ChatInput',
  
  components: {
    Promotion
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
    
    // 计算属性
    const wordCount = computed(() => content.value.length)
    
    const canSend = computed(() => {
      return content.value.trim().length > 0 && 
             wordCount.value <= props.maxLength && 
             !props.disabled && 
             !props.isLoading
    })
    
    const sendButtonText = computed(() => {
      if (props.isLoading) {
        return '发送中...'
      }
      return '发送'
    })
    
    // 方法
    const handleInput = (value) => {
      content.value = value
      emit('update:modelValue', value)
    }
    
    const handleKeydown = (event) => {
      // Ctrl+Enter 或 Cmd+Enter 发送
      if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault()
        if (canSend.value) {
          handleSend()
        }
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
      content.value = ''
      emit('update:modelValue', '')
    }
    

    
    onMounted(() => {
      // 组件挂载后聚焦
      nextTick(() => {
        if (textareaRef.value && !props.disabled) {
          textareaRef.value.focus()
        }
      })
    })
    
    return {
      textareaRef,
      content,
      wordCount,
      canSend,
      sendButtonText,
      handleInput,
      handleKeydown,
      handleSend
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

.input-wrapper {
  position: relative;
  padding: 12px 16px;
  display: flex;
  align-items: flex-end;
  gap: 12px;
}

.input-textarea {
  flex: 1;
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

.send-button {
  flex-shrink: 0;
  height: 32px;
  padding: 0 16px;
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
