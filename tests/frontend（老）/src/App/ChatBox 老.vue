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
    
    <ChatInput @send="sendMessage" />
  </div>
</template>

<script>
import InitialContent from '@/components/InitialContent.vue'
import ChatMessage from '@/components/ChatMessage.vue'
import RecommendedQuestions from '@/components/RecommendedQuestions.vue'
import ChatInput from '@/components/ChatInput.vue'

export default {
  components: {
    InitialContent,
    ChatMessage,
    RecommendedQuestions,
    ChatInput
  },
  data() {
    return {
      presetQuestions: [
        '中美近十年论文量对比',
        '地理图表展示国家间论文数量分布',
        '各作者之间的合作是什么样的？',
        '可视化学术论文的引用网络'
      ],
      messages: [],
      recommendedQuestions: []
    }
  },
  methods: {
    askPresetQuestion(question) {
      this.setMessageAndSend(question)
    },
    async sendMessage(message) {
      this.addUserMessage(message)
      this.scrollToBottom()

      // 模拟AI回复
      const aiResponse = "AI消息"
      this.addAiMessage(aiResponse)
      this.scrollToBottom()
    },
    addUserMessage(content) {
      this.messages.push({ content, type: 'user' })
    },
    addAiMessage(content) {
      this.messages.push({ content, type: 'ai' })
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
  padding-bottom: 10px;
}
</style>