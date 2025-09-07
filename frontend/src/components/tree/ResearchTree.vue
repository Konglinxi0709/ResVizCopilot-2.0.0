<template>
  <div class="research-tree">

    <!-- Mind-elixir渲染容器 -->
    <div class="tree-container">
      <MindElixirWrapper
        :mind-elixir-data="currentMindElixirData"
        @node-select="handleNodeSelect"
      />
    </div>

    <!-- 快照查看指示器 -->
    <div v-if="isSnapshotView" class="snapshot-indicator">
      <el-card class="snapshot-card" shadow="hover">
        <div class="snapshot-content">
          <el-icon class="snapshot-icon"><Camera /></el-icon>
          <span class="snapshot-text">正在查看历史快照</span>
          <el-button
            size="small"
            type="primary"
            @click="handleExitSnapshotView"
            class="return-btn"
          >
            返回当前
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 智能体操作指示器 -->
    <div v-if="agentOperatingNodeId" class="agent-indicator">
      <el-card class="agent-card" shadow="hover">
        <div class="agent-content">
          <el-icon class="agent-icon rotating"><Loading /></el-icon>
          <span class="agent-text">智能体正在操作中...</span>
        </div>
      </el-card>
    </div>

    <!-- 解决方案面板 -->
    <SolutionPanel
      v-if="shouldShowSolutionPanel"
      :selected-node-id="selectedNodeId"
      @close="handleClosePanel"
    />

    <!-- 根问题面板 -->
    <RootProblemPanel
      v-if="shouldShowRootProblemPanel"
      :selected-node-id="selectedNodeId"
      @close="handleClosePanel"
    />

  </div>
</template>

<script>
import MindElixirWrapper from './MindElixirWrapper.vue'
import SolutionPanel from './SolutionPanel.vue'
import RootProblemPanel from './RootProblemPanel.vue'
import { useTreeStore } from '@/stores/treeStore'
import { useMessageStore } from '@/stores/messageStore'
import { Camera, Loading } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

export default {
  name: 'ResearchTree',
  
  components: {
    MindElixirWrapper,
    SolutionPanel,
    RootProblemPanel,
    Camera,
    Loading
  },
  
  
  data() {
    return {
      treeStore: null,
      selectedNodeId: null,
      shouldShowSolutionPanel: false, // 控制解决方案面板显示
      shouldShowRootProblemPanel: false, // 控制根问题面板显示
    }
  },
  
  computed: {
    // 从treeStore获取数据
    currentSnapshot() {
      return this.treeStore?.getCurrentSnapshot
    },

    isSnapshotView() {
      return this.treeStore?.getIsViewingSnapshot
    },

    agentOperatingNodeId() {
      return this.treeStore?.getAgentOperatingNodeId
    },

    // 当前使用的Mind-elixir数据
    currentMindElixirData() {
      return this.treeStore?.getDisplaySnapshotData
    },

  },

  async mounted() {
    this.treeStore = useTreeStore()
    this.messageStore = useMessageStore()
    await this.treeStore.refreshCurrentSnapshot()
  },
  
  methods: {
    // 处理节点选择
    async handleNodeSelect(nodeId) {
      console.log('研究树节点被选中:', nodeId)
      
      // 重置所有面板状态
      this.shouldShowSolutionPanel = false
      this.shouldShowRootProblemPanel = false
      this.selectedNodeId = nodeId
      
      // mind-root节点：创建根问题
      if (nodeId === 'mind-root') {
        this.shouldShowRootProblemPanel = true
        return
      }
      
      // 检查是否为根问题节点
      if (this.treeStore?.getIsRootProblem(nodeId)) {
        await this.handleRootProblemSelect()
        return
      }
      
      // 其他节点：检查是否显示解决方案面板
      this.checkSolutionPanelDisplay(nodeId)
    },

    // 检查是否显示解决方案面板
    checkSolutionPanelDisplay(nodeId) {
      const nodeType = this.treeStore.getNodeType(nodeId)
      if (nodeType === 'solution') {
        this.shouldShowSolutionPanel = true
      } else if (nodeType === 'problem') {
        const problemType = this.treeStore.getProblemNodeType(nodeId)
        if (problemType === 'implementation' && this.treeStore.getIsNodeEnabled(nodeId) === true) {
          this.shouldShowSolutionPanel = true
        }
        // 条件问题不显示任何面板
      }
    },

    // 处理根问题节点选择
    async handleRootProblemSelect() {
      try {
        // eslint-disable-next-line no-unused-vars
        const choice = await ElMessageBox.confirm(
          '请选择您要执行的操作：',
          '根问题操作',
          {
            distinguishCancelAndClose: true,
            confirmButtonText: '新建解决方案',
            cancelButtonText: '查看根问题',
            type: 'info',
            customClass: 'root-problem-dialog'
          }
        )
        
        // 用户选择了新建解决方案
        this.shouldShowSolutionPanel = true
        
      } catch (action) {
        if (action === 'cancel') {
          // 用户选择了查看根问题
          this.shouldShowRootProblemPanel = true
        }
        // action === 'close' 表示用户关闭了对话框，不做任何操作
      }
    },

    // 处理关闭面板
    handleClosePanel() {
      this.selectedNodeId = null
      this.shouldShowSolutionPanel = false
      this.shouldShowRootProblemPanel = false
    },

    // 处理退出快照查看
    handleExitSnapshotView() {
      console.log('退出快照查看模式')
      this.treeStore.exitSnapshotView()
    }
  }
}
</script>

<style scoped>
.research-tree {
  position: relative;
  height: 100%; /* 使用父容器的100%高度（center-panel已经减去了AppHeader） */
  max-height: 100%; /* 确保不超过父容器高度 */
  display: flex;
  flex-direction: column;
  background: var(--bg-color);
  overflow: hidden; /* 防止内容溢出 */
}

.tree-container {
  flex: 1;
  position: relative;
  min-height: 300px; /* 减小最小高度 */
  max-height: 100%; /* 使用父容器的全部可用高度 */
  overflow: hidden; /* 防止内容溢出 */
}

/* 快照查看指示器 */
.snapshot-indicator {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 1000;
}

.snapshot-card {
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border: 1px solid #e4e7ed;
}

.snapshot-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.snapshot-icon {
  color: #f59e0b;
  font-size: 18px;
}

.snapshot-text {
  font-weight: 500;
  color: #303133;
}

.return-btn {
  margin-left: auto;
}

/* 智能体操作指示器 */
.agent-indicator {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 1000;
}

.agent-card {
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border: 1px solid #e4e7ed;
}

.agent-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.agent-icon {
  color: #409eff;
  font-size: 18px;
}

.agent-icon.rotating {
  animation: rotating 2s linear infinite;
}

.agent-text {
  font-weight: 500;
  color: #303133;
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .tree-container {
    min-height: 250px; /* 移动端减小最小高度 */
  }

  .snapshot-indicator,
  .agent-indicator {
    top: 10px;
    left: 10px;
    right: 10px;
  }

  .snapshot-content,
  .agent-content {
    flex-direction: column;
    gap: 8px;
  }

  .return-btn {
    margin-left: 0;
    margin-top: 8px;
  }
}

/* 深色主题适配 */
:root[data-theme="dark"] .snapshot-card,
:root[data-theme="dark"] .agent-card {
  background: rgba(45, 45, 45, 0.95);
  border-color: #4c4d4f;
  color: #e4e7ed;
}
</style>
