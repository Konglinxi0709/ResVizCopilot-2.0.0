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
          <div class="project-name">{{ currentProject.project_name }}</div>
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
          <template v-for="project in projectList" :key="project?.project_name || 'unknown'">
            <div 
              v-if="project && project.project_name"
              class="project-card"
              :class="{ active: isCurrentProject(project) }"
              @click="handleLoadProject(project)"
            >
            <div class="project-info">
              <div class="project-name">{{ project.project_name }}</div>
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
        <el-button @click="cancelSaveAs">取消</el-button>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, MoreFilled } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/projectStore'
import dayjs from 'dayjs'

export default {
  name: 'ProjectManager',
  
  components: {
    Refresh, MoreFilled
  },
  
  emits: ['project-changed'],
  
  data() {
    return {
      projectStore: null,
      showSaveAsDialog: false,
      isSavingAs: false,
      saveAsFormRef: null,
      saveAsForm: {
        name: ''
      },
      saveAsRules: {
        name: [
          { required: true, message: '请输入工程名称', trigger: 'blur' },
          { min: 1, max: 50, message: '工程名称长度在 1 到 50 个字符', trigger: 'blur' }
        ]
      }
    }
  },
  
  computed: {
    currentProject() {
      return this.projectStore?.getCurrentProject
    },

    projectList() {
      return this.projectStore?.getProjectList || []
    },

    isLoading() {
      return this.projectStore?.getIsLoading || false
    }
  },
  
  async mounted() {
    this.projectStore = useProjectStore()
    await this.loadProjects()
  },
  
  methods: {
    // 加载工程列表
    async loadProjects() {
      try {
        await this.projectStore.refreshProjects()
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
      return this.currentProject?.project_name && project?.project_name &&
             this.currentProject.project_name === project.project_name
    },
    
    // 处理加载工程
    async handleLoadProject(project) {
      if (!project?.project_name || this.isCurrentProject(project)) {
        return
      }
      
      try {
        await this.projectStore.loadProject(project.project_name)
        this.$emit('project-changed', project)
        ElMessage.success(`已加载工程: ${project.project_name}`)
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
      if (!project?.project_name) return
      
      try {
        await ElMessageBox.confirm(
          `确定要删除工程 "${project.project_name}" 吗？此操作不可撤销。`,
          '确认删除',
          {
            confirmButtonText: '确定删除',
            cancelButtonText: '取消',
            type: 'warning',
            confirmButtonClass: 'el-button--danger'
          }
        )
        
        await this.projectStore.deleteProject(project.project_name)
        ElMessage.success(`工程 "${project.project_name}" 已删除`)
        
        // 如果删除的是当前工程，清空当前工程
        if (this.isCurrentProject(project)) {
          this.projectStore.clearCurrentProject()
          this.$emit('project-changed', null)
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除工程失败:', error)
          ElMessage.error('删除工程失败')
        }
      }
    },
    
    // 处理另存为工程
    async handleSaveAs() {
      if (!this.currentProject) {
        ElMessage.warning('请先加载一个工程')
        return
      }
      
      this.saveAsForm.name = `${this.currentProject.project_name}_副本`
      this.showSaveAsDialog = true
    },
    
    // 确认另存为
    async confirmSaveAs() {
      try {
        // 确保表单ref已可用
        await this.$nextTick()
        const formRef = this.$refs && this.$refs.saveAsFormRef
        if (formRef && formRef.validate) {
          await formRef.validate()
        }
        
        this.isSavingAs = true
        await this.projectStore.saveAsProject(this.saveAsForm.name)
        
        ElMessage.success(`工程已另存为: ${this.saveAsForm.name}`)
        this.showSaveAsDialog = false
        this.saveAsForm.name = ''
        
        // 刷新工程列表
        await this.loadProjects()

        // 通知父组件当前工程已变更，触发上层加载树与同步消息
        if (this.projectStore?.currentProject) {
          this.$emit('project-changed', this.projectStore.currentProject)
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('另存为工程失败:', error)
          ElMessage.error('另存为工程失败')
        }
      } finally {
        this.isSavingAs = false
      }
    },
    
    // 取消另存为
    cancelSaveAs() {
      this.showSaveAsDialog = false
      this.saveAsForm.name = ''
    },
    
    // 格式化时间
    formatTime(timeStr) {
      if (!timeStr) return ''
      return dayjs(timeStr).format('YYYY-MM-DD HH:mm')
    },
    
    // 获取工程操作菜单
    getProjectActions(project) {
      const actions = []
      
      // 加载操作
      if (!this.isCurrentProject(project)) {
        actions.push({
          label: '加载',
          icon: 'el-icon-folder-opened',
          action: () => this.handleLoadProject(project)
        })
      }
      
      // 删除操作
      actions.push({
        label: '删除',
        icon: 'el-icon-delete',
        action: () => this.handleDeleteProject(project),
        danger: true
      })
      
      return actions
    }
  }
}
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
