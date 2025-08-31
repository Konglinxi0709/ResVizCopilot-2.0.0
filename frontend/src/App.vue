<template>
  <div id="app" class="app-container">
    <!-- 应用头部 -->
    <AppHeader 
      :current-project="currentProject"
      @language-change="handleLanguageChange"
      @theme-change="handleThemeChange"
    />
    
    <!-- 主体内容区域 -->
    <div class="main-content">
      <!-- 左侧面板 - 工程管理 -->
      <div 
        class="left-panel" 
        :class="{ 'collapsed': leftPanelCollapsed }"
      >
        <div class="panel-header">
          <h3 v-if="!leftPanelCollapsed">{{ $t('project.list') }}</h3>
          <el-button 
            type="text" 
            @click="toggleLeftPanel"
            class="collapse-btn"
            :class="{ 'collapsed-btn': leftPanelCollapsed }"
          >
            <el-icon>
              <ArrowLeft v-if="!leftPanelCollapsed" />
              <ArrowRight v-else />
            </el-icon>
          </el-button>
        </div>
        <ProjectManager 
          v-if="!leftPanelCollapsed"
          @project-changed="handleProjectChanged"
        />
      </div>
      
      <!-- 中央面板 - 研究树可视化 -->
      <div class="center-panel">
        <div class="panel-header">
          <h3>{{ $t('tree.title') }}</h3>
          <div class="tree-controls">
            <el-button 
              v-if="isViewingSnapshot" 
              type="warning" 
              @click="exitSnapshotView"
            >
              <el-icon><Camera /></el-icon>
              {{ $t('tree.backToCurrent') }}
            </el-button>
          </div>
        </div>
        <ResearchTree 
          :snapshot-data="currentSnapshotData"
          :is-snapshot-view="isViewingSnapshot"
          :agent-operating-node-id="agentOperatingNodeId"
          @node-selected="handleNodeSelected"
          @exit-snapshot-view="exitSnapshotView"
        />
      </div>
      
      <!-- 右侧面板 - 消息列表和AI对话 -->
      <div 
        class="right-panel" 
        :class="{ 'collapsed': rightPanelCollapsed }"
      >
        <div class="panel-header">
          <h3>{{ $t('message.title') }}</h3>
          <el-button 
            type="text" 
            @click="toggleRightPanel"
            class="collapse-btn"
          >
            <ArrowRight v-if="!rightPanelCollapsed" />
            <ArrowLeft v-else />
          </el-button>
        </div>
        <MessageCenter 
          v-if="!rightPanelCollapsed"
          :selected-node-id="selectedNodeId"
          @view-snapshot="handleViewSnapshot"
          @agent-operating="handleAgentOperating"
        />
      </div>
    </div>
    
    <!-- 全局加载指示器 -->
    <div v-if="isLoading" class="global-loading">
      <el-loading 
        :text="loadingText || $t('app.loading')"
        background="rgba(0, 0, 0, 0.7)"
      />
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight, Camera } from '@element-plus/icons-vue'
import AppHeader from './components/shared/AppHeader.vue'
import ProjectManager from './components/project/ProjectManager.vue'
import ResearchTree from './components/tree/ResearchTree.vue'
import MessageCenter from './components/message/MessageCenter.vue'
import { useProjectStore } from './stores/projectStore'
import { useTreeStore } from './stores/treeStore'
import { useUIStore } from './stores/uiStore'

export default defineComponent({
  name: 'App',
  components: {
    AppHeader,
    ProjectManager,
    ResearchTree,
    MessageCenter,
    ArrowLeft,
    ArrowRight,
    Camera
  },
  
  setup() {
    const projectStore = useProjectStore()
    const treeStore = useTreeStore()
    const uiStore = useUIStore()
    
    return {
      projectStore,
      treeStore,
      uiStore
    }
  },
  
  computed: {
    currentProject() {
      return this.projectStore.currentProject
    },
    
    leftPanelCollapsed() {
      return this.uiStore.leftPanelCollapsed
    },
    
    rightPanelCollapsed() {
      return this.uiStore.rightPanelCollapsed
    },
    
    isLoading() {
      return this.uiStore.isLoading
    },
    
    loadingText() {
      return this.uiStore.loadingText
    },
    
    currentSnapshotData() {
      return this.treeStore.currentSnapshot
    },
    
    isViewingSnapshot() {
      return this.treeStore.isViewingSnapshot
    },
    
    selectedNodeId() {
      return this.treeStore.selectedNodeId
    },
    
    agentOperatingNodeId() {
      return this.treeStore.agentOperatingNodeId
    }
  },
  
  async mounted() {
    try {
      // 初始化应用
      await this.initializeApp()
    } catch (error) {
      console.error('应用初始化失败:', error)
      ElMessage.error('应用初始化失败，请刷新页面重试')
    }
  },
  
  methods: {
    async initializeApp() {
      // 设置加载状态
      this.uiStore.setLoading(true, '正在初始化应用...')
      
      try {
        // 加载项目列表
        await this.projectStore.fetchProjectList()
        
        // 如果有当前项目，加载项目数据
        if (this.currentProject) {
          await this.loadCurrentProject()
        }
      } finally {
        this.uiStore.setLoading(false)
      }
    },
    
    async loadCurrentProject() {
      if (!this.currentProject) return
      
      try {
        // 加载研究树数据
        await this.treeStore.loadCurrentSnapshot()
      } catch (error) {
        console.error('加载项目数据失败:', error)
        ElMessage.error('加载项目数据失败')
      }
    },
    
    handleLanguageChange(locale) {
      this.$i18n.locale = locale
      this.uiStore.setLanguage(locale)
    },
    
    handleThemeChange(theme) {
      this.uiStore.setTheme(theme)
      // 应用主题到document
      document.documentElement.setAttribute('data-theme', theme)
    },
    
    toggleLeftPanel() {
      this.uiStore.toggleLeftPanel()
    },
    
    toggleRightPanel() {
      this.uiStore.toggleRightPanel()
    },
    
    async handleProjectChanged(project) {
      try {
        this.uiStore.setLoading(true, '正在切换项目...')
        
        // 切换项目
        await this.projectStore.setCurrentProject(project)
        
        // 重新加载项目数据
        await this.loadCurrentProject()
        
        ElMessage.success(`已切换到项目: ${project.name}`)
      } catch (error) {
        console.error('切换项目失败:', error)
        ElMessage.error('切换项目失败')
      } finally {
        this.uiStore.setLoading(false)
      }
    },
    
    handleNodeSelected(nodeInfo) {
      this.treeStore.setSelectedNode(nodeInfo.id)
    },
    
    async handleViewSnapshot(snapshotId) {
      try {
        await this.treeStore.viewSnapshot(snapshotId)
      } catch (error) {
        console.error('查看快照失败:', error)
        ElMessage.error('查看快照失败')
      }
    },
    
    exitSnapshotView() {
      this.treeStore.exitSnapshotView()
    },
    
    handleAgentOperating(nodeId) {
      this.treeStore.setAgentOperatingNode(nodeId)
    }
  }
})
</script>

<style>
/* 全局样式变量 */
:root {
  --header-height: 60px;
  --panel-header-height: 60px; /* 增加到60px */
  --sidebar-width: 300px;
  --sidebar-collapsed-width: 50px;
  
  /* 亮色主题 */
  --bg-color: #ffffff;
  --text-color: #303133;
  --border-color: #dcdfe6;
  --shadow-color: rgba(0, 0, 0, 0.1);
  --primary-color: #409eff;
  --success-color: #67c23a;
  --warning-color: #e6a23c;
  --danger-color: #f56c6c;
}

/* 暗色主题 */
[data-theme="dark"] {
  --bg-color: #1a1a1a;
  --text-color: #e4e7ed;
  --border-color: #4c4d4f;
  --shadow-color: rgba(0, 0, 0, 0.3);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  background-color: var(--bg-color);
  color: var(--text-color);
}

.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.main-content {
  flex: 1;
  display: flex;
  height: calc(100vh - var(--header-height));
}

.left-panel,
.right-panel {
  width: var(--sidebar-width);
  background-color: var(--bg-color);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}

.right-panel {
  border-right: none;
  border-left: 1px solid var(--border-color);
}

.left-panel.collapsed,
.right-panel.collapsed {
  width: var(--sidebar-collapsed-width);
}

.center-panel {
  flex: 1;
  background-color: var(--bg-color);
  display: flex;
  flex-direction: column;
  min-width: 600px;
}

.panel-header {
  height: var(--panel-header-height) !important;
  min-height: 60px !important; /* 强制最小高度 */
  max-height: 60px !important; /* 强制最大高度 */
  padding: 0 16px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: var(--bg-color);
  flex-shrink: 0; /* 防止被压缩 */
}

.panel-header h3 {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-color);
}

.collapse-btn {
  padding: 4px;
  min-width: auto;
}

.collapsed-btn {
  width: 100%;
  justify-content: center;
}

.tree-controls {
  display: flex;
  gap: 8px;
}

.global-loading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
}

/* 响应式设计 */
@media (max-width: 1199px) {
  .left-panel,
  .right-panel {
    position: absolute;
    height: 100%;
    z-index: 100;
    box-shadow: 2px 0 6px var(--shadow-color);
  }
  
  .left-panel.collapsed,
  .right-panel.collapsed {
    transform: translateX(-100%);
  }
  
  .right-panel.collapsed {
    transform: translateX(100%);
  }
}

@media (max-width: 767px) {
  .main-content {
    flex-direction: column;
  }
  
  .left-panel,
  .right-panel {
    width: 100%;
    height: 200px; /* 固定高度而不是百分比 */
  }
  
  .center-panel {
    flex: 1; /* 占据剩余空间 */
    min-width: auto;
    min-height: 400px; /* 确保最小高度 */
  }
}
</style>