<template>
  <div class="app-header">
    <div class="header-left">
      <!-- 应用Logo和标题 -->
      <div class="app-logo">
        <img src="@/assets/logo.png" alt="Logo" class="logo-image" />
        <h1 class="app-title">{{ $t('app.title') }}</h1>
      </div>
      
      <!-- 当前工程信息 -->
      <div v-if="currentProject" class="current-project">
        <el-tag type="primary" size="large">
          <el-icon><Folder /></el-icon>
          {{ currentProject.project_name }}
        </el-tag>
        <span v-if="lastSaveTime" class="save-time">
          最后保存: {{ formatTime(lastSaveTime) }}
        </span>
      </div>
    </div>
    
    <div class="header-right">
      <!-- 工程管理按钮 -->
      <div class="project-actions">
        <el-button 
          type="primary" 
          @click="handleCreateProject"
          :disabled="isOperationDisabled"
        >
          <el-icon><Plus /></el-icon>
          {{ $t('project.create') }}
        </el-button>
        
        <el-button 
          v-if="currentProject"
          type="success" 
          @click="handleSaveProject"
          :loading="isSaving"
          :disabled="isOperationDisabled"
        >
          <el-icon><Document /></el-icon>
          {{ $t('project.save') }}
        </el-button>
      </div>
      
      <!-- 设置按钮组 -->
      <div class="settings-group">
        <!-- 语言切换 -->
        <el-dropdown @command="handleLanguageChange" trigger="click">
          <el-button type="text" class="setting-btn">
🌐
            {{ currentLanguageLabel }}
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="zh-CN">
                <span :class="{ active: $i18n.locale === 'zh-CN' }">
                  中文
                </span>
              </el-dropdown-item>
              <el-dropdown-item command="en-US">
                <span :class="{ active: $i18n.locale === 'en-US' }">
                  English
                </span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        
        <!-- 主题切换 -->
        <el-button 
          type="text" 
          class="setting-btn"
          @click="handleThemeChange"
        >
          <el-icon>
            <Sunny v-if="currentTheme === 'dark'" />
            <Moon v-else />
          </el-icon>
        </el-button>
      </div>
    </div>
    
    <!-- 创建工程对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建新工程"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form ref="createFormRef" :model="createForm" :rules="createRules">
        <el-form-item label="工程名称" prop="name">
          <el-input
            v-model="createForm.name"
            placeholder="请输入工程名称"
            @keyup.enter="confirmCreateProject"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="cancelCreateProject">{{ $t('app.cancel') }}</el-button>
          <el-button 
            type="primary" 
            @click="confirmCreateProject"
            :loading="isCreating"
          >
            {{ $t('app.confirm') }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus'
import { 
  Folder, Plus, Document, Sunny, Moon 
} from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/projectStore'
import { useUIStore } from '@/stores/uiStore'
import dayjs from 'dayjs'

export default {
  name: 'AppHeader',
  
  components: {
    Folder, Plus, Document, Sunny, Moon
  },
  
  props: {
    currentProject: {
      type: Object,
      default: null
    }
  },
  
  emits: ['language-change', 'theme-change'],
  
  data() {
    return {
      projectStore: null,
      uiStore: null,
      showCreateDialog: false,
      isCreating: false,
      isSaving: false,
      createFormRef: null,
      createForm: {
        name: ''
      },
      createRules: {
        name: [
          { required: true, message: '请输入工程名称', trigger: 'blur' },
          { min: 1, max: 50, message: '工程名称长度在 1 到 50 个字符', trigger: 'blur' },
          {
            validator: (rule, value, callback) => {
              if (this.projectStore?.isProjectNameExists(value)) {
                callback(new Error('工程名称已存在'))
              } else {
                callback()
              }
            },
            trigger: 'blur'
          }
        ]
      }
    }
  },
  
  computed: {
    currentTheme() {
      return this.uiStore?.theme
    },

    lastSaveTime() {
      return this.projectStore?.getLastSaveTime
    },

    isOperationDisabled() {
      // 当有智能体正在工作或其他操作进行中时禁用
      return this.projectStore?.getIsLoading || this.uiStore?.isLoading
    },

    currentLanguageLabel() {
      const locale = this.uiStore?.language
      return locale === 'zh-CN' ? '中文' : 'English'
    }
  },
  
  mounted() {
    this.projectStore = useProjectStore()
    this.uiStore = useUIStore()
  },
  
  methods: {
    // 处理创建工程
    async handleCreateProject() {
      this.showCreateDialog = true
      this.createForm.name = ''
      
      // 等待对话框打开后聚焦输入框
      this.$nextTick(() => {
        if (this.createFormRef) {
          this.createFormRef.focus()
        }
      })
    },
    
    // 确认创建工程
    async confirmCreateProject() {
      if (!this.createFormRef) return
      
      try {
        await this.createFormRef.validate()
        
        this.isCreating = true
        await this.projectStore.createProject(this.createForm.name)
        
        ElMessage.success(`工程 "${this.createForm.name}" 创建成功`)
        this.showCreateDialog = false
        this.createForm.name = ''
      } catch (error) {
        console.error('创建工程失败:', error)
        ElMessage.error('创建工程失败')
      } finally {
        this.isCreating = false
      }
    },
    
    // 取消创建工程
    cancelCreateProject() {
      this.showCreateDialog = false
      this.createForm.name = ''
    },
    
    // 保存当前工程
    async handleSaveProject() {
      if (!this.currentProject) {
        ElMessage.warning('请先加载一个工程')
        return
      }
      
      try {
        this.isSaving = true
        await this.projectStore.saveProject()
        ElMessage.success('工程保存成功')
      } catch (error) {
        console.error('保存工程失败:', error)
        ElMessage.error('保存工程失败')
      } finally {
        this.isSaving = false
      }
    },
    
    // 切换语言
    handleLanguageChange() {
      const newLanguage = this.uiStore.language === 'zh-CN' ? 'en-US' : 'zh-CN'
      this.uiStore.setLanguage(newLanguage)
      this.$emit('language-change', newLanguage)
    },
    
    // 切换主题
    handleThemeChange() {
      const newTheme = this.uiStore.theme === 'light' ? 'dark' : 'light'
      this.uiStore.setTheme(newTheme)
      this.$emit('theme-change', newTheme)
    },
    
    // 格式化时间
    formatTime(timeStr) {
      if (!timeStr) return ''
      return dayjs(timeStr).format('MM-DD HH:mm')
    }
  }
}
</script>

<style scoped>
.app-header {
  height: var(--header-height);
  background-color: var(--bg-color);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 1px 4px var(--shadow-color);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.app-logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-image {
  width: 32px;
  height: 32px;
}

.app-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-color);
  margin: 0;
}

.current-project {
  display: flex;
  align-items: center;
  gap: 12px;
}

.save-time {
  font-size: 12px;
  color: var(--text-color);
  opacity: 0.7;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.project-actions {
  display: flex;
  gap: 8px;
}

.settings-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.setting-btn {
  padding: 8px;
  min-width: auto;
  display: flex;
  align-items: center;
  gap: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* 下拉菜单激活状态 */
.active {
  color: var(--primary-color);
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 767px) {
  .app-header {
    padding: 0 16px;
  }
  
  .header-left {
    gap: 16px;
  }
  
  .app-title {
    font-size: 18px;
  }
  
  .current-project {
    display: none;
  }
  
  .project-actions {
    flex-direction: column;
    gap: 4px;
  }
  
  .project-actions .el-button {
    font-size: 12px;
    padding: 4px 8px;
  }
}
</style>
