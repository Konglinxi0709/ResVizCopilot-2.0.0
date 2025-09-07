<template>
  <div class="problem-element">
    <!-- 主标题栏 -->
    <div class="problem-header" @click="handleHeaderClick">
      <!-- 状态指示器 -->
      <div class="status-indicator">
        <div 
          class="status-dot" 
          :class="{ 'status-modified': isModified }"
          :title="isModified ? '已修改' : '未修改'"
        ></div>
      </div>

      <!-- 标题内容 -->
      <div class="title-container" :class="{ 'editing': isEditingLocal }">
        <!-- 编辑模式：输入框 -->
        <el-input
          v-if="isEditingLocal"
          v-model="localTitle"
          placeholder="请输入问题标题"
          class="title-input"
          @keydown.enter="handleSave"
          @keydown.esc="handleCancel"
          ref="titleInput"
        />
        <!-- 展示模式：标题文本 -->
        <div v-else class="title-text">
          {{ problemData.title || '未命名' }}
        </div>
      </div>

      <!-- 操作按钮组 -->
      <div class="action-buttons">
        <!-- 编辑模式按钮 -->
        <template v-if="isEditingLocal">
          <el-button
            type="primary"
            size="small"
            @click.stop="handleSave"
            title="保存"
          >
            <el-icon><Check /></el-icon>
          </el-button>
          <el-button
            size="small"
            @click.stop="handleCancel"
            title="取消"
          >
            <el-icon><Close /></el-icon>
          </el-button>
        </template>
        
        <!-- 可编辑但未进入编辑模式 -->
        <template v-else-if="isEditable && !isEditingLocal">
          <el-button
            size="small"
            @click.stop="handleEdit"
            title="编辑"
          >
            <el-icon><Edit /></el-icon>
          </el-button>
          <el-button
            size="small"
            @click.stop="handleMoveUp"
            title="向上移动"
            :disabled="!canMoveUp"
          >
            <el-icon><ArrowUp /></el-icon>
          </el-button>
          <el-button
            size="small"
            @click.stop="handleMoveDown" 
            title="向下移动"
            :disabled="!canMoveDown"
          >
            <el-icon><ArrowDown /></el-icon>
          </el-button>
          <el-button
            size="small"
            @click.stop="handleDelete"
            title="删除"
            type="danger"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </template>
      </div>

      <!-- 展开/折叠按钮 -->
      <el-button
        size="small"
        @click.stop="toggleExpanded"
        title="展开/折叠"
        class="expand-button"
      >
        <el-icon>
          <ArrowUp v-if="isExpanded" />
          <ArrowDown v-else />
        </el-icon>
      </el-button>
    </div>

    <!-- 折叠内容区域 -->
    <div v-if="isExpanded" class="problem-content">
      <!-- 重要性部分 -->
      <div class="content-section">
        <div class="section-label">重要性</div>
        <div class="section-content">
          <!-- 编辑模式：文本框 -->
          <el-input
            v-if="isEditingLocal"
            v-model="localSignificance"
            type="textarea"
            :rows="3"
            placeholder="请描述问题的重要性"
            class="content-textarea"
          />
          <!-- 展示模式：Markdown渲染 -->
          <MarkdownRenderer
            v-else
            :content="problemData.significance || ''"
            class="content-markdown"
          />
        </div>
      </div>

      <!-- 评判标准部分 -->
      <div class="content-section">
        <div class="section-label">评判标准</div>
        <div class="section-content">
          <!-- 编辑模式：文本框 -->
          <el-input
            v-if="isEditingLocal"
            v-model="localCriteria"
            type="textarea"
            :rows="3"
            placeholder="请描述评判标准"
            class="content-textarea"
          />
          <!-- 展示模式：Markdown渲染 -->
          <MarkdownRenderer
            v-else
            :content="problemData.criteria || ''"
            class="content-markdown"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ElButton, ElInput, ElIcon } from 'element-plus'
import { 
  Edit, 
  Check, 
  Close, 
  ArrowUp, 
  ArrowDown, 
  Delete 
} from '@element-plus/icons-vue'
import MarkdownRenderer from '@/components/message/MarkdownRenderer.vue'

export default {
  name: 'ProblemElement',
  
  components: {
    ElButton,
    ElInput,
    ElIcon,
    MarkdownRenderer,
    Edit,
    Check,
    Close,
    ArrowUp,
    ArrowDown,
    Delete
  },

  props: {
    // 问题数据
    problemData: {
      type: Object,
      required: true,
      default: () => ({
        id: null,
        title: '',
        significance: '',
        criteria: '',
        problem_type: 'implementation'
      })
    },
    
    // 是否可编辑
    isEditable: {
      type: Boolean,
      default: true
    },
    
    // 是否可以向上移动
    canMoveUp: {
      type: Boolean,
      default: true
    },
    
    // 是否可以向下移动
    canMoveDown: {
      type: Boolean,
      default: true
    },
    
    // 初始展开状态
    initialExpanded: {
      type: Boolean,
      default: false
    }
  },

  emits: [
    'edit',      // 进入编辑模式
    'save',      // 保存修改
    'cancel',    // 取消编辑
    'move-up',   // 向上移动
    'move-down', // 向下移动
    'delete'     // 删除
  ],

  data() {
    return {
      // 是否展开
      isExpanded: this.initialExpanded,
      
      // 是否正在编辑
      isEditingLocal: false,
      
      // 本地编辑数据
      localTitle: '',
      localSignificance: '',
      localCriteria: '',
      
      // 原始数据备份
      originalData: null
    }
  },

  computed: {
    // 是否被修改过（id为null表示新建或已修改）
    isModified() {
      return this.problemData.id === null
    }
  },

  watch: {
    // 监听外部数据变化，更新本地数据
    problemData: {
      handler(newData) {
        if (!this.isEditingLocal) {
          this.updateLocalData(newData)
        }
      },
      deep: true,
      immediate: true
    }
  },

  methods: {
    // 更新本地数据
    updateLocalData(data) {
      this.localTitle = data.title || ''
      this.localSignificance = data.significance || ''
      this.localCriteria = data.criteria || ''
    },

    // 备份原始数据
    backupOriginalData() {
      this.originalData = {
        title: this.localTitle,
        significance: this.localSignificance,
        criteria: this.localCriteria
      }
    },

    // 恢复原始数据
    restoreOriginalData() {
      if (this.originalData) {
        this.localTitle = this.originalData.title
        this.localSignificance = this.originalData.significance
        this.localCriteria = this.originalData.criteria
      }
    },

    // 切换展开/折叠状态
    toggleExpanded() {
      this.isExpanded = !this.isExpanded
    },

    // 处理标题栏点击
    handleHeaderClick() {
      if (!this.isEditingLocal) {
        this.toggleExpanded()
      }
    },

    // 进入编辑模式
    handleEdit() {
      if (!this.isEditable) return
      
      this.backupOriginalData()
      this.isEditingLocal = true
      this.isExpanded = true // 编辑时自动展开
      
      // 聚焦到标题输入框
      this.$nextTick(() => {
        if (this.$refs.titleInput) {
          this.$refs.titleInput.focus()
        }
      })
      
      this.$emit('edit', this.problemData)
    },

    // 保存编辑
    handleSave() {
      if (!this.isEditingLocal) return

      // 验证标题不能为空
      if (!this.localTitle.trim()) {
        this.$message.error('问题标题不能为空')
        return
      }

      const editedData = {
        ...this.problemData,
        title: this.localTitle.trim(),
        significance: this.localSignificance.trim(),
        criteria: this.localCriteria.trim()
      }

      this.isEditingLocal = false
      this.originalData = null
      
      this.$emit('save', editedData)
    },

    // 取消编辑
    handleCancel() {
      if (!this.isEditingLocal) return
      
      this.restoreOriginalData()
      this.isEditingLocal = false
      this.originalData = null
      
      this.$emit('cancel', this.problemData)
    },

    // 向上移动
    handleMoveUp() {
      if (!this.canMoveUp) return
      this.$emit('move-up', this.problemData)
    },

    // 向下移动
    handleMoveDown() {
      if (!this.canMoveDown) return
      this.$emit('move-down', this.problemData)
    },

    // 删除
    handleDelete() {
      this.$emit('delete', this.problemData)
    }
  }
}
</script>

<style scoped>
.problem-element {
  border: 1px solid var(--border-color, #dcdfe6);
  border-radius: 8px;
  margin-bottom: 12px;
  background: var(--bg-color, #ffffff);
  transition: all 0.3s ease;
}

.problem-element:hover {
  border-color: var(--primary-color, #409eff);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

/* 标题栏 */
.problem-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  user-select: none;
  transition: background-color 0.3s ease;
}

.problem-header:hover {
  background: var(--bg-color-light, #f5f7fa);
}

/* 状态指示器 */
.status-indicator {
  margin-right: 12px;
  flex-shrink: 0;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #67c23a; /* 绿色 - 未修改 */
  transition: background-color 0.3s ease;
}

.status-dot.status-modified {
  background: #e6a23c; /* 橙色 - 已修改 */
}

/* 标题容器 */
.title-container {
  flex: 1;
  min-width: 0;
}

.title-container.editing {
  cursor: default;
}

.title-input {
  width: 100%;
}

.title-text {
  font-weight: 500;
  color: var(--text-color, #303133);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 操作按钮组 */
.action-buttons {
  display: flex;
  gap: 6px;
  margin-left: 12px;
  flex-shrink: 0;
}

.action-buttons .el-button {
  padding: 4px 8px;
  min-width: auto;
}

/* 展开按钮 */
.expand-button {
  margin-left: 8px;
  padding: 4px 8px;
  min-width: auto;
  flex-shrink: 0;
}

/* 折叠内容区域 */
.problem-content {
  border-top: 1px solid var(--border-color, #dcdfe6);
  padding: 16px;
  background: var(--bg-color-light, #f5f7fa);
}

/* 内容部分 */
.content-section {
  margin-bottom: 16px;
}

.content-section:last-child {
  margin-bottom: 0;
}

.section-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color-secondary, #606266);
  margin-bottom: 8px;
}

.section-content {
  max-height: 200px;
  overflow-y: auto;
}

.content-textarea {
  width: 100%;
}

.content-markdown {
  min-height: 40px;
  padding: 8px 12px;
  border: 1px solid var(--border-color-light, #e4e7ed);
  border-radius: 4px;
  background: var(--bg-color, #ffffff);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .problem-header {
    padding: 10px 12px;
  }
  
  .action-buttons {
    gap: 4px;
  }
  
  .action-buttons .el-button {
    padding: 2px 6px;
  }
  
  .problem-content {
    padding: 12px;
  }
  
  .section-content {
    max-height: 150px;
  }
}

/* 深色主题适配 */
:root[data-theme="dark"] .problem-element {
  background: var(--bg-color-dark, #1d1d1d);
  border-color: var(--border-color-dark, #414243);
}

:root[data-theme="dark"] .problem-header:hover {
  background: var(--bg-color-darker, #2d2d2d);
}

:root[data-theme="dark"] .problem-content {
  background: var(--bg-color-darker, #2d2d2d);
  border-color: var(--border-color-dark, #414243);
}

:root[data-theme="dark"] .content-markdown {
  background: var(--bg-color-dark, #1d1d1d);
  border-color: var(--border-color-dark, #414243);
}
</style>
