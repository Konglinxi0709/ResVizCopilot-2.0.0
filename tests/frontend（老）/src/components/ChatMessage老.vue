<template>
  <div :class="['chat-message', message.type === 'user' ? 'user-message' : 'ai-message']">
    <div class="message-avatar">
      <img :src="avatar" alt="头像" class="avatar">
    </div>
    <div class="message-content" v-html="message.content"></div>
  </div>
</template>

<script>
export default {
  props: {
    message: {
      type: Object,
      required: true
    },
    userAvatar: {
      type: String,
      default: require('@/assets/user-logo-2.png')
    },
    aiAvatar: {
      type: String,
      default: require('@/assets/ai-logo.png')
    }
  },
  computed: {
    avatar() {
      return this.message.type === 'user' ? this.userAvatar : this.aiAvatar
    }
  }
}
</script>

<style scoped>
.chat-message {
  display: flex;
  align-items: flex-start;
  margin-bottom: 10px;
  max-width: 80%;
}

.user-message {
  flex-direction: row-reverse;
  margin-left: auto;
}

.user-message .message-avatar {
  margin-left: 10px;
}

.ai-message {
  flex-direction: row;
  margin-right: auto;
}

.ai-message .message-avatar {
  margin-right: 10px;
}

.message-content {
  padding: 10px;
  background-color: #e0e0e0;
  border-radius: 10px;
  margin: 0 10px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
}
</style>