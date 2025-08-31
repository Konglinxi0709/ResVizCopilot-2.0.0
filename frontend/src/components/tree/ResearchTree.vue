<template>
  <div class="research-tree">
    <!-- 调试信息面板 -->
    <div v-if="showDebugInfo" class="debug-panel">
      <el-card class="debug-card" shadow="hover">
        <template #header>
          <div class="debug-header">
            <span>调试信息</span>
            <el-button 
              size="small" 
              text 
              @click="showDebugInfo = false"
            >
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </template>
        <div class="debug-content">
          <div class="debug-item">
            <el-tag v-if="currentMindElixirData" type="success">有Mind-elixir数据</el-tag>
            <el-tag v-else type="danger">无Mind-elixir数据</el-tag>
          </div>
          <div class="debug-item">
            <el-tag v-if="isSnapshotView" type="warning">快照查看模式</el-tag>
            <el-tag v-else type="info">正常模式</el-tag>
          </div>
          <div class="debug-item">
            <el-tag v-if="agentOperatingNodeId" type="info">智能体操作中: {{ agentOperatingNodeId.slice(0,8) }}...</el-tag>
            <el-tag v-else type="success">智能体空闲</el-tag>
          </div>
          <div class="debug-item">
            <el-tag v-if="selectedNodeId" type="primary">已选中节点: {{ selectedNodeId.slice(0,8) }}...</el-tag>
            <el-tag v-else>无选中节点</el-tag>
          </div>
        </div>
        <div class="debug-actions">
          <el-button size="small" @click="loadTestData">加载测试数据</el-button>
          <el-button size="small" @click="loadSnapshotTestData">加载快照测试</el-button>
          <el-button size="small" @click="simulateAgentOperation">模拟智能体操作</el-button>
          <el-button size="small" @click="clearTestData">清除数据</el-button>
        </div>
      </el-card>
    </div>
    
    <!-- 调试控制按钮 -->
    <div class="debug-toggle">
      <el-button 
        circle 
        size="small" 
        @click="showDebugInfo = !showDebugInfo"
        :type="showDebugInfo ? 'primary' : 'default'"
      >
        <el-icon><Setting /></el-icon>
      </el-button>
    </div>
    
    <!-- Mind-elixir渲染容器 -->
    <div class="tree-container">
      <MindElixirWrapper
        :mind-elixir-data="currentMindElixirData"
        :is-snapshot-view="isSnapshotView"
        :agent-operating-node-id="actualAgentOperatingNodeId"
        @node-selected="handleNodeSelected"
        @exit-snapshot-view="handleExitSnapshotView"
        @refresh-data="handleRefreshData"
      />
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { Close, Setting } from '@element-plus/icons-vue'
import MindElixirWrapper from './MindElixirWrapper.vue'
import { 
  simpleMindElixirData, 
  styledMindElixirData 
} from '@/data/simpleMindElixirData'

export default defineComponent({
  name: 'ResearchTree',
  
  components: {
    Close,
    Setting,
    MindElixirWrapper
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
  
  data() {
    return {
      // 调试面板控制
      showDebugInfo: true, // 初始显示调试面板，方便测试
      
      // 当前使用的Mind-elixir数据
      currentMindElixirData: null,
      
      // 测试用的智能体操作节点ID
      testAgentNodeId: null
    }
  },
  
  mounted() {
    // 自动加载测试数据
    this.loadTestData()
  },
  
  methods: {
    // 处理节点选择
    handleNodeSelected(nodeInfo) {
      console.log('研究树节点被选中:', nodeInfo)
      this.$emit('node-selected', nodeInfo)
    },
    
    // 处理退出快照查看
    handleExitSnapshotView() {
      console.log('退出快照查看模式')
      this.$emit('exit-snapshot-view')
    },
    
    // 处理刷新数据
    handleRefreshData() {
      console.log('请求刷新数据')
      // 重新加载测试数据
      this.loadTestData()
    },
    
    // 加载测试数据
    loadTestData() {
      console.log('加载简单Mind-elixir测试数据')
      this.currentMindElixirData = simpleMindElixirData
      this.testAgentNodeId = null
      this.$message.success('简单测试数据加载成功')
    },
    
    // 加载快照测试数据
    loadSnapshotTestData() {
      console.log('加载样式测试数据')
      this.currentMindElixirData = styledMindElixirData
      this.testAgentNodeId = null
      this.$message.success('样式测试数据加载成功')
    },
    
    // 模拟智能体操作
    simulateAgentOperation() {
      console.log('模拟智能体操作')
      this.testAgentNodeId = 'sub-problem-2'
      this.$message.info('智能体操作模拟已启动')
      
      // 3秒后自动停止模拟
      setTimeout(() => {
        this.testAgentNodeId = null
        this.$message.success('智能体操作模拟已结束')
      }, 3000)
    },
    
    // 清除测试数据
    clearTestData() {
      console.log('清除测试数据')
      this.currentMindElixirData = null
      this.testAgentNodeId = null
      this.$message.warning('测试数据已清除')
    }
  },
  
  // 计算属性，组合实际的智能体操作节点ID
  computed: {
    actualAgentOperatingNodeId() {
      return this.agentOperatingNodeId || this.testAgentNodeId
    }
  }
})
</script>

<style scoped>
.research-tree {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-color);
}

.tree-container {
  flex: 1;
  position: relative;
  min-height: 400px;
}

/* 调试面板样式 */
.debug-panel {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 1000;
  max-width: 400px;
}

.debug-card {
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border: 1px solid #e4e7ed;
}

.debug-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
}

.debug-content {
  margin-bottom: 16px;
}

.debug-item {
  margin-bottom: 8px;
}

.debug-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.debug-actions .el-button {
  font-size: 12px;
  padding: 4px 8px;
}

/* 调试控制按钮 */
.debug-toggle {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 999;
}

.debug-toggle .el-button {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(4px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .debug-panel {
    position: fixed;
    top: 10px;
    left: 10px;
    right: 10px;
    max-width: none;
  }
  
  .debug-toggle {
    top: 10px;
    right: 10px;
  }
  
  .debug-actions {
    justify-content: center;
  }
}

/* 深色主题适配 */
:root[data-theme="dark"] .debug-card {
  background: rgba(45, 45, 45, 0.95);
  border-color: #4c4d4f;
  color: #e4e7ed;
}
</style>
