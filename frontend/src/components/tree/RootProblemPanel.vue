<template>
  <div class="root-problem-panel-container">
    <!-- 背景遮罩 -->
    <div class="overlay" @click.self="handleClose"></div>
    <!-- 面板主体 -->
    <div class="root-problem-panel">
    <!-- 头部 -->
    <div class="panel-header">
      <!-- 标题部分 -->
      <div class="header-title">
        <!-- 编辑模式：标题输入框 -->
        <el-input
          v-if="isEditing"
          v-model="localData.title"
          placeholder="请输入根问题标题"
          class="title-input"
          size="large"
        />
        <!-- 展示模式：标题文本 -->
        <h2 v-else class="title-text">
          {{ currentData.title || '新建根问题' }}
        </h2>
      </div>

      <!-- 状态和操作区域 -->
      <div class="header-actions">
        <!-- 问题类型显示 -->
        <div class="status-section">
          <el-tag 
            :type="getProblemTypeTagType(currentData.problem_type)" 
            size="large"
            class="status-tag"
          >
            {{ getProblemTypeText(currentData.problem_type) }}
          </el-tag>
          
          <!-- 编辑状态指示器 -->
          <el-tag 
            v-if="isEditing"
            type="success"
            size="large"
            class="edit-mode-tag"
          >
            {{ isCreateMode ? '新建中' : '编辑中' }}
          </el-tag>
        </div>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <!-- 编辑模式按钮 -->
          <template v-if="isEditing">
            <el-button 
              type="primary" 
              @click="handleSave"
              :loading="isSaving"
            >
              保存
            </el-button>
            <el-button @click="handleCancel">
              取消
            </el-button>
          </template>
          
          <!-- 展示模式按钮 -->
          <template v-else>
            <el-button 
              v-if="!isCreateMode"
              type="danger" 
              @click="handleDelete"
              :disabled="!canEdit"
              :loading="isDeleting"
            >
              删除
            </el-button>
            <el-button 
              type="primary" 
              @click="handleEdit"
              :disabled="!canEdit"
            >
              编辑
            </el-button>
            <el-button @click="handleClose">
              关闭
            </el-button>
          </template>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="panel-content">
      <!-- 重要性 -->
      <div class="content-column">
        <div class="column-header">重要性</div>
        <div class="column-content">
          <!-- 编辑模式 -->
          <el-input
            v-if="isEditing"
            v-model="localData.significance"
            type="textarea"
            :rows="15"
            placeholder="请描述问题的重要性"
            class="content-textarea"
          />
          <!-- 展示模式 -->
          <MarkdownRenderer
            v-else
            :content="currentData.significance || ''"
            class="content-markdown"
          />
        </div>
      </div>

      <!-- 评判标准 -->
      <div class="content-column">
        <div class="column-header">评判标准</div>
        <div class="column-content">
          <!-- 编辑模式 -->
          <el-input
            v-if="isEditing"
            v-model="localData.criteria"
            type="textarea"
            :rows="15"
            placeholder="请描述问题的评判标准"
            class="content-textarea"
          />
          <!-- 展示模式 -->
          <MarkdownRenderer
            v-else
            :content="currentData.criteria || ''"
            class="content-markdown"
          />
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script>
import { ElButton, ElInput, ElTag, ElMessage, ElMessageBox } from 'element-plus'
import MarkdownRenderer from '@/components/message/MarkdownRenderer.vue'
import { useTreeStore } from '@/stores/treeStore'
import { useMessageStore } from '@/stores/messageStore'

export default {
  name: 'RootProblemPanel',

  components: {
    ElButton,
    ElInput,
    ElTag,
    MarkdownRenderer
  },

  props: {
    // 选中的节点ID（根问题ID或mind-root）
    selectedNodeId: {
      type: String,
      default: null
    }
  },

  emits: ['close'],

  data() {
    return {
      treeStore: null,
      messageStore: null,
      
      // 编辑状态
      isEditing: false,
      isSaving: false,
      isDeleting: false,
      
      // 本地编辑数据
      localData: {
        title: '',
        significance: '',
        criteria: '',
        problem_type: 'implementation'
      },
      
      // 原始数据备份
      originalData: null
    }
  },

  computed: {
    // 是否为创建模式
    isCreateMode() {
      // 只依赖于 selectedNodeId，避免循环依赖
      return this.selectedNodeId === 'mind-root'
    },

    // 当前显示的数据
    currentData() {
      if (this.isCreateMode) {
        // 创建模式：返回空数据
        return {
          id: null,
          title: '',
          significance: '',
          criteria: '',
          problem_type: 'implementation'
        }
      } else {
        // 展示模式：从treeStore获取数据
        return this.treeStore?.getRootProblemPanelData(this.selectedNodeId) || {}
      }
    },

    // 是否可以编辑
    canEdit() {
      // 如果正在查看快照，不能编辑
      if (this.treeStore?.getIsViewingSnapshot) {
        return false
      }
      
      // 如果智能体正在操作，不能编辑
      if (this.treeStore?.getAgentOperatingNodeId) {
        return false
      }
      
      return true
    }
  },

  watch: {
    selectedNodeId: {
      handler(newId) {
        if (newId) {
          this.initPanelData()
        } else {
          this.resetPanelData()
        }
      },
      immediate: true
    }
  },

  mounted() {
    this.treeStore = useTreeStore()
    this.messageStore = useMessageStore()
  },

  methods: {
    // 初始化面板数据
    initPanelData() {
      if (this.isCreateMode) {
        // 创建模式：进入编辑状态
        this.isEditing = true
        this.localData = {
          title: '',
          significance: '',
          criteria: '',
          problem_type: 'implementation'
        }
      } else {
        // 展示模式
        this.isEditing = false
        this.updateLocalData(this.currentData)
      }
    },

    // 更新本地数据
    updateLocalData(data) {
      this.localData = {
        title: data.title || '',
        significance: data.significance || '',
        criteria: data.criteria || '',
        problem_type: data.problem_type || 'implementation'
      }
    },

    // 重置面板数据
    resetPanelData() {
      this.isEditing = false
      this.isSaving = false
      this.isDeleting = false
      this.localData = {
        title: '',
        significance: '',
        criteria: '',
        problem_type: 'implementation'
      }
      this.originalData = null
    },

    // 备份原始数据
    backupOriginalData() {
      this.originalData = { ...this.localData }
    },

    // 恢复原始数据
    restoreOriginalData() {
      if (this.originalData) {
        this.localData = { ...this.originalData }
      }
    },

    // 获取问题类型显示文本
    getProblemTypeText(type) {
      const typeMap = {
        implementation: '实施问题',
        conditional: '条件问题'
      }
      return typeMap[type] || '实施问题'
    },

    // 获取问题类型标签类型
    getProblemTypeTagType(type) {
      const typeMap = {
        implementation: 'primary',
        conditional: 'warning'
      }
      return typeMap[type] || 'primary'
    },

    // 验证数据
    validateData() {
      // 验证标题不能为空
      if (!this.localData.title.trim()) {
        ElMessage.error('根问题标题不能为空')
        return false
      }

      // 验证标题唯一性
      const excludeIds = this.isCreateMode ? [] : [this.selectedNodeId]
      if (this.treeStore?.getIsNodeTitleExists(this.localData.title.trim(), excludeIds)) {
        ElMessage.error('根问题标题已存在，请使用其他标题')
        return false
      }

      return true
    },

    // 进入编辑模式
    handleEdit() {
      if (!this.canEdit) return
      
      // 先用当前数据更新本地数据
      this.updateLocalData(this.currentData)
      this.backupOriginalData()
      this.isEditing = true
    },

    // 保存
    async handleSave() {
      if (!this.validateData()) return
      
      this.isSaving = true
      
      try {
        const problemData = {
          title: this.localData.title.trim(),
          significance: this.localData.significance.trim(),
          criteria: this.localData.criteria.trim(),
          problem_type: this.localData.problem_type
        }

        if (this.isCreateMode) {
          // 创建根问题
          await this.messageStore.createRootProblem(problemData)
          ElMessage.success('根问题创建成功')
          this.handleClose()
        } else {
          // 更新根问题
          await this.messageStore.updateRootProblem(this.selectedNodeId, problemData)
          ElMessage.success('根问题更新成功')
        }

        this.isEditing = false
        this.originalData = null

      } catch (error) {
        console.error('保存失败:', error)
        // 错误已在messageStore中处理，保持编辑状态
      } finally {
        this.isSaving = false
      }
    },

    // 取消编辑
    handleCancel() {
      this.restoreOriginalData()
      this.isEditing = false
      this.originalData = null
      if (this.isCreateMode) {
        this.handleClose()
      }
    },

    // 关闭面板
    handleClose() {
      this.$emit('close')
    },

    // 删除根问题
    async handleDelete() {
      if (!this.canEdit || this.isCreateMode) return
      
      // 确认删除
      const confirmed = await ElMessageBox.confirm(
        `确定要删除根问题"${this.currentData.title}"吗？`,
        '删除确认',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning',
          confirmButtonClass: 'el-button--danger'
        }
      ).catch(() => false)
      
      if (!confirmed) return
      
      this.isDeleting = true
      
      try {
        await this.messageStore.deleteRootProblem(this.selectedNodeId)
        ElMessage.success('根问题删除成功')
        this.handleClose() // 删除成功后关闭面板
        
      } catch (error) {
        console.error('删除失败:', error)
        // 错误已在messageStore中处理
      } finally {
        this.isDeleting = false
      }
    }
  }
}
</script>

<style scoped>
.root-problem-panel-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1100; /* 高层级确保在最上层 */
}

/* 背景遮罩 */
.overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5); /* 半透明黑色背景 */
  z-index: 1; /* 确保在面板下方 */
}

/* 面板主体 */
.root-problem-panel {
  position: relative;
  width: calc(100% - 120px); /* 左右各60px的边距 */
  height: calc(100% - 120px); /* 上下各60px的边距 */
  background: var(--bg-color, #ffffff);
  border: 1px solid var(--border-color, #dcdfe6);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2); /* 增强阴影效果 */
  display: flex;
  flex-direction: column;
  z-index: 2; /* 确保在遮罩上方 */
  max-width: 1200px; /* 限制最大宽度，根问题面板比解决方案面板稍窄 */
  margin: 0 auto; /* 水平居中 */
}

/* 头部 */
.panel-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color, #dcdfe6);
  background: var(--bg-color-light, #f5f7fa);
  border-radius: 12px 12px 0 0;
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: start;
  column-gap: 24px;
  row-gap: 8px;
}

.header-title {
  min-width: 0;
}

.title-input {
  font-size: 24px;
  font-weight: 600;
}

.title-text {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--text-color, #303133);
  word-break: break-word;
  overflow-wrap: anywhere;
  max-width: 100%;
}

.header-actions {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.status-section {
  display: flex;
  gap: 12px;
  align-items: center;
}

.status-tag,
.edit-mode-tag {
  font-weight: 600;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-left: 0;
}

/* 主内容区域 */
.panel-content {
  flex: 1;
  min-height: 0; /* 允许内容区在父 flex 容器中收缩，给头部让位 */
  display: grid;
  grid-template-columns: 1fr 1fr; /* 两列布局 */
  gap: 1px;
  background: var(--border-color, #dcdfe6);
  overflow: hidden;
}

.content-column {
  background: var(--bg-color, #ffffff);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.column-header {
  padding: 16px 20px;
  background: var(--bg-color-light, #f5f7fa);
  border-bottom: 1px solid var(--border-color, #dcdfe6);
  font-weight: 600;
  font-size: 16px;
  color: var(--text-color, #303133);
  text-align: center;
  flex-shrink: 0;
}

.column-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.content-textarea {
  width: 100%;
  resize: none;
}

.content-markdown {
  min-height: 100%;
  padding: 16px;
  border: 1px solid var(--border-color-light, #e4e7ed);
  border-radius: 8px;
  background: var(--bg-color-light, #f5f7fa);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .root-problem-panel {
    width: calc(100% - 40px); /* 左右各20px的边距 */
    height: calc(100% - 40px); /* 上下各20px的边距 */
  }
  
  .panel-header {
    padding: 16px 20px;
  }
  
  .header-actions {
    gap: 16px;
    flex-direction: column;
    align-items: stretch;
  }
  
  .action-buttons {
    margin-left: 0;
  }
  
  .panel-content {
    grid-template-columns: 1fr; /* 单列布局 */
  }
  
  .column-content {
    padding: 16px;
  }
}

/* 深色主题适配 */
:root[data-theme="dark"] .root-problem-panel {
  background: var(--bg-color-dark, #1d1d1d);
  border-color: var(--border-color-dark, #414243);
}

:root[data-theme="dark"] .panel-header {
  background: var(--bg-color-darker, #2d2d2d);
  border-color: var(--border-color-dark, #414243);
}

:root[data-theme="dark"] .content-column {
  background: var(--bg-color-dark, #1d1d1d);
}

:root[data-theme="dark"] .column-header {
  background: var(--bg-color-darker, #2d2d2d);
  border-color: var(--border-color-dark, #414243);
}

:root[data-theme="dark"] .content-markdown {
  background: var(--bg-color-darker, #2d2d2d);
  border-color: var(--border-color-dark, #414243);
}
</style>
