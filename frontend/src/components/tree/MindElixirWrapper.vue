<template>
  <div class="mind-elixir-wrapper">
    <!-- Mind-elixir 渲染容器 -->
    <div
      ref="mindElixirEl"
      class="mind-elixir-canvas"
    ></div>
    
  </div>
</template>

<script>
import MindElixir from 'mind-elixir'

export default {
  name: 'MindElixirWrapper',

  components: {},
  
  props: {
    // Mind-elixir数据
    mindElixirData: {
      type: Object,
      default: null
    },

    // 选中的节点ID (v-model)
    selectedNodeId: {
      type: String,
      default: null
    },

    // 自定义配置
    options: {
      type: Object,
      default: () => ({})
    }
  },

  emits: ['node-selected', 'update:selectedNodeId'],
  
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
        console.error('❌ 找不到Mind-elixir容器元素')
        return
      }
      
      try {
        // 创建Mind-elixir配置
        const config = this.createMindElixirConfig()
        
        // 初始化Mind-elixir实例
        this.mind = new MindElixir(config)
        
        console.log('✅ Mind-elixir实例创建成功:', this.mind)
        
        // 如果有数据，立即渲染
        if (this.mindElixirData) {
          this.updateMindMap(this.mindElixirData)
        }
        
        this.isInitialized = true
        console.log('🎉 Mind-elixir初始化完成')
        
      } catch (error) {
        console.error('❌ Mind-elixir初始化失败:', error)
      }
    },
    
    // 创建Mind-elixir配置
    createMindElixirConfig() {
      const baseConfig = {
        el: this.$refs.mindElixirEl,
        direction: MindElixir.RIGHT,
        locale: 'zh_CN',
        // 关键：限制内部画布尺寸的扩展，避免 map-canvas 无限增大
        overflowHidden: true,
        
        // 只读模式配置
        draggable: false,
        editable: false,
        contextMenu: false,
        toolBar: true,
        keypress: false,
        
        // 禁用所有编辑操作
        before: {
          insertSibling: () => false,
          insertParent: () => false,
          addChild: () => false,
          removeNode: () => false,
          removeNodes: () => false,
          moveNode: () => false,
          moveUpNode: () => false,
          moveDownNode: () => false,
          moveNodeIn: () => false,
          moveNodeBefore: () => false,
          moveNodeAfter: () => false,
          copyNode: () => false,
          copyNodes: () => false,
          beginEdit: () => false
        },
        
        // 主题配置
        theme: {
          name: 'Default',
          cssVar: {
            '--main-bgcolor': '#ffffff',
            '--main-color': '#303133',
            '--color': '#666666',
            '--bgcolor': '#f6f6f6'
          }
        }
      }
      
      // 合并自定义配置
      return { ...baseConfig, ...this.options }
    },
    
    // 更新思维导图数据
    updateMindMap(data) {
      if (!this.mind || !data) {
        console.warn('⚠️ 无法更新思维导图：mind实例或数据不存在')
        return
      }
      
      try {
        console.log('🔄 更新思维导图数据:', data)
        
        // 确保数据格式正确
        let nodeData = null
        if (data.nodeData) {
          nodeData = data.nodeData
        } else if (data.id && data.topic) {
          // 如果data本身就是节点数据
          nodeData = data
        } else {
          throw new Error('无效的数据格式：缺少nodeData或有效的节点数据')
        }
        
        // 验证节点数据的完整性
        if (!nodeData.id || !nodeData.topic) {
          throw new Error('节点数据不完整：缺少id或topic')
        }
        
        console.log('🎯 准备传递给Mind-elixir的数据:', nodeData)
        
        // 使用init方法加载数据（参考老项目）
        // 注意：老项目传入的是完整的data对象，而不是nodeData
        // Mind-elixir期望接收包含nodeData和theme的完整对象
        this.mind.init(data)
        
        console.log('✅ 思维导图数据更新成功')
        
        // 检查init后的状态
        console.log('🔍 Mind-elixir init后状态:', {
          mindInstance: !!this.mind,
          painter: !!this.mind.painter,
          nodeData: !!this.mind.nodeData,
          container: !!this.mind.container
        })
        
        // 强制重新渲染和布局（参考老版本）
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
        
        // 数据更新成功后，应用主题（如果有）
        if (data.theme) {
          try {
            setTimeout(() => {
              this.mind.changeTheme(data.theme)
              console.log('🎨 主题应用成功')
            }, 200) // 增加延迟，确保数据完全渲染
          } catch (themeError) {
            console.warn('⚠️ 主题应用失败:', themeError)
          }
        }
        
      } catch (error) {
        console.error('❌ 更新思维导图失败:', error)
        console.error('❌ 错误详情:', {
          message: error.message,
          stack: error.stack,
          data: data
        })
        
        // 尝试重新初始化Mind-elixir
        console.log('🔄 尝试重新初始化Mind-elixir...')
        this.reinitializeMindElixir()
      }
    },
    
    // 安全的数据刷新方法
    safeRefresh() {
      try {
        console.log('🔄 尝试安全刷新数据...')
        
        // 如果mind实例存在，先销毁
        if (this.mind) {
          this.mind.destroy()
          this.mind = null
        }
        
        // 重新初始化
        this.initMindElixir()
        
      } catch (error) {
        console.error('❌ 安全刷新也失败:', error)
      }
    },
    
    // 重新初始化Mind-elixir
    reinitializeMindElixir() {
      try {
        if (this.mind) {
          this.mind.destroy()
          this.mind = null
        }
        
        this.isInitialized = false
        
        // 延迟重新初始化，避免立即重试
        setTimeout(() => {
          this.initMindElixir()
        }, 100)
        
      } catch (error) {
        console.error('❌ 重新初始化失败:', error)
        this.$message?.error('思维导图重新初始化失败')
      }
    },
    
    // 处理节点选择事件
    handleNodeSelect(nodeObj) {
      console.log('🎯 节点被选中:', nodeObj)

      const nodeId = nodeObj.id
      this.$emit('update:selectedNodeId', nodeId)

      const nodeInfo = {
        id: nodeId,
        title: nodeObj.topic,
        data: nodeObj
      }

      this.$emit('node-selected', nodeInfo)
    },
    
  }
}
</script>

<style scoped>
.mind-elixir-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  max-height: 100%; /* 确保不超过父容器高度 */
  overflow: hidden;
}

.mind-elixir-canvas {
  width: 100%;
  height: 100%;
  max-height: 100%; /* 确保不超过父容器高度 */
  background: #ffffff; /* 白色背景 */
  transition: all 0.3s ease;
  min-height: 300px; /* 减小最小高度，避免强制撑开 */
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
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

<!-- Mind-elixir 专用样式 - 现代化设计 -->
<style scoped>
.mind-elixir-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
}
</style>

<!-- 基本样式 - 保持简洁 -->
<style>
/* 确保Mind-elixir正常显示 */
.mind-elixir-wrapper .mind-elixir {
  background-color: #ffffff;
  color: #333333;
}

.mind-elixir-wrapper .mind-elixir svg {
  background-color: #ffffff;
}
</style>
