<template>
  <div class="solution-panel-container">
    <!-- 背景遮罩 -->
    <div class="overlay" @click.self="handleClose"></div>
    <!-- 面板主体 -->
    <div class="solution-panel">
      <!-- 头部 -->
      <div class="panel-header">
        <!-- 标题部分 -->
        <div class="header-title">
          <!-- 编辑模式：标题输入框 -->
          <el-input
            v-if="isEditing"
            v-model="localData.title"
            placeholder="请输入解决方案标题"
            class="title-input"
            size="large"
          />
          <!-- 展示模式：标题文本 -->
          <h2 v-else class="title-text">
            {{ currentData.title || '新建解决方案' }}
          </h2>
        </div>

        <!-- 状态和操作区域 -->
        <div class="header-actions">
          <!-- 状态显示 -->
          <div class="status-section">
            <el-tag 
              :type="getStatusTagType(currentData.state)" 
              size="large"
              class="status-tag"
            >
              {{ getStatusText(currentData.state) }}
            </el-tag>

            <!-- 编辑状态指示器 -->
            <el-tag 
              v-if="isEditing"
              :type="isCreateMode ? 'warning' : 'success'"
              size="large"
              class="edit-mode-tag"
            >
              {{ isCreateMode ? '新建中' : '编辑中' }}
            </el-tag>
          </div>

          <!-- 选中开关 -->
          <div class="selection-section" v-if="!isEditing && !isCreateSolution">
            <el-switch
              v-model="localSelected"
              @change="handleSelectionChange"
              active-text="已选中"
              inactive-text="未选中"
              :disabled="isEditing"
            />
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
                v-if="!isCreateSolution"
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
        <!-- 顶层思路 -->
        <div class="content-column">
          <div class="column-header">顶层思路</div>
          <div class="column-content">
            <!-- 编辑模式 -->
            <el-input
              v-if="isEditing"
              v-model="localData.top_level_thoughts"
              type="textarea"
              :rows="12"
              placeholder="请描述顶层思路"
              class="content-textarea"
            />
            <!-- 展示模式 -->
            <MarkdownRenderer
              v-else
              :content="currentData.top_level_thoughts || ''"
              class="content-markdown"
            />
          </div>
        </div>

        <!-- 研究计划（子问题列表） -->
        <div class="content-column research-plan-column">
          <div class="column-header">研究计划</div>
          <div class="column-content">
            <!-- 条件问题列表 -->
            <div class="problem-list-section">
              <div class="problem-list-header">
                <span class="section-title">条件问题</span>
                <el-button
                  v-if="isEditing"
                  size="small"
                  type="primary"
                  @click="addConditionalProblem"
                >
                  <el-icon><Plus /></el-icon>
                  添加条件问题
                </el-button>
              </div>
              <div class="problem-list">
                <ProblemElement
                  v-for="(problem, index) in conditionalProblems"
                  :key="problem.id || `conditional-${index}`"
                  :problem-data="problem"
                  :is-editable="isEditing"
                  :can-move-up="index > 0"
                  :can-move-down="index < conditionalProblems.length - 1"
                  @save="handleProblemSave(problem, $event)"
                  @move-up="handleProblemMoveUp(problem, 'conditional')"
                  @move-down="handleProblemMoveDown(problem, 'conditional')"
                  @delete="handleProblemDelete(problem, 'conditional')"
                />
                <div v-if="conditionalProblems.length === 0" class="empty-list">
                  暂无条件问题
                </div>
              </div>
            </div>

            <!-- 实施问题列表 -->
            <div class="problem-list-section">
              <div class="problem-list-header">
                <span class="section-title">实施问题</span>
                <el-button
                  v-if="isEditing"
                  size="small"
                  type="primary"
                  @click="addImplementationProblem"
                >
                  <el-icon><Plus /></el-icon>
                  添加实施问题
                </el-button>
              </div>
              <div class="problem-list">
                <ProblemElement
                  v-for="(problem, index) in implementationProblems"
                  :key="problem.id || `implementation-${index}`"
                  :problem-data="problem"
                  :is-editable="isEditing"
                  :can-move-up="index > 0"
                  :can-move-down="index < implementationProblems.length - 1"
                  @save="handleProblemSave(problem, $event)"
                  @move-up="handleProblemMoveUp(problem, 'implementation')"
                  @move-down="handleProblemMoveDown(problem, 'implementation')"
                  @delete="handleProblemDelete(problem, 'implementation')"
                />
                <div v-if="implementationProblems.length === 0" class="empty-list">
                  暂无实施问题
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 收尾工作计划 -->
        <div class="content-column">
          <div class="column-header">收尾工作计划</div>
          <div class="column-content">
            <!-- 编辑模式 -->
            <el-input
              v-if="isEditing"
              v-model="localData.implementation_plan"
              type="textarea"
              :rows="12"
              placeholder="请描述收尾工作计划"
              class="content-textarea"
            />
            <!-- 展示模式 -->
            <MarkdownRenderer
              v-else
              :content="currentData.implementation_plan || ''"
              class="content-markdown"
            />
          </div>
        </div>

        <!-- 可行性论证 -->
        <div class="content-column">
          <div class="column-header">可行性论证</div>
          <div class="column-content">
            <!-- 编辑模式 -->
            <el-input
              v-if="isEditing"
              v-model="localData.plan_justification"
              type="textarea"
              :rows="12"
              placeholder="请描述可行性论证"
              class="content-textarea"
            />
            <!-- 展示模式 -->
            <MarkdownRenderer
              v-else
              :content="currentData.plan_justification || ''"
              class="content-markdown"
            />
          </div>
        </div>
      </div>

      <!-- 消息输入区域 -->
      <div 
        v-if="!isEditing" 
        class="message-input-area"
      >
        <el-input
          v-model="messageContent"
          :placeholder="messagePlaceholder"
          @keyup.enter="handleSendMessage"
          :disabled="isSendingMessage || isMessageInputDisabled"
          class="chat-input"
        >
          <template #append>
            <el-button 
              type="primary" 
              circle 
              @click="handleSendMessage"
              :loading="isSendingMessage"
              :disabled="!messageContent.trim() || isMessageInputDisabled"
            >
              <el-icon><ChatSquare /></el-icon>
            </el-button>
          </template>
        </el-input>
      </div>
    </div>
  </div>
</template>

<script>
import { ElButton, ElInput, ElTag, ElSwitch, ElIcon, ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ChatSquare } from '@element-plus/icons-vue'
import MarkdownRenderer from '@/components/message/MarkdownRenderer.vue'
import ProblemElement from './ProblemElement.vue'
import { useTreeStore } from '@/stores/treeStore'
import { useMessageStore } from '@/stores/messageStore'

export default {
  name: 'SolutionPanel',

  components: {
    ElButton,
    ElInput,
    ElTag,
    ElSwitch,
    ElIcon,
    MarkdownRenderer,
    ProblemElement,
    Plus,
    ChatSquare
  },

  props: {
    // 选中的节点ID（解决方案ID或问题ID）
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
        top_level_thoughts: '',
        implementation_plan: '',
        plan_justification: '',
        state: 'in_progress'
      },
      
      // 本地子问题列表
      localChildren: [],
      
      // 选中状态
      localSelected: false,
      
      // 原始数据备份
      originalData: null,
      originalChildren: [],

      // 消息输入相关
      messageContent: '',
      isSendingMessage: false,
    }
  },

  computed: {
    // 当前节点类型
    currentNodeType() {
      if (!this.selectedNodeId) return null
      return this.treeStore?.getNodeType(this.selectedNodeId)
    },

    // 是否为创建解决方案模式（点击实施问题节点）
    isCreateSolution() {
      return this.currentNodeType === 'problem' && 
             this.treeStore?.getProblemNodeType(this.selectedNodeId) === 'implementation'
    },

    // 当前显示的数据
    currentData() {
      if (this.isCreateSolution) {
        // 创建模式：返回空数据
        return {
          id: null,
          title: '',
          top_level_thoughts: '',
          implementation_plan: '',
          plan_justification: '',
          state: 'in_progress',
          selected: false,
          children: [],
          parentProblemId: this.selectedNodeId
        }
      } else if (this.currentNodeType === 'solution') {
        // 展示解决方案
        return this.treeStore?.getSolutionPanelData(this.selectedNodeId) || {}
      }
      return {}
    },

    // 是否为新建模式
    isCreateMode() {
      if (this.isCreateSolution) return true
      
      // 检查子问题是否被修改
      return this.hasChildrenChanged()
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

      // 弃用节点不能编辑
      if (this.currentData.id && this.treeStore?.getIsNodeEnabled(this.currentData.id) !== true) {
        return false
      }
      
      return true
    },

    // 条件问题列表
    conditionalProblems() {
      return this.localChildren.filter(child => child.problem_type === 'conditional')
    },

    // 实施问题列表
    implementationProblems() {
      return this.localChildren.filter(child => child.problem_type === 'implementation')
    },

    // 消息输入框占位符
    messagePlaceholder() {
      if (!this.currentData.id) return '无法发送消息'
      return `向${this.treeStore?.getAgentNameByNodeId(this.currentData.id)}发送消息`
    },

    // 消息输入是否禁用
    isMessageInputDisabled() {
      // 如果当前节点没有ID，或者节点未启用，则禁用消息输入
      return !this.currentData.id || !this.canEdit;
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
    },

    currentData: {
      handler(newData) {
        if (newData && !this.isEditing) {
          this.updateLocalData(newData)
        }
      },
      deep: true
    }
  },

  mounted() {
    this.treeStore = useTreeStore()
    this.messageStore = useMessageStore()
    this.initPanelData()
  },

  methods: {
    // 初始化面板数据
    initPanelData() {
      if (this.isCreateSolution) {
        // 创建模式：进入编辑状态
        this.isEditing = true
        this.localData = {
          title: '',
          top_level_thoughts: '',
          implementation_plan: '',
          plan_justification: '',
          state: 'in_progress'
        }
        this.localChildren = []
        this.localSelected = false
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
        top_level_thoughts: data.top_level_thoughts || '',
        implementation_plan: data.implementation_plan || '',
        plan_justification: data.plan_justification || '',
        state: data.state || 'in_progress'
      }
      this.localChildren = [...(data.children || [])]
      this.localSelected = data.selected || false
    },

    // 重置面板数据
    resetPanelData() {
      this.isEditing = false
      this.isSaving = false
      this.isDeleting = false
      this.localData = {
        title: '',
        top_level_thoughts: '',
        implementation_plan: '',
        plan_justification: '',
        state: 'in_progress'
      }
      this.localChildren = []
      this.localSelected = false
      this.originalData = null
      this.originalChildren = []
    },

    // 备份原始数据
    backupOriginalData() {
      this.originalData = { ...this.localData }
      this.originalChildren = JSON.parse(JSON.stringify(this.localChildren))
    },

    // 恢复原始数据
    restoreOriginalData() {
      if (this.originalData) {
        this.localData = { ...this.originalData }
        this.localChildren = JSON.parse(JSON.stringify(this.originalChildren))
      }
    },

    // 检查子问题是否被修改
    hasChildrenChanged() {
      if (!this.originalChildren.length && !this.localChildren.length) {
        return false
      }
      
      if (this.originalChildren.length !== this.localChildren.length) {
        return true
      }
      
      for (let i = 0; i < this.originalChildren.length; i++) {
        const orig = this.originalChildren[i]
        const local = this.localChildren[i]
        
        if (local.id === null || orig.id !== local.id) {
          return true
        }
        
        if (orig.title !== local.title ||
            orig.significance !== local.significance ||
            orig.criteria !== local.criteria) {
          return true
        }
      }
      
      return false
    },

    // 获取状态显示文本
    getStatusText(state) {
      const statusMap = {
        success: '已成功',
        failure: '已失败', 
        in_progress: '进行中'
      }
      return statusMap[state] || '进行中'
    },

    // 获取状态标签类型
    getStatusTagType(state) {
      const typeMap = {
        success: 'success',
        failure: 'danger',
        in_progress: 'primary'
      }
      return typeMap[state] || 'primary'
    },

    // 验证数据
    validateData() {
      // 验证标题不能为空
      if (!this.localData.title.trim()) {
        ElMessage.error('解决方案标题不能为空')
        return false
      }

      // 验证标题唯一性
      const excludeIds = this.isCreateSolution ? [] : [this.selectedNodeId]
      if (this.treeStore?.getIsNodeTitleExists(this.localData.title.trim(), excludeIds)) {
        ElMessage.error('解决方案标题已存在，请使用其他标题')
        return false
      }

      // 验证子问题标题
      for (const child of this.localChildren) {
        if (!child.title.trim()) {
          ElMessage.error('问题标题不能为空')
          return false
        }
        
        const childExcludeIds = child.id ? [child.id] : []
        if (this.treeStore?.getIsNodeTitleExists(child.title.trim(), childExcludeIds)) {
          ElMessage.error(`问题标题"${child.title}"已存在，请使用其他标题`)
          return false
        }
      }

      return true
    },

    // 进入编辑模式
    handleEdit() {
      if (!this.canEdit) return
      
      this.backupOriginalData()
      this.isEditing = true
    },

    // 保存
    async handleSave() {
      if (!this.validateData()) return
      
      this.isSaving = true
      
      try {
        const solutionData = {
          title: this.localData.title.trim(),
          top_level_thoughts: this.localData.top_level_thoughts.trim(),
          implementation_plan: this.localData.implementation_plan.trim(),
          plan_justification: this.localData.plan_justification.trim(),
          state: this.localData.state,
          children: this.localChildren.map(child => ({
            ...child,
            title: child.title.trim(),
            significance: child.significance.trim(),
            criteria: child.criteria.trim()
          }))
        }

        if (this.isCreateSolution) {
          // 创建解决方案
          await this.messageStore.createSolution(this.selectedNodeId, solutionData)
          ElMessage.success('解决方案创建成功')
        } else if (this.isCreateMode) {
          // 重新创建解决方案
          await this.messageStore.createSolution(this.currentData.parentProblemId, solutionData)
          ElMessage.success('解决方案更新成功')
        } else {
          // 更新解决方案（不包含子问题）
          // eslint-disable-next-line no-unused-vars
          const { children, ...updateData } = solutionData
          await this.messageStore.updateSolution(this.selectedNodeId, updateData)
          ElMessage.success('解决方案更新成功')
        }

        this.isEditing = false
        this.originalData = null
        this.originalChildren = []
        if (this.isCreateSolution) {
          this.handleClose()
        }
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
      this.originalChildren = []
      if (this.isCreateSolution) {
        this.handleClose()
      }
    },

    // 关闭面板
    handleClose() {
      this.$emit('close')
    },

    // 删除解决方案
    async handleDelete() {
      if (!this.canEdit || this.isCreateSolution) return
      
      // 确认删除
      const confirmed = await ElMessageBox.confirm(
        `确定要删除解决方案"${this.currentData.title}"吗？`,
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
        await this.messageStore.deleteSolution(this.selectedNodeId)
        ElMessage.success('解决方案删除成功')
        this.handleClose() // 删除成功后关闭面板
        
      } catch (error) {
        console.error('删除失败:', error)
        // 错误已在messageStore中处理
      } finally {
        this.isDeleting = false
      }
    },

    // 处理选中状态变化
    async handleSelectionChange(selected) {
      try {
        await this.messageStore.setSelectedSolution(
          this.currentData.parentProblemId,
          selected ? this.selectedNodeId : null
        )
        ElMessage.success(selected ? '已设置为选中方案' : '已取消选中')
      } catch (error) {
        console.error('更新选中状态失败:', error)
        // 恢复原状态
        this.localSelected = !selected
      }
    },

    // 添加条件问题
    addConditionalProblem() {
      const newProblem = {
        id: null,
        title: '未命名条件问题',
        significance: '',
        criteria: '',
        problem_type: 'conditional'
      }
      // 找到第一个实施问题的位置，将条件问题插入到它之前
      const firstImplementationIndex = this.localChildren.findIndex(p => p.problem_type === 'implementation')
      if (firstImplementationIndex !== -1) {
        this.localChildren.splice(firstImplementationIndex, 0, newProblem)
      } else {
        // 如果没有实施问题，直接添加到列表末尾
        this.localChildren.push(newProblem)
      }
    },

    // 添加实施问题
    addImplementationProblem() {
      const newProblem = {
        id: null,
        title: '未命名实施问题',
        significance: '',
        criteria: '',
        problem_type: 'implementation'
      }
      // 实施问题直接添加到列表末尾
      this.localChildren.push(newProblem)
    },

    // 处理问题保存
    handleProblemSave(originalProblem, editedProblem) {
      const index = this.localChildren.findIndex(p => p === originalProblem)
      if (index !== -1) {
        // 如果问题被编辑过，设置id为null
        this.localChildren[index] = {
          ...editedProblem,
          id: null // 标记为已修改
        }
      }
    },

    // 处理问题向上移动
    handleProblemMoveUp(problem, type) {
      const list = type === 'conditional' ? this.conditionalProblems : this.implementationProblems
      const listIndex = list.findIndex(p => p === problem)
      const globalIndex = this.localChildren.findIndex(p => p === problem)
      
      if (listIndex > 0 && globalIndex > 0) {
        // 在同类型列表中向上移动
        const prevProblem = list[listIndex - 1]
        const prevGlobalIndex = this.localChildren.findIndex(p => p === prevProblem)
        
        // 交换位置
        const temp = this.localChildren[globalIndex]
        this.localChildren[globalIndex] = this.localChildren[prevGlobalIndex]
        this.localChildren[prevGlobalIndex] = temp
      }
    },

    // 处理问题向下移动
    handleProblemMoveDown(problem, type) {
      const list = type === 'conditional' ? this.conditionalProblems : this.implementationProblems
      const listIndex = list.findIndex(p => p === problem)
      const globalIndex = this.localChildren.findIndex(p => p === problem)
      
      if (listIndex < list.length - 1 && globalIndex < this.localChildren.length - 1) {
        // 在同类型列表中向下移动
        const nextProblem = list[listIndex + 1]
        const nextGlobalIndex = this.localChildren.findIndex(p => p === nextProblem)
        
        // 交换位置
        const temp = this.localChildren[globalIndex]
        this.localChildren[globalIndex] = this.localChildren[nextGlobalIndex]
        this.localChildren[nextGlobalIndex] = temp
      }
    },

    // 处理问题删除
    // eslint-disable-next-line no-unused-vars
    handleProblemDelete(problem, type) {
      const index = this.localChildren.findIndex(p => p === problem)
      if (index !== -1) {
        this.localChildren.splice(index, 1)
      }
    },

    // 发送消息
    async handleSendMessage() {
      if (!this.messageContent.trim() || this.isSendingMessage) {
        ElMessage.warning('请输入消息内容')
        return
      }

      this.isSendingMessage = true // 发送前短暂设置为true，禁用按钮
      try {
        await this.messageStore.sendMessage(
          this.messageContent.trim(),
          "用户消息",
          "user_chat_agent",
          { solution_id: this.currentData.id }
        )
        ElMessage.success('消息发送成功')
        this.handleClose() // 发送前关闭面板
      } catch (error) {
        console.error('发送消息失败:', error)
        ElMessage.error('发送消息失败')
      }
    }
  }
}
</script>

<style scoped>
.solution-panel-container {
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
.solution-panel {
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
  max-width: 1800px; /* 限制最大宽度，避免在超大屏幕上过宽 */
  margin: 0 auto; /* 水平居中 */
}

/* 头部 */
.panel-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color, #dcdfe6);
  background: var(--bg-color-light, #f5f7fa);
  border-radius: 12px 12px 0 0;
  /* 标题与操作区域并排，标题区域可换行时自动增高 */
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: start;
  column-gap: 24px;
  row-gap: 8px;
}

.header-title {
  /* 限制标题列在栅格中可收缩，避免挤压右侧控件 */
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
  /* 长中文/连续字符也能优雅换行，撑高头部不溢出 */
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

.selection-section {
  display: flex;
  align-items: center;
}

.action-buttons {
  display: flex;
  gap: 12px;
  /* 栅格布局下不再需要自动占位推到右侧 */
  margin-left: 0;
}

/* 消息输入区域 */
.message-input-area {
  padding: 16px 24px;
  border-top: 1px solid var(--border-color, #dcdfe6);
  background: var(--bg-color-light, #f5f7fa);
  border-radius: 0 0 12px 12px;
  flex-shrink: 0; /* 防止被压缩 */
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-input {
  flex: 1;
}

.el-button.is-circle {
  border-radius: 50%;
  padding: 8px; /* Adjust padding for circular button */
}

/* 主内容区域 */
.panel-content {
  flex: 1;
  min-height: 0; /* 允许内容区在父 flex 容器中收缩，给头部让位 */
  display: grid;
  grid-template-columns: 1fr 1.2fr 1fr 1fr;
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

.research-plan-column {
  background: var(--bg-color-light, #f5f7fa);
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

.research-plan-column .column-header {
  background: var(--bg-color, #ffffff);
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

/* 子问题列表 */
.problem-list-section {
  margin-bottom: 24px;
}

.problem-list-section:last-child {
  margin-bottom: 0;
}

.problem-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color, #dcdfe6);
}

.section-title {
  font-weight: 600;
  font-size: 16px;
  color: var(--text-color, #303133);
}

.problem-list {
  max-height: 300px;
  overflow-y: auto;
}

.empty-list {
  text-align: center;
  color: var(--text-color-secondary, #909399);
  padding: 40px 20px;
  font-style: italic;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .panel-content {
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
  }
  
  .research-plan-column {
    grid-column: 1 / -1;
    grid-row: 2;
  }
}

@media (max-width: 768px) {
  .solution-panel {
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
    grid-template-columns: 1fr;
  }
  
  .column-content {
    padding: 16px;
  }
}

/* 深色主题适配 */
:root[data-theme="dark"] .solution-panel {
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

:root[data-theme="dark"] .research-plan-column {
  background: var(--bg-color-darker, #2d2d2d);
}

:root[data-theme="dark"] .column-header {
  background: var(--bg-color-darker, #2d2d2d);
  border-color: var(--border-color-dark, #414243);
}

:root[data-theme="dark"] .research-plan-column .column-header {
  background: var(--bg-color-dark, #1d1d1d);
}

:root[data-theme="dark"] .content-markdown {
  background: var(--bg-color-darker, #2d2d2d);
  border-color: var(--border-color-dark, #414243);
}

:root[data-theme="dark"] .message-input-area {
  background: var(--bg-color-darker, #2d2d2d);
  border-color: var(--border-color-dark, #414243);
}
</style>
