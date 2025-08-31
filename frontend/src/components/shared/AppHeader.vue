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
          {{ currentProject.name }}
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
          @click="toggleTheme"
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
            @keyup.enter="confirmCreate"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="cancelCreate">{{ $t('app.cancel') }}</el-button>
          <el-button 
            type="primary" 
            @click="confirmCreate"
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
import { defineComponent, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Folder, Plus, Document, Sunny, Moon 
} from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/projectStore'
import { useUIStore } from '@/stores/uiStore'
import dayjs from 'dayjs'

export default defineComponent({
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
  
  setup() {
    const projectStore = useProjectStore()
    const uiStore = useUIStore()
    
    // 响应式数据
    const showCreateDialog = ref(false)
    const isCreating = ref(false)
    const isSaving = ref(false)
    const createFormRef = ref(null)
    
    const createForm = ref({
      name: ''
    })
    
    const createRules = {
      name: [
        { required: true, message: '请输入工程名称', trigger: 'blur' },
        { min: 1, max: 50, message: '工程名称长度在 1 到 50 个字符', trigger: 'blur' },
        {
          validator: (rule, value, callback) => {
            if (projectStore.isProjectNameExists(value)) {
              callback(new Error('工程名称已存在'))
            } else {
              callback()
            }
          },
          trigger: 'blur'
        }
      ]
    }
    
    // 计算属性
    const currentTheme = computed(() => uiStore.theme)
    const lastSaveTime = computed(() => projectStore.lastSaveTime)
    const isOperationDisabled = computed(() => {
      // 当有智能体正在工作或其他操作进行中时禁用
      return projectStore.isLoading || uiStore.isLoading
    })
    
    const currentLanguageLabel = computed(() => {
      const locale = uiStore.language
      return locale === 'zh-CN' ? '中文' : 'English'
    })
    
    return {
      projectStore,
      uiStore,
      showCreateDialog,
      isCreating,
      isSaving,
      createFormRef,
      createForm,
      createRules,
      currentTheme,
      lastSaveTime,
      isOperationDisabled,
      currentLanguageLabel
    }
  },
  
  methods: {
    // 处理创建工程
    async handleCreateProject() {
      this.showCreateDialog = true
      this.createForm.name = ''
      
      // 等待对话框打开后聚焦输入框
      this.$nextTick(() => {
        this.$refs.createFormRef?.clearValidate()
      })
    },
    
    // 确认创建工程
    async confirmCreate() {
      try {
        // 验证表单
        const valid = await this.$refs.createFormRef.validate()
        if (!valid) return
        
        this.isCreating = true
        
        // 创建工程
        await this.projectStore.createProject(this.createForm.name)
        
        ElMessage.success(`工程 "${this.createForm.name}" 创建成功`)
        this.showCreateDialog = false
        
      } catch (error) {
        console.error('创建工程失败:', error)
        ElMessage.error(error.message || '创建工程失败')
      } finally {
        this.isCreating = false
      }
    },
    
    // 取消创建工程
    cancelCreate() {
      this.showCreateDialog = false
      this.createForm.name = ''
    },
    
    // 处理保存工程
    async handleSaveProject() {
      try {
        this.isSaving = true
        
        await this.projectStore.saveProject()
        
        ElMessage.success('工程保存成功')
      } catch (error) {
        console.error('保存工程失败:', error)
        ElMessage.error(error.message || '保存工程失败')
      } finally {
        this.isSaving = false
      }
    },
    
    // 处理语言切换
    handleLanguageChange(locale) {
      this.uiStore.setLanguage(locale)
      this.$i18n.locale = locale
      this.$emit('language-change', locale)
      ElMessage.success(locale === 'zh-CN' ? '已切换到中文' : 'Switched to English')
    },
    
    // 切换主题
    toggleTheme() {
      const newTheme = this.currentTheme === 'light' ? 'dark' : 'light'
      this.uiStore.setTheme(newTheme)
      this.$emit('theme-change', newTheme)
    },
    
    // 格式化时间
    formatTime(time) {
      if (!time) return ''
      return dayjs(time).format('MM-DD HH:mm')
    }
  }
})
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
