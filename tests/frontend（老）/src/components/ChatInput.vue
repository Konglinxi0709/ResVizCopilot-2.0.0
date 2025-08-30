<template>
  <div class="input-container">
    <el-mention
      v-model="inputMessage"
      type="textarea"
      :options="options"
      :prefix="['@', '#']"
      whole
      :check-is-whole="checkIsWhole"
      class="chat-input"
      :autosize="{ minRows: 3, maxRows: 6 }"
      :placeholder="$t('chatInput.placeholder')"
      @search="handleSearch"
      @keydown="handleKeydown"
    />
    <el-button class="send-button" @click="send">
      <img src="@/assets/upload.png" :alt="$t('chatInput.uploadIcon')" class="upload-icon">
    </el-button>
  </div>
</template>

<script>
import { ElMention, ElButton } from 'element-plus'

export default {
  components: {
    ElMention,
    ElButton
  },
  data() {
    return {
      inputMessage: '',
      MOCK_DATA: {
        '@': ['1_Fuphoenixes', '2_kooriookami', '3_Jeremy', 'btea'],
        '#': ['1.0', '2.0', '3.0']
      },
      options: []
    }
  },
  methods: {
    send() {
      if (this.inputMessage.trim()) {
        this.$emit('send', this.inputMessage)
        this.inputMessage = ''
      }
    },
    handleKeydown(event) {
      if (event.key === 'Enter' && !event.shiftKey) {
        this.send()
        event.preventDefault()
      } else if (event.key === 'Enter' && event.shiftKey) {
        // 允许 Shift+Enter 换行
        this.inputMessage += '\n'
      }
    },
    handleSearch(query, prefix) {
      this.options = (this.MOCK_DATA[prefix] || []).map(value => ({ value }))
    },
    checkIsWhole(pattern, prefix) {
      return (this.MOCK_DATA[prefix] || []).includes(pattern)
    }
  }
}
</script>

<style scoped>
.input-container {
  display: flex;
  align-items: flex-end;
  padding: 10px;
  background-color: #fff;
}

.chat-input {
  flex: 1;
}

/* 关键修改3：多行样式适配 */
:deep(.el-mention) {
  /* 确保使用文本域布局 */
  display: block !important;
  
  .el-textarea {
    /* 继承原有文本域样式 */
    .el-textarea__inner {
      min-height: 60px !important;
      resize: vertical;
      line-height: 1.5;
      padding: 8px 15px;
      white-space: pre-wrap;  /* 允许自动换行 */
    }
  }

  /* 调整建议框位置 */
  .el-mention__suggestions {
    position: absolute;
    z-index: 2000;
    margin-top: 5px;
  }
}


.send-button {
  margin-left: 10px;
  margin-bottom: 5px;
  background-color: transparent;
  padding: 0;
  display: flex;
  height: 30px;
  border: none;
  box-shadow: none;
}

.send-button:focus {
  outline: none;
}

.upload-icon {
  width: 30px;
  height: 30px;
}

/* 保持文本域高度自适应 */
:deep(.el-textarea) {
  .el-textarea__inner {
    min-height: 60px !important;
    resize: vertical;
  }
}
</style>