<template>
  <div class="mind-elixir-wrapper">
    <!-- Mind-elixir 渲染容器 -->
    <div 
      ref="mindElixirEl" 
      class="mind-elixir-canvas"
      :class="{ 'snapshot-view': isSnapshotView }"
    ></div>
    
    <!-- 快照查看指示器 -->
    <div v-if="isSnapshotView" class="snapshot-indicator">
      <el-card class="snapshot-card" shadow="hover">
        <div class="snapshot-content">
          <el-icon class="snapshot-icon"><Camera /></el-icon>
          <span class="snapshot-text">正在查看历史快照</span>
          <el-button 
            size="small" 
            type="primary" 
            @click="exitSnapshotView"
            class="return-btn"
          >
            返回当前
          </el-button>
        </div>
      </el-card>
    </div>
    
    <!-- 智能体操作指示器 -->
    <div v-if="agentOperatingNodeId" class="agent-indicator">
      <el-card class="agent-card" shadow="hover">
        <div class="agent-content">
          <el-icon class="agent-icon rotating"><Loading /></el-icon>
          <span class="agent-text">智能体正在操作中...</span>
        </div>
      </el-card>
    </div>
    
    <!-- 调试信息 -->
    <div v-if="!hasData" class="debug-info">
      <div class="debug-overlay">
        <h3>调试信息</h3>
        <p>hasData: {{ hasData }}</p>
        <p>mindElixirData: {{ !!mindElixirData }}</p>
        <p>nodeData: {{ !!mindElixirData?.nodeData }}</p>
        <p>mind实例: {{ !!mind }}</p>
        <p>isInitialized: {{ isInitialized }}</p>
        <el-button type="primary" @click="$emit('refresh-data')">重新加载</el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import MindElixir from 'mind-elixir'
import { Camera, Loading } from '@element-plus/icons-vue'

export default defineComponent({
  name: 'MindElixirWrapper',
  
  components: {
    Camera,
    Loading
  },
  
  props: {
    // Mind-elixir数据
    mindElixirData: {
      type: Object,
      default: null
    },
    
    // 是否为快照查看模式
    isSnapshotView: {
      type: Boolean,
      default: false
    },
    
    // 智能体正在操作的节点ID
    agentOperatingNodeId: {
      type: String,
      default: null
    },
    
    // 自定义配置
    options: {
      type: Object,
      default: () => ({})
    }
  },
  
  emits: ['node-selected', 'exit-snapshot-view', 'refresh-data'],
  
  data() {
    return {
      mind: null,
      isInitialized: false
    }
  },
  
  computed: {
    hasData() {
      return !!(this.mindElixirData && this.mindElixirData.nodeData)
    }
  },
  
  watch: {
    mindElixirData: {
      handler(newData) {
        if (newData && this.mind) {
          this.updateMindMap(newData)
        }
      },
      deep: true,
      immediate: false
    },
    
    agentOperatingNodeId() {
      // 当智能体操作状态变化时，重新渲染以应用特殊样式
      if (this.mind && this.mindElixirData) {
        this.updateMindMap(this.mindElixirData)
      }
    }
  },
  
  mounted() {
    this.$nextTick(() => {
      this.initMindElixir()
    })
  },
  
  beforeUnmount() {
    if (this.mind) {
      try {
        this.mind.destroy()
      } catch (error) {
        console.warn('Mind-elixir destroy error:', error)
      }
    }
  },
  
  methods: {
    // 初始化Mind-elixir
    initMindElixir() {
      console.log('🚀 开始初始化Mind-elixir')
      console.log('容器元素:', this.$refs.mindElixirEl)
      console.log('mindElixirData:', this.mindElixirData)
      
      if (!this.$refs.mindElixirEl) {
        console.error('❌ Mind-elixir容器元素未找到')
        return
      }
      
      try {
                 // 基础只读配置（参考老项目的简洁配置）
         const config = {
           el: this.$refs.mindElixirEl,
           direction: MindElixir.RIGHT, // 侧边布局
           locale: 'zh_CN',
           
           // 设置亮色主题
           theme: {
             name: 'Default',
             palette: ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399'],
             cssVar: {
               '--main-color': '#303133',
               '--main-bgcolor': '#ffffff',
               '--color': '#606266',
               '--bgcolor': '#f5f7fa'
             }
           },
           
           // 禁用编辑功能
           draggable: false,
           editable: false,
           contextMenu: false,
           toolBar: false,
           nodeMenu: false,
           keypress: false,
           
           // 禁用关键编辑操作
           before: {
             copyNode: () => false,
             copyNodes: () => false,
             insertSibling: () => false,
             insertParent: () => false,
             addChild: () => false,
             removeNode: () => false,
             removeNodes: () => false,
             moveNode: () => false,
             beginEdit: () => false
           },
           
           // 合并自定义配置
           ...this.options
         }
        
        // 创建Mind-elixir实例
        console.log('⚙️ 创建Mind-elixir实例，配置:', config)
        this.mind = new MindElixir(config)
        console.log('✅ Mind-elixir实例创建成功:', this.mind)
        
        // 添加节点选择事件监听
        this.mind.bus.addListener('selectNode', this.handleNodeSelect)
        this.mind.bus.addListener('unselectNode', this.handleNodeUnselect)
        
        this.isInitialized = true
        console.log('✅ Mind-elixir初始化完成')
        
        // 如果有数据，立即渲染
        if (this.mindElixirData) {
          console.log('📊 有初始数据，开始渲染')
          this.updateMindMap(this.mindElixirData)
        } else {
          console.log('📊 暂无初始数据')
        }
        
      } catch (error) {
        console.error('Mind-elixir初始化失败:', error)
        this.$message.error('思维导图初始化失败')
      }
    },
    
    // 更新思维导图数据
    updateMindMap(data) {
      if (!this.mind || !data || !data.nodeData) {
        console.warn('Mind-elixir实例或数据未准备好')
        return
      }
      
      try {
        // 处理智能体操作状态
        const processedData = this.processAgentOperatingState(data)
        
        // 打印详细数据信息
        console.log('🔍 准备渲染的数据:', processedData.nodeData)
        console.log('🔍 数据结构检查:', {
          hasNodeData: !!processedData.nodeData,
          hasId: !!processedData.nodeData?.id,
          hasTopic: !!processedData.nodeData?.topic,
          hasChildren: !!processedData.nodeData?.children,
          childrenCount: processedData.nodeData?.children?.length || 0
        })
        
        // 使用init方法加载数据（参考老项目）
        // 注意：老项目传入的是完整的data对象，而不是nodeData
        this.mind.init(processedData)
        
        // 检查init后的状态
        console.log('🔍 Mind-elixir init后状态:', {
          mindInstance: !!this.mind,
          painter: !!this.mind.painter,
          nodeData: !!this.mind.nodeData,
          container: !!this.mind.container
        })
        
        // 强制重新渲染和布局
        this.$nextTick(() => {
          if (this.mind && this.mind.painter) {
            console.log('🎨 尝试手动触发绘制')
            // 尝试触发重新布局
            if (this.mind.layout) {
              this.mind.layout()
            }
            // 尝试手动绘制
            if (this.mind.painter.draw) {
              this.mind.painter.draw()
            }
          }
        })
        
        // 应用主题（在init之后）
        if (data.theme) {
          setTimeout(() => {
            try {
              this.mind.changeTheme(data.theme)
            } catch (themeError) {
              console.warn('主题应用失败:', themeError)
            }
          }, 100) // 延迟应用主题，确保init完成
        }
        
        console.log('Mind-elixir数据更新完成')
        
      } catch (error) {
        console.error('Mind-elixir数据更新失败:', error)
        this.$message?.error('思维导图更新失败')
      }
    },
    
    // 处理智能体操作状态
    processAgentOperatingState(data) {
      if (!this.agentOperatingNodeId) {
        return data
      }
      
      // 深度克隆数据以避免修改原始数据
      const processedData = JSON.parse(JSON.stringify(data))
      
      // 递归查找并标记智能体操作的节点
      const markAgentOperating = (node) => {
        if (node.id === this.agentOperatingNodeId) {
          // 添加智能体操作标识
          node.icons = [...(node.icons || []), '🤖']
          if (node.style) {
            node.style.borderColor = '#fa8c16'
            node.style.borderWidth = '3px'
            node.style.animation = 'pulse 2s infinite'
          }
        }
        
        if (node.children) {
          node.children.forEach(markAgentOperating)
        }
      }
      
      if (processedData.nodeData) {
        markAgentOperating(processedData.nodeData)
      }
      
      return processedData
    },
    
    // 处理节点选择事件
    handleNodeSelect(nodeObj) {
      if (!nodeObj || nodeObj.id === 'root') {
        return
      }
      
      console.log('节点被选中:', nodeObj)
      
      this.$emit('node-selected', {
        id: nodeObj.id,
        title: nodeObj.topic,
        data: nodeObj
      })
    },
    
    // 处理节点取消选择事件
    handleNodeUnselect() {
      console.log('节点取消选中')
    },
    
    // 退出快照查看
    exitSnapshotView() {
      this.$emit('exit-snapshot-view')
    },
    
    // 获取Mind-elixir实例（供外部使用）
    getMindInstance() {
      return this.mind
    },
    
    // 重新初始化（供外部调用）
    reinitialize() {
      if (this.mind) {
        this.mind.destroy()
      }
      this.$nextTick(() => {
        this.initMindElixir()
      })
    }
  }
})
</script>

<style scoped>
.mind-elixir-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.mind-elixir-canvas {
  width: 100%;
  height: 100%;
  background: #ffffff; /* 白色背景 */
  transition: all 0.3s ease;
  min-height: 400px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.mind-elixir-canvas.snapshot-view {
  filter: brightness(0.9) saturate(0.8);
}

/* 快照查看指示器 */
.snapshot-indicator {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
}

.snapshot-card {
  border-radius: 8px;
  border: 1px solid #409eff;
  background: rgba(64, 158, 255, 0.1);
  backdrop-filter: blur(4px);
}

.snapshot-content {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
}

.snapshot-icon {
  color: #409eff;
  font-size: 16px;
}

.snapshot-text {
  color: #409eff;
  font-weight: 500;
  font-size: 14px;
}

.return-btn {
  font-size: 12px;
  height: 28px;
}

/* 智能体操作指示器 */
.agent-indicator {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 1000;
}

.agent-card {
  border-radius: 8px;
  border: 1px solid #fa8c16;
  background: rgba(250, 140, 22, 0.1);
  backdrop-filter: blur(4px);
}

.agent-content {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
}

.agent-icon {
  color: #fa8c16;
  font-size: 16px;
}

.agent-text {
  color: #fa8c16;
  font-weight: 500;
  font-size: 14px;
}

.rotating {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 调试信息 */
.debug-info {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 100;
}

.debug-overlay {
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid #409eff;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.debug-overlay h3 {
  margin-top: 0;
  color: #409eff;
}

.debug-overlay p {
  margin: 8px 0;
  font-family: monospace;
}

/* 智能体操作动画效果 */
:deep(.mind-elixir-canvas .node[data-agent-operating="true"]) {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(250, 140, 22, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(250, 140, 22, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(250, 140, 22, 0);
  }
}
</style>

<!-- Mind-elixir 专用样式 -->
<style>
/* Mind-elixir 容器样式 */
.mind-elixir-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
}

.mind-elixir-wrapper * {
  box-sizing: border-box;
}

/* 强制设置Mind-elixir亮色主题 */
.mind-elixir-wrapper .mind-elixir {
  background-color: #ffffff !important;
  color: #303133 !important;
}

/* 确保SVG背景也是白色的 */
.mind-elixir-wrapper .mind-elixir svg {
  background-color: #ffffff !important;
}

/* 节点样式 */
.mind-elixir-wrapper .mind-elixir .node {
  color: #303133 !important;
  background-color: #f5f7fa !important;
  border: 1px solid #dcdfe6 !important;
}

/* 连接线样式 */
.mind-elixir-wrapper .mind-elixir .line {
  stroke: #606266 !important;
}
</style>
