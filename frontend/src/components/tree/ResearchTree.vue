<template>
  <div class="research-tree">
    <div class="tree-container">
      <!-- 临时占位内容 -->
      <div class="placeholder">
        <el-icon size="64" color="#409eff"><Share /></el-icon>
        <h3>研究树可视化</h3>
        <p>基于 Mind-elixir 的思维导图组件</p>
        <div class="feature-list">
          <el-tag v-if="snapshotData" type="success">有快照数据</el-tag>
          <el-tag v-if="isSnapshotView" type="warning">快照查看模式</el-tag>
          <el-tag v-if="agentOperatingNodeId" type="info">智能体操作中</el-tag>
          <el-tag v-if="selectedNodeId" type="primary">节点已选中</el-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { Share } from '@element-plus/icons-vue'

export default defineComponent({
  name: 'ResearchTree',
  
  components: {
    Share
  },
  
  props: {
    snapshotData: {
      type: Object,
      default: null
    },
    isSnapshotView: {
      type: Boolean,
      default: false
    },
    agentOperatingNodeId: {
      type: String,
      default: null
    },
    selectedNodeId: {
      type: String,
      default: null
    }
  },
  
  emits: ['node-selected', 'exit-snapshot-view'],
  
  methods: {
    // 模拟节点选择
    handleNodeSelect() {
      this.$emit('node-selected', {
        id: 'test-node-1',
        title: '测试节点',
        data: {}
      })
    },
    
    // 退出快照查看
    exitSnapshotView() {
      this.$emit('exit-snapshot-view')
    }
  }
})
</script>

<style scoped>
.research-tree {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.tree-container {
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
}
</style>
