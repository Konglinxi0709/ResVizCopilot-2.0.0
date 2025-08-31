<template>
  <div class="agent-selector">
    <div class="selector-header">
      <el-icon><UserFilled /></el-icon>
      <span class="header-text">选择智能体</span>
    </div>
    
    <el-select
      v-model="selectedAgent"
      placeholder="请选择智能体类型"
      size="large"
      class="agent-select"
      :disabled="disabled"
      @change="handleAgentChange"
    >
      <el-option
        v-for="agent in availableAgents"
        :key="agent.value"
        :label="agent.label"
        :value="agent.value"
        :disabled="agent.disabled"
      >
        <div class="agent-option">
          <div class="option-header">
            <el-icon class="agent-icon">
              <component :is="agent.icon" />
            </el-icon>
            <span class="agent-name">{{ agent.label }}</span>
            <el-tag 
              v-if="agent.status" 
              :type="getStatusType(agent.status)" 
              size="small"
            >
              {{ getStatusText(agent.status) }}
            </el-tag>
          </div>
          <div class="agent-description">{{ agent.description }}</div>
          <div v-if="agent.requirements" class="agent-requirements">
            <el-icon><InfoFilled /></el-icon>
            <span>{{ agent.requirements }}</span>
          </div>
        </div>
      </el-option>
    </el-select>
    
    <!-- 智能体详细信息 -->
    <transition name="fade">
      <div v-if="selectedAgentInfo" class="agent-info">
        <div class="info-header">
          <el-icon class="info-icon">
            <component :is="selectedAgentInfo.icon" />
          </el-icon>
          <span class="info-title">{{ selectedAgentInfo.label }}</span>
        </div>
        
        <div class="info-content">
          <p class="info-description">{{ selectedAgentInfo.description }}</p>
          
          <div v-if="selectedAgentInfo.capabilities" class="capabilities">
            <h4>主要功能：</h4>
            <ul>
              <li v-for="capability in selectedAgentInfo.capabilities" :key="capability">
                {{ capability }}
              </li>
            </ul>
          </div>
          
          <div v-if="selectedAgentInfo.requirements" class="requirements">
            <el-icon><WarningFilled /></el-icon>
            <span>{{ selectedAgentInfo.requirements }}</span>
          </div>
          
          <div v-if="selectedAgentInfo.tips" class="tips">
            <el-icon><InfoFilled /></el-icon>
            <span>使用提示：{{ selectedAgentInfo.tips }}</span>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { defineComponent, ref, computed, watch } from 'vue'
import { 
  UserFilled, Cpu, ChatDotRound, InfoFilled, WarningFilled 
} from '@element-plus/icons-vue'
import { useMessageStore } from '@/stores/messageStore'

export default defineComponent({
  name: 'AgentSelector',
  
  components: {
    UserFilled, Cpu, ChatDotRound, InfoFilled, WarningFilled
  },
  
  props: {
    // 选中的智能体
    modelValue: {
      type: String,
      default: ''
    },
    
    // 是否禁用
    disabled: {
      type: Boolean,
      default: false
    },
    
    // 可用的节点列表（用于检查智能体是否可用）
    availableNodes: {
      type: Array,
      default: () => []
    }
  },
  
  emits: ['update:modelValue', 'agent-changed'],
  
  setup(props, { emit }) {
    const messageStore = useMessageStore()
    
    const selectedAgent = ref(props.modelValue)
    
    // 智能体配置
    const agentConfigs = [
      {
        value: 'auto_research_agent',
        label: '自动研究智能体',
        description: '为实施问题自动生成解决方案，深度分析问题并提供结构化的解决思路',
        icon: 'Cpu',
        status: 'available',
        requiresNode: true,
        nodeType: 'problem',
        nodeFilter: (node) => node.type === 'problem' && node.problem_type === 'implementation',
        capabilities: [
          '分析实施问题的复杂性和挑战',
          '生成结构化的解决方案',
          '提供详细的实施计划',
          '考虑技术可行性和资源需求'
        ],
        requirements: '需要选择一个实施类型的问题节点',
        tips: '详细描述你的要求和约束条件，智能体会生成更精准的解决方案'
      },
      {
        value: 'user_chat_agent',
        label: '用户对话智能体',
        description: '与解决方案进行深度对话，探讨技术细节、实施方案和优化建议',
        icon: 'ChatDotRound',
        status: 'available',
        requiresNode: true,
        nodeType: 'solution',
        nodeFilter: (node) => node.type === 'solution',
        capabilities: [
          '深度分析解决方案的技术细节',
          '讨论实施过程中的挑战',
          '提供优化建议和改进方案',
          '回答技术相关问题'
        ],
        requirements: '需要选择一个解决方案节点',
        tips: '可以询问技术实现、潜在风险、替代方案等问题'
      }
    ]
    
    // 计算可用的智能体
    const availableAgents = computed(() => {
      return agentConfigs.map(agent => {
        let status = 'available'
        let disabled = false
        
        // 检查是否正在生成
        if (messageStore.isGenerating) {
          status = 'busy'
          disabled = true
        }
        
        // 检查节点要求
        if (agent.requiresNode && props.availableNodes.length > 0) {
          const hasValidNodes = props.availableNodes.some(node => 
            agent.nodeFilter(node)
          )
          
          if (!hasValidNodes) {
            status = 'unavailable'
            disabled = true
          }
        } else if (agent.requiresNode && props.availableNodes.length === 0) {
          status = 'no_data'
          disabled = true
        }
        
        return {
          ...agent,
          status,
          disabled
        }
      })
    })
    
    // 当前选中的智能体信息
    const selectedAgentInfo = computed(() => {
      if (!selectedAgent.value) return null
      return availableAgents.value.find(agent => agent.value === selectedAgent.value)
    })
    
    // 获取状态类型
    const getStatusType = (status) => {
      switch (status) {
        case 'available': return 'success'
        case 'busy': return 'warning'
        case 'unavailable': return 'danger'
        case 'no_data': return 'info'
        default: return 'info'
      }
    }
    
    // 获取状态文本
    const getStatusText = (status) => {
      switch (status) {
        case 'available': return '可用'
        case 'busy': return '忙碌'
        case 'unavailable': return '不可用'
        case 'no_data': return '无数据'
        default: return '未知'
      }
    }
    
    // 处理智能体变化
    const handleAgentChange = (value) => {
      selectedAgent.value = value
      emit('update:modelValue', value)
      
      const agentInfo = availableAgents.value.find(agent => agent.value === value)
      emit('agent-changed', agentInfo)
    }
    
    // 监听外部变化
    watch(() => props.modelValue, (newValue) => {
      selectedAgent.value = newValue
    })
    
    // 监听智能体生成状态
    watch(() => messageStore.isGenerating, (isGenerating) => {
      if (isGenerating) {
        // 智能体开始生成时，可以显示当前使用的智能体
        const currentAgent = messageStore.currentAgentName
        if (currentAgent && currentAgent !== selectedAgent.value) {
          selectedAgent.value = currentAgent
          emit('update:modelValue', currentAgent)
        }
      }
    })
    
    return {
      selectedAgent,
      availableAgents,
      selectedAgentInfo,
      getStatusType,
      getStatusText,
      handleAgentChange
    }
  }
})
</script>

<style scoped>
.agent-selector {
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
}

.agent-select {
  width: 100%;
}

/* 智能体选项样式 */
.agent-option {
  padding: 4px 0;
}

.option-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.agent-icon {
  font-size: 16px;
  color: var(--primary-color);
}

.agent-name {
  font-weight: 500;
  color: var(--text-color);
}

.agent-description {
  font-size: 12px;
  color: var(--text-color);
  opacity: 0.8;
  line-height: 1.4;
  margin-bottom: 4px;
}

.agent-requirements {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--warning-color);
}

/* 智能体信息面板 */
.agent-info {
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
}

.info-icon {
  font-size: 18px;
  color: var(--primary-color);
}

.info-title {
  font-weight: 600;
  font-size: 16px;
  color: var(--text-color);
}

.info-content {
  font-size: 14px;
  line-height: 1.6;
}

.info-description {
  margin: 0 0 12px 0;
  color: var(--text-color);
  opacity: 0.9;
}

.capabilities {
  margin-bottom: 12px;
}

.capabilities h4 {
  margin: 0 0 8px 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-color);
}

.capabilities ul {
  margin: 0;
  padding-left: 16px;
}

.capabilities li {
  margin-bottom: 4px;
  font-size: 13px;
  color: var(--text-color);
  opacity: 0.8;
}

.requirements {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 8px 12px;
  background: var(--warning-color-lighter, #fdf6ec);
  border: 1px solid var(--warning-color-light, #faecd8);
  border-radius: 6px;
  margin-bottom: 8px;
}

.requirements span {
  font-size: 12px;
  color: var(--warning-color);
}

.tips {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 8px 12px;
  background: var(--info-color-lighter, #f4f9ff);
  border: 1px solid var(--info-color-light, #d9ecff);
  border-radius: 6px;
}

.tips span {
  font-size: 12px;
  color: var(--info-color);
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
  .agent-info {
    padding: 12px;
  }
  
  .info-content {
    font-size: 13px;
  }
  
  .capabilities h4 {
    font-size: 12px;
  }
  
  .capabilities li {
    font-size: 12px;
  }
  
  .requirements span,
  .tips span {
    font-size: 11px;
  }
}

/* 暗色主题适配 */
.dark-theme .agent-info {
  background: var(--bg-color-dark, #1d1d1d);
  border-color: var(--border-color-dark, #3a3a3a);
}

.dark-theme .requirements {
  background: rgba(230, 162, 60, 0.1);
  border-color: rgba(230, 162, 60, 0.2);
}

.dark-theme .tips {
  background: rgba(64, 158, 255, 0.1);
  border-color: rgba(64, 158, 255, 0.2);
}
</style>
