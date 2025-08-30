<template>
  <div class="chat-box">
    <InitialContent
      v-if="messages.length === 0"
      :preset-questions="presetQuestions"
      @question-click="askPresetQuestion"
    />
    
    <div class="chat-content" ref="chatContent">
      <ChatMessage
        v-for="(message, index) in messages"
        :key="index"
        :message="message"
      />
    </div>

    <RecommendedQuestions
      :questions="recommendedQuestions"
      @question-click="setMessageAndFocus"
    />
    <div class="mode-container">
      <div class="mode-selector">
        <el-select 
          v-model="currentMode" 
          size="small" 
          :placeholder="$t('chatBox.selectMode')"
          style="width: 100%"
        >
          <template #prefix>
            <el-icon class="selected-icon">
              <component :is="workModes.find(m => m.value === currentMode)?.icon" />
            </el-icon>
          </template>
          <el-option
            v-for="item in workModes"
            :key="item.value"
            :label="item.label"
            :value="item.value"
            :disabled="item.value === 'exploration' && !currentFocusProblem"
          >
            <template #default>
              <el-icon v-if="item.value === 'newProblem'"><CirclePlusFilled /></el-icon>
              <el-icon v-else-if="item.value === 'exploration'"><Guide /></el-icon>
              <el-icon v-else><ChatRound /></el-icon>
              {{ item.label }}
            </template>
          </el-option>
        </el-select>
      </div>
      <div
        v-if="currentMode !== 'chat'"
        class="more-settings-container"
      >
        <div v-if="currentMode === 'exploration'">
          {{ $t('chatBox.currentProblem') }}: {{ focusProblemName.slice(0, 10) }}{{ focusProblemName.length > 10 ? '...' : '' }}
        </div>
        <div v-if="currentMode !== 'chat'">
          <el-switch
            v-model="autoCreateCategory"
            :active-text="$t('chatBox.autoCreateCategory')"
          />
        </div>
      </div>
    </div> 
    <ChatInput @send="sendMessage" />
  </div>
</template>

<script>
import InitialContent from '@/components/InitialContent.vue'
import ChatMessage from '@/components/ChatMessage.vue'
import RecommendedQuestions from '@/components/RecommendedQuestions.vue'
import ChatInput from '@/components/ChatInput.vue'
import axios from 'axios'
import { CirclePlusFilled, Guide, ChatRound } from '@element-plus/icons-vue'

export default {
  components: {
    InitialContent,
    ChatMessage,
    RecommendedQuestions,
    ChatInput,
    CirclePlusFilled,
    Guide,
    ChatRound
  },
  props: {
    currentFocusProblem: {
      type: String,
      default: null
    },
  },
  data() {
    return {
      presetQuestions: [
        this.$t('chatBox.presetQuestions.question1'),
        this.$t('chatBox.presetQuestions.question2'),
        this.$t('chatBox.presetQuestions.question3'),
        this.$t('chatBox.presetQuestions.question4')
      ],
      messages: [],
      recommendedQuestions: [],
      currentMode: 'newProblem',
      workModes: [
        { value: 'newProblem', label: this.$t('chatBox.modes.newProblem'), icon: CirclePlusFilled },
        { value: 'exploration', label: this.$t('chatBox.modes.exploration'), icon: Guide },
        { value: 'chat', label: this.$t('chatBox.modes.chat'), icon: ChatRound }
      ],
      focusProblemName: '',
      autoCreateCategory: false
    }
  },
  watch: {
    currentFocusProblem: {
      immediate: true,
      handler(newId) {
        if (newId) {
          this.fetchProblemInfo(newId);
        } else {
          this.focusProblemName = '';
          // 如果没有聚焦问题，自动切换到新问题模式或普通聊天模式
          if (this.currentMode === 'exploration') {
            this.currentMode = 'newProblem';
          }
        }
      }
    }
  },
  async created() {
    await this.fetchHistory()
  },
  methods: {
    async fetchProblemInfo(problemId) {
      if (!problemId) return;
      
      try {
        const res = await axios.get(`/api/research/problem/${problemId}`)
        if (res.data && res.data.success) {
          this.focusProblemName = res.data.problem.viewName || '';
        }
      } catch (error) {
        console.error(`获取问题信息失败: ${error.response?.data?.detail || error.message}`)
      }
    },
    async fetchHistory() {
      try {
        const res = await axios.get('/api/chat/history')
        this.messages = [...res.data]
      } catch (error) {
        console.error(`获取历史对话失败: ${error.response?.data?.detail || error.message}`)
      }
    },
    askPresetQuestion(question) {
      this.setMessageAndSend(question)
    },
    async sendMessage(message) {
      this.addUserMessage(message);
      this.scrollToBottom();
    
      try {
        // 创建AI消息容器
        const aiMessage = {
          type: 'ai',
          blocks: [], // 包含所有内容板块
          content: '' // 兼容旧版（可选）
        };
        this.messages.push(aiMessage);
        
        // 构建带有工作模式和当前聚焦问题信息的请求
        const requestData = { 
          message,
          workMode: this.currentMode
        };
        if (this.currentMode !== 'chat') {
          requestData.autoCreateCategory = this.autoCreateCategory;
        }
        
        const response = await fetch('/api/chat/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestData)
        });
      
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';
        let currentBlock = null;
      
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          for (;;) {
            const match = buffer.match(/\n\n/);
            if (!match) break;

            const eventStr = buffer.substring(0, match.index);
            buffer = buffer.substring(match.index + 2);
            //console.log('发现事件：', eventStr)
            if (eventStr.startsWith('data: ')) {
              try {
                const data = JSON.parse(eventStr.substring(6));
                const currentAiMessage = this.messages[this.messages.length - 1];
              
                // 板块处理逻辑
                if (data.role == 'command') {
                  this.handleCommandContent(data.content)
                  continue
                }
                if (!currentBlock || currentBlock.role !== data.role) {
                  currentBlock = {
                    role: data.role,
                    content: '',
                    isLoading: !data.is_end
                  };
                  currentAiMessage.blocks.push({...currentBlock});
                }
              
                const blockIndex = currentAiMessage.blocks.length - 1;
                currentBlock.content += data.content;
                if (data.is_end) {
                  currentBlock.isLoading = false;
                  currentAiMessage.blocks[blockIndex] = {...currentBlock};
                  currentBlock = null;
                } else {
                  currentAiMessage.blocks[blockIndex] = {...currentBlock};
                }
              
                this.messages[this.messages.length - 1] = {...currentAiMessage};
                //this.scrollToBottom();
              } catch (e) {
                console.error('解析错误:', e);
              }
            }
          }
        }
        // 处理剩余buffer
        if (buffer.trim().length > 0) {
          console.warn('未处理的数据:', buffer);
        }
      } catch (error) {
        console.error('请求失败:', error);
      }
    },
    async handleCommandContent(content) {
      const command_info = JSON.parse(content)
      this.$emit('handleCommand', command_info.command, command_info.args);
      console.log('触发指令：', command_info.command, command_info.args)
    },
    addUserMessage(content) {
      this.messages.push({ content, type: 'user' })
    },
    setMessageAndFocus(question) {
      this.newMessage = question;
      this.recommendedQuestions = []
    },
    setMessageAndSend(message) {
      this.sendMessage(message);
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const chatContent = this.$refs.chatContent
        if (chatContent) {
          chatContent.scrollTop = chatContent.scrollHeight
        }
      })
    }
  }
}
</script>

<style scoped>
.chat-box {
  display: flex;
  flex-direction: column;
  height: 100%;
  border: 20px solid #fdfdfd;
}

.chat-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-bottom: 10px;
}

.mode-container {
  display: grid; /* 改用网格布局 */
  grid-template-columns: 150px 1fr; /* 两列布局 */
  gap: 8px;
  align-items: center;
  width: 100%;
  margin: 8px 0 12px;
}

.mode-selector {
  grid-column: 1; /* 固定在第一列 */
  width: 100% !important; /* 强制填充列宽 */
}

.more-settings-container {
  background: #f0f4ff;
  padding: 4px 10px;
  border-radius: 14px;
  font-size: 12px;
  color: #3a5ccc;
  border: 1px solid #d0d7ff;
  grid-column: 2; /* 固定在第二列 */
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  flex-direction: row;
  align-items: center;
}


.selected-icon {
  margin-right: 8px;
  font-size: 16px;
}
</style>