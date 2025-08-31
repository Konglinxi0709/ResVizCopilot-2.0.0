<template>
  <div class="node-selector" v-if="shouldShowSelector">
    <div class="selector-header">
      <el-icon><Operation /></el-icon>
      <span class="header-text">{{ selectorTitle }}</span>
      <el-tag v-if="filteredNodes.length > 0" type="info" size="small">
        {{ filteredNodes.length }} 个可选
      </el-tag>
    </div>
    
    <!-- 无可选节点提示 -->
    <div v-if="filteredNodes.length === 0" class="no-nodes-tip">
      <el-icon size="32" color="#C0C4CC"><Warning /></el-icon>
      <div class="tip-content">
        <h4>{{ noNodesTitle }}</h4>
        <p>{{ noNodesMessage }}</p>
        <el-button 
          v-if="canCreateNode" 
          type="primary" 
          size="small"
          @click="handleCreateNode"
        >
          {{ createNodeText }}
        </el-button>
      </div>
    </div>
    
    <!-- 节点选择 -->
    <el-select
      v-else
      v-model="selectedNode"
      :placeholder="selectPlaceholder"
      size="large"
      class="node-select"
      :disabled="disabled"
      @change="handleNodeChange"
      filterable
      :filter-method="filterNodes"
    >
      <el-option
        v-for="node in displayNodes"
        :key="node.id"
        :label="node.title"
        :value="node.id"
        :disabled="node.disabled"
      >
        <div class="node-option">
          <div class="option-header">
            <el-icon class="node-icon" :style="{ color: getNodeColor(node) }">
              <component :is="getNodeIcon(node)" />
            </el-icon>
            <span class="node-title">{{ truncateTitle(node.title, 30) }}</span>
            <div class="node-badges">
              <el-tag 
                :type="getNodeTypeTagType(node)" 
                size="small"
                class="type-tag"
              >
                {{ getNodeTypeText(node) }}
              </el-tag>
              <el-tag 
                v-if="node.state" 
                :type="getStateTagType(node.state)" 
                size="small"
              >
                {{ getStateText(node.state) }}
              </el-tag>
            </div>
          </div>
          
          <div v-if="node.significance" class="node-significance">
            <el-icon><InfoFilled /></el-icon>
            <span>{{ truncateTitle(node.significance, 50) }}</span>
          </div>
          
          <div v-if="node.top_level_thoughts" class="node-thoughts">
            <el-icon><StarFilled /></el-icon>
            <span>{{ truncateTitle(node.top_level_thoughts, 50) }}</span>
          </div>
          
          <div class="node-path">
            <el-icon><Share /></el-icon>
            <span>{{ getNodePath(node) }}</span>
          </div>
        </div>
      </el-option>
    </el-select>
    
    <!-- 选中节点信息 -->
    <transition name="fade">
      <div v-if="selectedNodeInfo" class="selected-node-info">
        <div class="info-header">
          <el-icon class="info-icon" :style="{ color: getNodeColor(selectedNodeInfo) }">
            <component :is="getNodeIcon(selectedNodeInfo)" />
          </el-icon>
          <span class="info-title">{{ selectedNodeInfo.title }}</span>
          <div class="info-badges">
            <el-tag 
              :type="getNodeTypeTagType(selectedNodeInfo)" 
              size="small"
            >
              {{ getNodeTypeText(selectedNodeInfo) }}
            </el-tag>
            <el-tag 
              v-if="selectedNodeInfo.state" 
              :type="getStateTagType(selectedNodeInfo.state)" 
              size="small"
            >
              {{ getStateText(selectedNodeInfo.state) }}
            </el-tag>
          </div>
        </div>
        
        <div class="info-content">
          <div v-if="selectedNodeInfo.significance" class="info-section">
            <h4>研究意义：</h4>
            <p>{{ selectedNodeInfo.significance }}</p>
          </div>
          
          <div v-if="selectedNodeInfo.criteria" class="info-section">
            <h4>验收标准：</h4>
            <p>{{ selectedNodeInfo.criteria }}</p>
          </div>
          
          <div v-if="selectedNodeInfo.top_level_thoughts" class="info-section">
            <h4>核心思路：</h4>
            <p>{{ selectedNodeInfo.top_level_thoughts }}</p>
          </div>
          
          <div v-if="selectedNodeInfo.finishing_task" class="info-section">
            <h4>完成任务：</h4>
            <p>{{ selectedNodeInfo.finishing_task }}</p>
          </div>
          
          <div v-if="selectedNodeInfo.children && selectedNodeInfo.children.length > 0" class="info-section">
            <h4>子节点：</h4>
            <div class="child-nodes">
              <el-tag 
                v-for="child in selectedNodeInfo.children.slice(0, 3)"
                :key="child.id"
                size="small"
                type="info"
              >
                {{ truncateTitle(child.title, 20) }}
              </el-tag>
              <span v-if="selectedNodeInfo.children.length > 3" class="more-children">
                +{{ selectedNodeInfo.children.length - 3 }} 个
              </span>
            </div>
          </div>
          
          <div class="info-section">
            <h4>节点路径：</h4>
            <p class="node-path-full">{{ getNodePath(selectedNodeInfo) }}</p>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { defineComponent, ref, computed, watch } from 'vue'
import { 
  Operation, Warning, InfoFilled, StarFilled, Share,
  QuestionFilled, Cpu, Check 
} from '@element-plus/icons-vue'

export default defineComponent({
  name: 'NodeSelector',
  
  components: {
    Operation, Warning, InfoFilled, StarFilled, Share,
    QuestionFilled, Cpu, Check
  },
  
  props: {
    // 选中的节点ID
    modelValue: {
      type: String,
      default: ''
    },
    
    // 智能体类型
    agentType: {
      type: String,
      default: ''
    },
    
    // 可用的节点列表
    availableNodes: {
      type: Array,
      default: () => []
    },
    
    // 是否禁用
    disabled: {
      type: Boolean,
      default: false
    }
  },
  
  emits: ['update:modelValue', 'node-changed'],
  
  setup(props, { emit }) {
    const selectedNode = ref(props.modelValue)
    const searchFilter = ref('')
    
    // 智能体配置
    const agentNodeConfigs = {
      'auto_research_agent': {
        nodeType: 'problem',
        nodeFilter: (node) => node.type === 'problem' && node.problem_type === 'implementation',
        title: '选择实施问题',
        placeholder: '请选择要自动生成解决方案的实施问题',
        noNodesTitle: '暂无可用的实施问题',
        noNodesMessage: '自动研究智能体需要实施类型的问题节点，请先创建一个实施问题。',
        canCreateNode: true,
        createNodeText: '创建实施问题'
      },
      'user_chat_agent': {
        nodeType: 'solution',
        nodeFilter: (node) => node.type === 'solution',
        title: '选择解决方案',
        placeholder: '请选择要对话的解决方案节点',
        noNodesTitle: '暂无可用的解决方案',
        noNodesMessage: '用户对话智能体需要解决方案节点，请先生成一些解决方案。',
        canCreateNode: false,
        createNodeText: '生成解决方案'
      }
    }
    
    // 当前智能体配置
    const currentConfig = computed(() => {
      return agentNodeConfigs[props.agentType] || {
        nodeType: 'any',
        nodeFilter: () => true,
        title: '选择节点',
        placeholder: '请选择节点',
        noNodesTitle: '暂无可用节点',
        noNodesMessage: '当前没有可用的节点。',
        canCreateNode: false,
        createNodeText: '创建节点'
      }
    })
    
    // 是否显示选择器
    const shouldShowSelector = computed(() => {
      return props.agentType && agentNodeConfigs[props.agentType]
    })
    
    // 过滤的节点列表
    const filteredNodes = computed(() => {
      if (!props.availableNodes || props.availableNodes.length === 0) {
        return []
      }
      
      return props.availableNodes.filter(node => {
        return currentConfig.value.nodeFilter(node)
      })
    })
    
    // 显示的节点（应用搜索过滤）
    const displayNodes = computed(() => {
      if (!searchFilter.value) {
        return filteredNodes.value
      }
      
      const filter = searchFilter.value.toLowerCase()
      return filteredNodes.value.filter(node => {
        return (
          node.title.toLowerCase().includes(filter) ||
          (node.significance && node.significance.toLowerCase().includes(filter)) ||
          (node.top_level_thoughts && node.top_level_thoughts.toLowerCase().includes(filter))
        )
      })
    })
    
    // 选中的节点信息
    const selectedNodeInfo = computed(() => {
      if (!selectedNode.value) return null
      return findNodeById(props.availableNodes, selectedNode.value)
    })
    
    // 计算属性：各种显示文本
    const selectorTitle = computed(() => currentConfig.value.title)
    const selectPlaceholder = computed(() => currentConfig.value.placeholder)
    const noNodesTitle = computed(() => currentConfig.value.noNodesTitle)
    const noNodesMessage = computed(() => currentConfig.value.noNodesMessage)
    const canCreateNode = computed(() => currentConfig.value.canCreateNode)
    const createNodeText = computed(() => currentConfig.value.createNodeText)
    
    // 根据ID查找节点
    const findNodeById = (nodes, nodeId) => {
      for (const node of nodes) {
        if (node.id === nodeId) {
          return node
        }
        if (node.children) {
          const found = findNodeById(node.children, nodeId)
          if (found) return found
        }
      }
      return null
    }
    
    // 获取节点路径
    const getNodePath = (node) => {
      // 这里简化实现，实际应该从根节点开始构建路径
      const parentPath = getNodeParentPath(props.availableNodes, node.id)
      return parentPath.length > 0 ? parentPath.join(' > ') : '根节点'
    }
    
    // 获取节点父路径
    const getNodeParentPath = (nodes, targetId, currentPath = []) => {
      for (const node of nodes) {
        const newPath = [...currentPath, node.title]
        
        if (node.id === targetId) {
          return currentPath // 返回父路径，不包含自己
        }
        
        if (node.children) {
          const result = getNodeParentPath(node.children, targetId, newPath)
          if (result.length > 0) {
            return result
          }
        }
      }
      return []
    }
    
    // 获取节点图标
    const getNodeIcon = (node) => {
      if (node.type === 'problem') {
        return 'QuestionFilled'
      } else if (node.type === 'solution') {
        return 'Cpu'
      }
      return 'Check'
    }
    
    // 获取节点颜色
    const getNodeColor = (node) => {
      if (node.type === 'problem') {
        return node.problem_type === 'implementation' ? '#409eff' : '#e6a23c'
      } else if (node.type === 'solution') {
        switch (node.state) {
          case 'in_progress': return '#e6a23c'
          case 'completed': return '#67c23a'
          case 'failed': return '#f56c6c'
          default: return '#909399'
        }
      }
      return '#909399'
    }
    
    // 获取节点类型文本
    const getNodeTypeText = (node) => {
      if (node.type === 'problem') {
        return node.problem_type === 'implementation' ? '实施问题' : '条件问题'
      } else if (node.type === 'solution') {
        return '解决方案'
      }
      return '未知'
    }
    
    // 获取节点类型标签类型
    const getNodeTypeTagType = (node) => {
      if (node.type === 'problem') {
        return node.problem_type === 'implementation' ? 'primary' : 'warning'
      } else if (node.type === 'solution') {
        return 'success'
      }
      return 'info'
    }
    
    // 获取状态文本
    const getStateText = (state) => {
      switch (state) {
        case 'pending': return '待处理'
        case 'in_progress': return '进行中'
        case 'completed': return '已完成'
        case 'failed': return '失败'
        default: return state
      }
    }
    
    // 获取状态标签类型
    const getStateTagType = (state) => {
      switch (state) {
        case 'pending': return 'info'
        case 'in_progress': return 'warning'
        case 'completed': return 'success'
        case 'failed': return 'danger'
        default: return 'info'
      }
    }
    
    // 截断标题
    const truncateTitle = (title, maxLength) => {
      if (!title) return ''
      return title.length > maxLength ? title.slice(0, maxLength) + '...' : title
    }
    
    // 搜索过滤
    const filterNodes = (query) => {
      searchFilter.value = query
    }
    
    // 处理节点变化
    const handleNodeChange = (value) => {
      selectedNode.value = value
      emit('update:modelValue', value)
      
      const nodeInfo = findNodeById(props.availableNodes, value)
      emit('node-changed', nodeInfo)
    }
    
    // 处理创建节点
    const handleCreateNode = () => {
      // 这里应该触发创建节点的操作
      console.log('创建节点:', currentConfig.value.nodeType)
      // emit('create-node', currentConfig.value.nodeType)
    }
    
    // 监听外部变化
    watch(() => props.modelValue, (newValue) => {
      selectedNode.value = newValue
    })
    
    // 监听智能体类型变化，重置选择
    watch(() => props.agentType, () => {
      selectedNode.value = ''
      emit('update:modelValue', '')
    })
    
    return {
      selectedNode,
      shouldShowSelector,
      filteredNodes,
      displayNodes,
      selectedNodeInfo,
      selectorTitle,
      selectPlaceholder,
      noNodesTitle,
      noNodesMessage,
      canCreateNode,
      createNodeText,
      getNodeIcon,
      getNodeColor,
      getNodeTypeText,
      getNodeTypeTagType,
      getStateText,
      getStateTagType,
      getNodePath,
      truncateTitle,
      filterNodes,
      handleNodeChange,
      handleCreateNode
    }
  }
})
</script>

<style scoped>
.node-selector {
  margin-bottom: 16px;
}

.selector-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 500;
  color: var(--text-color);
}

.header-text {
  font-size: 14px;
  flex: 1;
}

.node-select {
  width: 100%;
}

/* 无节点提示 */
.no-nodes-tip {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--bg-color-light, #f8f9fa);
  border: 2px dashed var(--border-color);
  border-radius: 8px;
  text-align: left;
}

.tip-content h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color);
}

.tip-content p {
  margin: 0 0 12px 0;
  font-size: 13px;
  color: var(--text-color);
  opacity: 0.8;
  line-height: 1.4;
}

/* 节点选项样式 */
.node-option {
  padding: 8px 0;
}

.option-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.node-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.node-title {
  font-weight: 500;
  color: var(--text-color);
  flex: 1;
}

.node-badges {
  display: flex;
  gap: 4px;
}

.type-tag {
  font-size: 11px;
}

.node-significance,
.node-thoughts {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 12px;
  color: var(--text-color);
  opacity: 0.7;
  margin-bottom: 4px;
  line-height: 1.3;
}

.node-path {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-color);
  opacity: 0.6;
}

/* 选中节点信息 */
.selected-node-info {
  margin-top: 16px;
  padding: 16px;
  background: var(--bg-color-light, #f8f9fa);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.info-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.info-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.info-title {
  font-weight: 600;
  font-size: 15px;
  color: var(--text-color);
  flex: 1;
  min-width: 0; /* 允许文本截断 */
}

.info-badges {
  display: flex;
  gap: 4px;
}

.info-content {
  font-size: 13px;
  line-height: 1.5;
}

.info-section {
  margin-bottom: 12px;
}

.info-section:last-child {
  margin-bottom: 0;
}

.info-section h4 {
  margin: 0 0 6px 0;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-color);
  opacity: 0.8;
}

.info-section p {
  margin: 0;
  color: var(--text-color);
  opacity: 0.9;
}

.child-nodes {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.more-children {
  font-size: 11px;
  color: var(--text-color);
  opacity: 0.6;
}

.node-path-full {
  font-family: monospace;
  font-size: 11px !important;
  background: var(--bg-color);
  padding: 6px 8px;
  border-radius: 4px;
  border: 1px solid var(--border-color);
}

/* 动画效果 */
.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 响应式设计 */
@media (max-width: 767px) {
  .no-nodes-tip {
    flex-direction: column;
    text-align: center;
    padding: 16px;
  }
  
  .selected-node-info {
    padding: 12px;
  }
  
  .info-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .info-badges {
    align-self: stretch;
  }
  
  .info-content {
    font-size: 12px;
  }
  
  .info-section h4 {
    font-size: 11px;
  }
  
  .node-option {
    padding: 6px 0;
  }
  
  .option-header {
    flex-wrap: wrap;
    gap: 6px;
  }
  
  .node-badges {
    flex-wrap: wrap;
  }
}

/* 暗色主题适配 */
.dark-theme .no-nodes-tip {
  background: var(--bg-color-dark, #1d1d1d);
  border-color: var(--border-color-dark, #3a3a3a);
}

.dark-theme .selected-node-info {
  background: var(--bg-color-dark, #1d1d1d);
  border-color: var(--border-color-dark, #3a3a3a);
}

.dark-theme .node-path-full {
  background: var(--bg-color);
  border-color: var(--border-color-dark, #3a3a3a);
}
</style>
