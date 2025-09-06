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
import { ElMessage } from 'element-plus'
import { Promotion } from '@element-plus/icons-vue'

export default {
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
  
  data() {
    return {
      textareaRef: null,
      content: this.modelValue,
    }
  },
  
  computed: {
    wordCount() {
      return this.content.length
    },
    
    canSend() {
      return this.content.trim().length > 0 && 
             this.wordCount <= this.maxLength && 
             !this.disabled && 
             !this.isLoading
    },
    
    sendButtonText() {
      if (this.isLoading) {
        return '发送中...'
      }
      return '发送'
    }
  },
  
  watch: {
    modelValue(newValue) {
      this.content = newValue
    },
  },
  
  mounted() {
    // 自动聚焦输入框
    this.$nextTick(() => {
      if (this.textareaRef) {
        this.textareaRef.focus()
      }
    })
  },
  
  methods: {
    handleInput(value) {
      this.content = value
      this.$emit('update:modelValue', value)
    },
    
    handleKeydown(event) {
      // Ctrl+Enter 或 Cmd+Enter 发送
      if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault()
        if (this.canSend) {
          this.handleSend()
        }
      }
    },
    
    handleSend() {
      if (!this.canSend) {
        ElMessage.warning('请输入有效内容')
        return
      }
      
      // 发送消息
      this.$emit('send', this.content.trim())
      
      // 清空输入
      this.content = ''
      this.$emit('update:modelValue', '')
    },
  }
}
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
