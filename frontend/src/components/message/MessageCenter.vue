<template>
  <div class="message-center">
    <div class="message-container">
      <!-- 临时占位内容 -->
      <div class="placeholder">
        <el-icon size="64" color="#67c23a"><ChatDotRound /></el-icon>
        <h3>AI对话中心</h3>
        <p>智能体消息列表和对话功能</p>
        <div class="feature-list">
          <el-tag v-if="selectedNodeId" type="primary">节点: {{ selectedNodeId }}</el-tag>
          <el-tag type="info">SSE流式对话</el-tag>
          <el-tag type="success">多智能体支持</el-tag>
        </div>
        
        <!-- 模拟操作按钮 -->
        <div class="mock-actions">
          <el-button type="primary" @click="mockViewSnapshot">
            模拟查看快照
          </el-button>
          <el-button type="warning" @click="mockAgentWorking">
            模拟智能体工作
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { ChatDotRound } from '@element-plus/icons-vue'

export default defineComponent({
  name: 'MessageCenter',
  
  components: {
    ChatDotRound
  },
  
  props: {
    selectedNodeId: {
      type: String,
      default: null
    }
  },
  
  emits: ['view-snapshot', 'agent-operating'],
  
  methods: {
    // 模拟查看快照
    mockViewSnapshot() {
      const mockSnapshotId = 'snapshot_' + Date.now()
      this.$emit('view-snapshot', mockSnapshotId)
    },
    
    // 模拟智能体工作
    mockAgentWorking() {
      const mockNodeId = 'node_' + Date.now()
      this.$emit('agent-operating', mockNodeId)
      
      // 3秒后停止
      setTimeout(() => {
        this.$emit('agent-operating', null)
      }, 3000)
    }
  }
})
</script>

<style scoped>
.message-center {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.message-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-color);
}

.placeholder {
  text-align: center;
  padding: 40px;
}

.placeholder h3 {
  margin: 16px 0 8px 0;
  color: var(--text-color);
}

.placeholder p {
  margin: 0 0 20px 0;
  color: var(--text-color);
  opacity: 0.7;
}

.feature-list {
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.mock-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}
</style>
