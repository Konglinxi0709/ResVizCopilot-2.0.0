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
          <div class="panel-header-left">
            <el-icon><ChatDotRound /></el-icon>
            <h3>{{ $t('message.title') }}</h3>
            <el-tag v-if="messageCount > 0" type="info" size="small">
              {{ messageCount }} 条消息
            </el-tag>
          </div>
          
          <div class="panel-header-right">
            <!-- 连接状态指示 -->
            <div class="connection-status" :class="connectionStatusClass">
              <el-icon><component :is="connectionStatusIcon" /></el-icon>
              <span class="status-text">{{ connectionStatusText }}</span>
            </div>
            
            <!-- 消息操作下拉菜单 -->
            <el-dropdown @command="handleMessageAction" trigger="click">
              <el-button type="text" size="small">
                <el-icon><More /></el-icon>
              </el-button>
              
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item 
                    command="sync-messages"
                    :icon="Refresh"
                    :disabled="isGenerating"
                  >
                    同步消息
                  </el-dropdown-item>
                  <el-dropdown-item 
                    command="clear-messages"
                    :icon="Delete"
                    divided
                  >
                    清空消息
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            
            <el-button 
              type="text" 
              @click="toggleRightPanel"
              class="collapse-btn"
            >
              <ArrowRight v-if="!rightPanelCollapsed" />
              <ArrowLeft v-else />
            </el-button>
          </div>
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
      <div class="loading-overlay">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <div class="loading-text">{{ loadingText || $t('app.loading') }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ArrowLeft, ArrowRight, Camera, ChatDotRound, More, Refresh, Delete,
  Connection, Loading, Check
} from '@element-plus/icons-vue'
import AppHeader from './components/shared/AppHeader.vue'
import ProjectManager from './components/project/ProjectManager.vue'
import ResearchTree from './components/tree/ResearchTree.vue'
import MessageCenter from './components/message/MessageCenter.vue'
import { useProjectStore } from './stores/projectStore'
import { useTreeStore } from './stores/treeStore'
import { useMessageStore } from './stores/messageStore'
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
    Camera,
    ChatDotRound,
    More,
    Refresh,
    Delete,
    Connection,
    Loading,
    Check
  },
  
  setup() {
    const projectStore = useProjectStore()
    const treeStore = useTreeStore()
    const messageStore = useMessageStore()
    const uiStore = useUIStore()
    
    return {
      projectStore,
      treeStore,
      messageStore,
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
    },
    
    // 消息相关计算属性
    messageCount() {
      return this.messageStore.messageCount
    },
    
    isGenerating() {
      return this.messageStore.isGenerating
    },
    
    // 连接状态
    connectionStatus() {
      if (this.isGenerating) {
        return 'generating'
      } else if (this.messageStore.error) {
        return 'error'
      } else {
        return 'connected'
      }
    },
    
    connectionStatusClass() {
      return `status-${this.connectionStatus}`
    },
    
    connectionStatusIcon() {
      switch (this.connectionStatus) {
        case 'generating': return 'Loading'
        case 'error': return 'Connection'
        case 'connected': return 'Connection'
        default: return 'Check'
      }
    },
    
    connectionStatusText() {
      switch (this.connectionStatus) {
        case 'generating': return '正在生成...'
        case 'error': return '连接错误'
        case 'connected': return '已连接'
        default: return '就绪'
      }
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

    handleAgentOperating(nodeId) {
      this.treeStore.setAgentOperatingNode(nodeId)
    },
    
    exitSnapshotView() {
      this.treeStore.exitSnapshotView()
    },
    
    // 消息操作方法
    async handleMessageAction(command) {
      try {
        switch (command) {
          case 'sync-messages':
            await this.syncMessages()
            break
          case 'clear-messages':
            await this.clearMessages()
            break
        }
      } catch (error) {
        console.error('消息操作失败:', error)
        ElMessage.error('操作失败')
      }
    },
    
    async syncMessages() {
      try {
        const success = await this.messageStore.syncMessagesFromBackend()
        if (success) {
          ElMessage.success('消息同步成功')
        } else {
          ElMessage.error('消息同步失败')
        }
      } catch (error) {
        console.error('同步消息失败:', error)
        ElMessage.error('同步消息失败')
      }
    },
    
    async clearMessages() {
      try {
        await ElMessageBox.confirm(
          '确定要清空所有消息吗？此操作不可恢复。',
          '确认清空',
          {
            confirmButtonText: '确定清空',
            cancelButtonText: '取消',
            type: 'warning',
            confirmButtonClass: 'el-button--danger'
          }
        )
        
        this.messageStore.clearMessages()
        ElMessage.success('消息已清空')
        
      } catch (error) {
        // 用户取消操作
        if (error === 'cancel') {
          return
        }
        throw error
      }
    }
  }
})
</script>

<style>
/* 全局样式变量 */
:root {
  --header-height: 60px;
  --panel-header-height: 60px; /* 增加到60px */
  --sidebar-width: 600px;
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

.panel-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.panel-header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 连接状态 */
.connection-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 12px;
  transition: all 0.3s;
}

.status-connected {
  color: var(--success-color);
  background: var(--success-color-lighter, #f0f9ff);
}

.status-generating {
  color: var(--warning-color);
  background: var(--warning-color-lighter, #fdf6ec);
}

.status-generating .el-icon {
  animation: spin 1s linear infinite;
}

.status-error {
  color: var(--danger-color);
  background: var(--danger-color-lighter, #fef0f0);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.status-text {
  font-weight: 500;
}

/* 全局加载指示器 */
.global-loading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: white;
}

.loading-icon {
  font-size: 32px;
  animation: spin 1s linear infinite;
}

.loading-text {
  font-size: 16px;
  font-weight: 500;
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