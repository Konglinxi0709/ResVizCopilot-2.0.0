<template>
  <div class="project-manager">
    <div class="project-header">
      <h4>工程管理</h4>
      <el-button type="primary" size="small" @click="refreshProjects">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>
    
    <div class="project-content">
      <!-- 当前工程信息 -->
      <div v-if="currentProject" class="current-project-info">
        <h5>当前工程</h5>
        <div class="project-card current">
          <div class="project-name">{{ currentProject.name }}</div>
          <div class="project-actions">
            <el-button type="text" size="small" @click="handleSaveAs">
              另存为
            </el-button>
          </div>
        </div>
      </div>
      
      <!-- 工程列表 -->
      <div class="project-list-section">
        <h5>所有工程</h5>
        
        <div v-if="isLoading" class="loading">
          <el-skeleton :rows="3" animated />
        </div>
        
        <div v-else-if="projectList.length === 0" class="empty-state">
          <el-empty description="暂无工程" />
        </div>
        
        <div v-else class="project-list">
          <template v-for="project in projectList" :key="project?.name || 'unknown'">
            <div 
              v-if="project && project.name"
              class="project-card"
              :class="{ active: isCurrentProject(project) }"
              @click="handleLoadProject(project)"
            >
            <div class="project-info">
              <div class="project-name">{{ project.name }}</div>
              <div class="project-meta">
                <span class="create-time">
                  创建: {{ formatTime(project.created_at) }}
                </span>
              </div>
            </div>
            
            <div class="project-actions" @click.stop>
              <el-dropdown @command="(cmd) => handleProjectAction(cmd, project)">
                <el-button type="text" size="small">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item 
                      command="load" 
                      :disabled="isCurrentProject(project)"
                    >
                      加载工程
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided>
                      删除工程
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </template>
        </div>
      </div>
    </div>
    
    <!-- 另存为对话框 -->
    <el-dialog
      v-model="showSaveAsDialog"
      title="另存为工程"
      width="400px"
    >
      <el-form ref="saveAsFormRef" :model="saveAsForm" :rules="saveAsRules">
        <el-form-item label="新工程名称" prop="name">
          <el-input
            v-model="saveAsForm.name"
            placeholder="请输入新工程名称"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showSaveAsDialog = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="confirmSaveAs"
          :loading="isSavingAs"
        >
          确认
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { defineComponent, ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, MoreFilled } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/projectStore'
import dayjs from 'dayjs'

export default defineComponent({
  name: 'ProjectManager',
  
  components: {
    Refresh, MoreFilled
  },
  
  emits: ['project-changed'],
  
  setup(props, { emit }) {
    const projectStore = useProjectStore()
    
    const showSaveAsDialog = ref(false)
    const isSavingAs = ref(false)
    const saveAsFormRef = ref(null)
    
    const saveAsForm = ref({
      name: ''
    })
    
    const saveAsRules = {
      name: [
        { required: true, message: '请输入工程名称', trigger: 'blur' },
        { min: 1, max: 50, message: '工程名称长度在 1 到 50 个字符', trigger: 'blur' }
      ]
    }
    
    const currentProject = computed(() => projectStore.currentProject)
    const projectList = computed(() => projectStore.projectList)
    const isLoading = computed(() => projectStore.isLoading)
    
    return {
      projectStore,
      showSaveAsDialog,
      isSavingAs,
      saveAsFormRef,
      saveAsForm,
      saveAsRules,
      currentProject,
      projectList,
      isLoading,
      emit
    }
  },
  
  async mounted() {
    await this.loadProjects()
  },
  
  methods: {
    // 加载工程列表
    async loadProjects() {
      try {
        await this.projectStore.fetchProjectList()
      } catch (error) {
        console.error('加载工程列表失败:', error)
      }
    },
    
    // 刷新工程列表
    async refreshProjects() {
      await this.loadProjects()
      ElMessage.success('工程列表已刷新')
    },
    
    // 检查是否为当前工程
    isCurrentProject(project) {
      return this.currentProject?.name && project?.name && 
             this.currentProject.name === project.name
    },
    
    // 处理加载工程
    async handleLoadProject(project) {
      if (!project?.name || this.isCurrentProject(project)) {
        return
      }
      
      try {
        await this.projectStore.loadProject(project.name)
        this.$emit('project-changed', project)
        ElMessage.success(`已加载工程: ${project.name}`)
      } catch (error) {
        console.error('加载工程失败:', error)
        ElMessage.error('加载工程失败')
      }
    },
    
    // 处理工程操作
    async handleProjectAction(command, project) {
      switch (command) {
        case 'load':
          await this.handleLoadProject(project)
          break
        case 'delete':
          await this.handleDeleteProject(project)
          break
      }
    },
    
    // 处理删除工程
    async handleDeleteProject(project) {
      if (!project?.name) {
        ElMessage.error('无效的工程信息')
        return
      }
      
      try {
        await ElMessageBox.confirm(
          `确定要删除工程 "${project.name}" 吗？此操作不可恢复。`,
          '确认删除',
          {
            confirmButtonText: '删除',
            cancelButtonText: '取消',
            type: 'warning',
            confirmButtonClass: 'el-button--danger'
          }
        )
        
        await this.projectStore.deleteProject(project.name)
        ElMessage.success(`工程 "${project.name}" 已删除`)
        
        // 如果删除的是当前工程，通知父组件
        if (this.isCurrentProject(project)) {
          this.$emit('project-changed', null)
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除工程失败:', error)
          ElMessage.error('删除工程失败')
        }
      }
    },
    
    // 处理另存为
    handleSaveAs() {
      if (!this.currentProject) {
        ElMessage.warning('没有当前工程可另存为')
        return
      }
      
      this.saveAsForm.name = `${this.currentProject.name}_副本`
      this.showSaveAsDialog = true
    },
    
    // 确认另存为
    async confirmSaveAs() {
      try {
        const valid = await this.$refs.saveAsFormRef.validate()
        if (!valid) return
        
        this.isSavingAs = true
        
        const newProject = await this.projectStore.saveAsProject(this.saveAsForm.name)
        
        ElMessage.success(`工程已另存为: ${newProject.name}`)
        this.showSaveAsDialog = false
        this.$emit('project-changed', newProject)
        
      } catch (error) {
        console.error('另存为失败:', error)
        ElMessage.error(error.message || '另存为失败')
      } finally {
        this.isSavingAs = false
      }
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
.project-manager {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.project-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.project-header h4 {
  margin: 0;
  font-size: 16px;
  color: var(--text-color);
}

.project-content {
  flex: 1;
  overflow-y: auto;
}

.current-project-info {
  margin-bottom: 24px;
}

.current-project-info h5,
.project-list-section h5 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: var(--text-color);
  opacity: 0.8;
}

.project-card {
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: all 0.2s;
}

.project-card:hover {
  border-color: var(--primary-color);
  box-shadow: 0 2px 8px var(--shadow-color);
}

.project-card.current {
  border-color: var(--primary-color);
  background: rgba(64, 158, 255, 0.1);
}

.project-card.active {
  border-color: var(--primary-color);
  background: rgba(64, 158, 255, 0.05);
}

.project-info {
  flex: 1;
}

.project-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color);
  margin-bottom: 4px;
}

.project-meta {
  font-size: 12px;
  color: var(--text-color);
  opacity: 0.6;
}

.project-actions {
  display: flex;
  align-items: center;
}

.loading {
  padding: 16px;
}

.empty-state {
  padding: 32px 16px;
  text-align: center;
}
</style>
