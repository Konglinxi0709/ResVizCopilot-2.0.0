<template>
  <div :class="['chat-message', message.type === 'user' ? 'user-message' : 'ai-message']">
    <div class="message-avatar">
      <img :src="avatar" :alt="$t('chatMessage.avatar')" class="avatar">
    </div>
    
    <!-- 用户消息直接显示 -->
    <div v-if="message.type === 'user'" class="message-content text-block">
      {{ message.content }}
    </div>

    <!-- AI消息显示多个板块 -->
    <div v-else class="message-content text-block">
      <div v-for="(block, index) in message.blocks" :key="index">
        <!-- AI角色直接显示文本 -->
        <template v-if="block.role === 'ai' && block.content != ''">
          <MarkdownRenderer :content="block.content" />
        </template>

        <!-- 其他角色显示折叠面板 -->
        <ListItem v-else-if="block.role != 'ai' && block.role != 'command'">
          <template #title>
            <div class="block-header">
              <span>{{ $t('chatMessage.processing', { role: block.role }) }}</span>
              <el-icon v-if="block.isLoading" class="loading-icon">
                <Loading />
              </el-icon>
            </div>
          </template>
          <template #expand-content>
            {{ block.content }}
          </template>
        </ListItem>
      </div>
    </div>
  </div>
</template>

<script>
import { Loading } from '@element-plus/icons-vue'
import ListItem from '@/components/ListItem.vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'

export default {
  components: {
    ListItem,
    Loading,
    MarkdownRenderer
  },
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

.message-content > div {
  margin-bottom: 12px;
}

.message-content > div:last-child {
  margin-bottom: 0;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
}

.block-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.loading-icon {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>