<template>
  <div id="app" class="app-container">
    <!-- 应用头部 -->
    <AppHeader
      :current-project="getCurrentProject"
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
        </div>
        <ResearchTree />
      </div>

      <!-- 右侧面板 - 消息列表和AI对话 -->
      <div
        class="right-panel"
        :class="{ 'collapsed': rightPanelCollapsed }"
      >
        <div class="panel-header">
          <div class="panel-header-left">
            <el-icon v-if="!rightPanelCollapsed"><ChatDotRound /></el-icon>
            <h3 v-if="!rightPanelCollapsed">{{ $t('message.title') }}</h3>
            <el-tag v-if="!rightPanelCollapsed && getMessageCount > 0" type="info" size="small">
              {{ getMessageCount }} 条消息
            </el-tag>
          </div>

          <div class="panel-header-right">
            <!-- 连接状态指示 -->
            <div v-if="!rightPanelCollapsed" class="connection-status" :class="connectionStatusClass">
              <el-icon><component :is="connectionStatusIcon" /></el-icon>
              <span class="status-text">{{ connectionStatusText }}</span>
            </div>

            <!-- 消息操作下拉菜单 -->
            <el-dropdown v-if="!rightPanelCollapsed" @command="handleMessageAction" trigger="click">
              <el-button type="text" size="small">
                <el-icon><More /></el-icon>
              </el-button>

              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                    command="sync-messages"
                    :disabled="getIsGenerating"
                  >
                    <el-icon><Refresh /></el-icon>
                    同步消息
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>

            <el-button
              type="text"
              @click="toggleRightPanel"
              class="collapse-btn"
              :class="{ 'collapsed-btn': rightPanelCollapsed }"
            >
              <el-icon>
                <ArrowRight v-if="!rightPanelCollapsed" />
                <ArrowLeft v-else />
              </el-icon>
            </el-button>
          </div>
        </div>
        <MessageCenter
          v-if="!rightPanelCollapsed"
        />
      </div>
    </div>

    <!-- 全局加载指示器 -->
    <div v-if="getIsLoading" class="global-loading">
      <div class="loading-overlay">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <div class="loading-text">{{ loadingText || $t('app.loading') }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus'
import { 
  ArrowLeft, ArrowRight, Camera, ChatDotRound, More, Delete,
  Connection, Loading, Check, Refresh
} from '@element-plus/icons-vue'
import AppHeader from './components/shared/AppHeader.vue'
import ProjectManager from './components/project/ProjectManager.vue'
import ResearchTree from './components/tree/ResearchTree.vue'
import MessageCenter from './components/message/MessageCenter.vue'
import { useProjectStore } from './stores/projectStore'
import { useTreeStore } from './stores/treeStore'
import { useMessageStore } from './stores/messageStore'
import { useUIStore } from './stores/uiStore'

export default {
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
    Delete,
    Connection,
    Loading,
    Check,
    Refresh
  },
  
  data() {
    return {
      // Store实例
      projectStore: null,
      treeStore: null,
      messageStore: null,
      uiStore: null
    }
  },
  
  computed: {
    // 使用新的stores getters接口
    getCurrentProject() {
      return this.projectStore?.getCurrentProject
    },


    getMessageCount() {
      return this.messageStore?.getMessageCount
    },

    getIsGenerating() {
      return this.messageStore?.getIsGenerating
    },

    getError() {
      return this.messageStore?.getError
    },

    // UI状态
    leftPanelCollapsed() {
      return this.uiStore?.leftPanelCollapsed
    },

    rightPanelCollapsed() {
      return this.uiStore?.rightPanelCollapsed
    },

    getIsLoading() {
      // 检查所有存储器的加载状态
      return this.uiStore?.isLoading
    },

    loadingText() {
      return this.uiStore?.loadingText
    },

    // 连接状态
    connectionStatus() {
      if (this.getIsGenerating) {
        return 'generating'
      } else if (this.getError) {
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
    // 初始化store实例
    this.projectStore = useProjectStore()
    this.treeStore = useTreeStore()
    this.messageStore = useMessageStore()
    this.uiStore = useUIStore()
  },
  
  methods: {

    async loadCurrentProject() {
      if (!this.getCurrentProject) return

      try {
        // 加载研究树数据
        await this.projectStore.refreshProjects()
        await this.treeStore.refreshCurrentSnapshot()
        await this.messageStore.refreshMessages()
      } catch (error) {
        console.error('加载当前项目失败:', error)
        ElMessage.error('加载项目数据失败')
      }
    },
    
    // 面板折叠控制
    toggleLeftPanel() {
      this.uiStore.toggleLeftPanel()
    },
    
    toggleRightPanel() {
      this.uiStore.toggleRightPanel()
    },
    
    // 项目变更处理
    async handleProjectChanged() {
      try {
        console.log("触发项目变更处理！！！")
        await this.loadCurrentProject()
        // 同步消息历史，确保切换工程后右侧面板立即更新
        await this.treeStore.refreshCurrentSnapshot()
        await this.messageStore.refreshMessages()
        ElMessage.success('项目切换成功')
      } catch (error) {
        console.error('项目切换失败:', error)
        ElMessage.error('项目切换失败')
      }
    },
    
    
    // 语言切换
    handleLanguageChange(language) {
      this.uiStore.setLanguage(language)
      if (this.$i18n) {
        this.$i18n.locale = language
      }
    },
    
    // 主题切换
    handleThemeChange(theme) {
      this.uiStore.setTheme(theme)
    },
    
    // 消息操作
    async handleMessageAction(command) {
      switch (command) {
        case 'sync-messages':
          await this.messageStore.refreshMessages()
          break
        default:
          console.warn('未知的消息操作:', command)
      }
    },
    
  }
}
</script>

<style>
/* 全局样式变量 */
:root {
  --header-height: 60px;
  --panel-header-height: 60px; /* 增加到60px */
  --left-sidebar-width: 300px; /* 左侧面板宽度 */
  --right-sidebar-width: 600px; /* 右侧面板宽度 */
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

.left-panel {
  width: var(--left-sidebar-width);
  background-color: var(--bg-color);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}

.right-panel {
  width: var(--right-sidebar-width);
  border-right: none;
  border-left: 1px solid var(--border-color);
  background-color: var(--bg-color);
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
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
