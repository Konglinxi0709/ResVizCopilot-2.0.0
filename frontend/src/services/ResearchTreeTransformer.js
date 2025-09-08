/**
 * 研究树数据转换器
 * 
 * 将后端研究树数据转换为Mind-elixir格式，并应用现代化的视觉样式
 * 支持节点类型区分、状态指示、快照查看等多种视觉模式
 */

// 现代化配色方案 - 基于Design System的原则
const MODERN_COLORS = {
  // 主色调 - 蓝色系（问题节点）
  primary: {
    50: '#f0f7ff',
    100: '#e0f0ff', 
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8'
  },
  
  // 成功色 - 绿色系（成功状态）
  success: {
    50: '#f0fdf4',
    100: '#dcfce7',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d'
  },
  
  // 警告色 - 琥珀色系（进行中状态）
  warning: {
    50: '#fffbeb',
    100: '#fef3c7',
    500: '#f59e0b',
    600: '#d97706',
    700: '#b45309'
  },
  
  // 错误色 - 红色系（失败状态/条件问题）
  error: {
    50: '#fef2f2',
    100: '#fecaca',
    500: '#ef4444',
    600: '#dc2626',
    700: '#b91c1c'
  },
  
  // 中性色 - 灰色系（已弃用/其他状态）
  neutral: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827'
  },
  
  // 紫色系 - 解决方案节点
  purple: {
    50: '#faf5ff',
    100: '#f3e8ff',
    500: '#a855f7',
    600: '#9333ea',
    700: '#7c3aed'
  }
}

// 节点类型样式配置
const NODE_STYLE_CONFIG = {
  // 问题节点样式
  problem: {
    implementation: {
      background: MODERN_COLORS.primary[50],
      color: MODERN_COLORS.primary[700],
      borderColor: MODERN_COLORS.primary[500],
      borderWidth: '2px',
      borderRadius: '8px',
      padding: '12px 16px',
      fontSize: '14px',
      fontWeight: '500'
    },
    conditional: {
      background: MODERN_COLORS.error[50],
      color: MODERN_COLORS.error[700],
      borderColor: MODERN_COLORS.error[500],
      borderWidth: '2px',
      borderRadius: '8px',
      padding: '12px 16px',
      fontSize: '14px',
      fontWeight: '500'
    }
  },
  
  // 解决方案节点样式
  solution: {
    base: {
      background: MODERN_COLORS.purple[50],
      color: MODERN_COLORS.purple[700],
      borderColor: MODERN_COLORS.purple[500],
      borderWidth: '2px',
      borderRadius: '8px',
      padding: '12px 16px',
      fontSize: '14px',
      fontWeight: '500'
    },
    selected: {
      borderWidth: '3px',
      boxShadow: `0 0 0 2px ${MODERN_COLORS.purple[500]}20`
    },
    states: {
      pending: {
        background: MODERN_COLORS.neutral[100],
        color: MODERN_COLORS.neutral[700],
        borderColor: MODERN_COLORS.neutral[400]
      },
      in_progress: {
        background: MODERN_COLORS.warning[50],
        color: MODERN_COLORS.warning[700],
        borderColor: MODERN_COLORS.warning[500]
      },
      completed: {
        background: MODERN_COLORS.success[50],
        color: MODERN_COLORS.success[700],
        borderColor: MODERN_COLORS.success[500]
      },
      failed: {
        background: MODERN_COLORS.error[50],
        color: MODERN_COLORS.error[700],
        borderColor: MODERN_COLORS.error[500]
      },
    }
  },
  
  // 通用状态样式（适用于所有节点类型）
  common: {
    deprecated: {
      background: MODERN_COLORS.neutral[100],
      color: MODERN_COLORS.neutral[500],
      borderColor: MODERN_COLORS.neutral[300],
      opacity: '0.7'
    }
  }
}

// 图标配置 - 使用更现代的emoji
const ICON_CONFIG = {
  nodeTypes: {
    implementation_problem: '🎯',
    conditional_problem: '❓',
    solution: '💡'
  },
  
  states: {
    pending: '',
    in_progress: '⏳',
    completed: '✅',
    failed: '❌',
    deprecated: '🗑️'
  },
  
  special: {
    selected_solution: '⭐',
    agent_operating: '🤖',
    snapshot_view: '📸',
    root_problem: '🏠'
  }
}

// 标签配置 - 简化标签显示
const TAG_CONFIG = {
  nodeTypes: {
    implementation_problem: ['实施问题'],
    conditional_problem: ['条件问题'],
    solution: ['解决方案']
  },
  
  states: {
    pending: [],
    in_progress: ['进行中'],
    completed: ['已完成'],
    failed: ['失败'],
    deprecated: ['已弃用']
  },
  
  special: {
    selected: ['已选中'],
    root: ['根问题']
  }
}

export class ResearchTreeTransformer {
  constructor() {
    this.styleConfig = NODE_STYLE_CONFIG
    this.iconConfig = ICON_CONFIG
    this.tagConfig = TAG_CONFIG
  }
  
  /**
   * 将后端研究树数据转换为Mind-elixir格式
   * @param {Object} backendSnapshot - 后端快照数据
   * @param {Object} context - 转换上下文
   * @returns {Object} Mind-elixir格式的数据
   */
  transformToMindElixir(backendSnapshot, context = {}) {
    console.log('🔄 开始转换后端数据到Mind-elixir格式')
    console.log('📊 后端快照数据:', backendSnapshot)
    console.log('🎨 转换上下文:', context)
    
    if (!backendSnapshot || !backendSnapshot.roots || backendSnapshot.roots.length === 0) {
      console.warn('⚠️ 后端数据为空，使用空数据模板')
      return this.createEmptyMindMap()
    }
    
    // 创建根节点作为Mind-elixir的根
    const rootNode = {
      id: 'mind-root',
      topic: '研究树',
      root: true,
      style: {
        background: MODERN_COLORS.neutral[50],
        color: MODERN_COLORS.neutral[800],
        borderColor: MODERN_COLORS.neutral[300],
        fontSize: '16px',
        fontWeight: '600',
        borderRadius: '12px',
        padding: '16px 20px'
      },
      children: []
    }
    
    // 将快照数据添加到 context 中，供节点启用状态判断使用
    context.snapshotData = backendSnapshot
    
    // 转换所有根节点为子节点
    backendSnapshot.roots.forEach(root => {
      const transformedNode = this.transformNode(root, context, null)
      if (transformedNode) {
        // 为根问题添加特殊标识
        transformedNode.icons = [...(transformedNode.icons || []), this.iconConfig.special.root_problem]
        transformedNode.tags = [...(transformedNode.tags || []), ...this.tagConfig.special.root]
        rootNode.children.push(transformedNode)
      }
    })
    
    const result = {
      nodeData: rootNode,
      theme: this.getTheme(context)
    }
    
    console.log('✅ 数据转换完成:', result)
    return result
  }
  
  /**
   * 转换单个节点
   * @param {Object} node - 后端节点数据
   * @param {Object} context - 转换上下文
   * @param {Object} parentNode - 父节点数据（用于判断选中状态）
   * @returns {Object} 转换后的节点
   */
  transformNode(node, context, parentNode = null) {
    if (!node || !node.id) {
      console.warn('⚠️ 节点数据无效:', node)
      return null
    }
    
    // 如果启用了隐藏弃用节点，且当前节点是弃用的，则跳过
    if (context.hideDeprecatedNodes && context.snapshotData) {
      const isNodeEnabled = this.isNodeInSelectedPath(context.snapshotData.roots, node.id)
      if (isNodeEnabled === false) {
        return null // 跳过弃用节点
      }
    }
    
    // 创建符合Mind-elixir要求的节点结构
    const mindElixirNode = {
      id: node.id,
      topic: node.title || '未命名节点',
      children: []
    }
    
    // 应用节点样式
    this.applyNodeStyle(mindElixirNode, node, context, parentNode)
    
    // 递归处理子节点 - 参考老版本的实现
    if (node.children && node.children.length > 0) {
      const validChildren = []
      node.children.forEach(child => {
        const transformedChild = this.transformNode(child, context, node)
        if (transformedChild && transformedChild.id && transformedChild.topic) {
          validChildren.push(transformedChild)
        }
      })
      mindElixirNode.children = validChildren
    }
    
    // 确保节点数据完整
    if (!mindElixirNode.id || !mindElixirNode.topic) {
      console.warn('⚠️ 转换后的节点数据不完整:', mindElixirNode)
      return null
    }
    
    return mindElixirNode
  }
  
  /**
   * 应用节点样式
   * @param {Object} mindElixirNode - Mind-elixir节点
   * @param {Object} backendNode - 后端节点数据
   * @param {Object} context - 转换上下文
   * @param {Object} parentNode - 父节点数据
   */
  applyNodeStyle(mindElixirNode, backendNode, context, parentNode = null) {
    const nodeState = this.getNodeState(backendNode)
    
    // 获取基础样式
    let baseStyle = {}
    let baseTags = []
    let baseIcons = []
    
    if (backendNode.type === 'problem') {
      const problemType = backendNode.problem_type === 'implementation' ? 'implementation' : 'conditional'
      baseStyle = { ...this.styleConfig.problem[problemType] }
      baseTags = [...this.tagConfig.nodeTypes[`${problemType}_problem`]]
      baseIcons = [this.iconConfig.nodeTypes[`${problemType}_problem`]]
    } else if (backendNode.type === 'solution') {
      baseStyle = { ...this.styleConfig.solution.base }
      baseTags = [...this.tagConfig.nodeTypes.solution]
      baseIcons = [this.iconConfig.nodeTypes.solution]
      
      // 应用解决方案状态样式
      if (nodeState && this.styleConfig.solution.states[nodeState]) {
        Object.assign(baseStyle, this.styleConfig.solution.states[nodeState])
        baseTags.push(...this.tagConfig.states[nodeState])
      }
      
      // 添加状态图标
      if (nodeState && this.iconConfig.states[nodeState]) {
        baseIcons.push(this.iconConfig.states[nodeState])
      }
      
      // 检查是否为选中的解决方案
      if (this.isSelectedSolution(backendNode, parentNode)) {
        Object.assign(baseStyle, this.styleConfig.solution.selected)
        baseIcons.push(this.iconConfig.special.selected_solution)
        baseTags.push(...this.tagConfig.special.selected)
      }
    }
    
    // 应用智能体操作状态
    if (context.agentOperatingNodeId === backendNode.id) {
      baseIcons.push(this.iconConfig.special.agent_operating)
      baseStyle.borderColor = MODERN_COLORS.warning[500]
      baseStyle.borderWidth = '3px'
      baseStyle.boxShadow = `0 0 0 2px ${MODERN_COLORS.warning[500]}30`
      // 添加特殊属性，用于 CSS 选择器
      mindElixirNode.data = {
        ...mindElixirNode.data,
        'agent-operating': 'true'
      }
    }
    
    // 应用快照查看状态
    if (context.isSnapshotView) {
      baseIcons.push(this.iconConfig.special.snapshot_view)
      baseStyle.opacity = '0.8'
      baseStyle.filter = 'grayscale(0.2)'
    }
    
    // 检查节点是否在选中的解决方案路径上（是否启用）
    if (context.snapshotData) {
      const isNodeEnabled = this.isNodeInSelectedPath(context.snapshotData.roots, backendNode.id)
      if (isNodeEnabled === false) {
        // 节点被弃用，应用弃用样式
        Object.assign(baseStyle, this.styleConfig.common.deprecated)
        baseIcons.push(this.iconConfig.states.deprecated)
        baseTags.push(...this.tagConfig.states.deprecated)
      }
    }
    
    // 设置节点属性
    mindElixirNode.style = baseStyle
    mindElixirNode.tags = baseTags.length > 0 ? baseTags : undefined
    mindElixirNode.icons = baseIcons.length > 0 ? baseIcons : undefined
  }
  
  /**
   * 获取节点类型
   * @param {Object} node - 节点数据
   * @returns {string} 节点类型
   */
  getNodeType(node) {
    if (node.type === 'solution') {
      return 'solution'
    } else if (node.type === 'problem') {
      return node.problem_type === 'implementation' ? 'implementation_problem' : 'conditional_problem'
    }
    return 'implementation_problem' // 默认
  }
  
  /**
   * 获取节点状态
   * @param {Object} node - 节点数据
   * @returns {string|null} 节点状态
   */
  getNodeState(node) {
    if (node.type === 'solution') {
      return node.state || 'pending'
    }
    return null
  }
  
  /**
   * 检查是否为选中的解决方案
   * @param {Object} solutionNode - 解决方案节点
   * @param {Object} parentNode - 父问题节点
   * @returns {boolean} 是否为选中的解决方案
   */
  isSelectedSolution(solutionNode, parentNode) {
    if (!solutionNode || solutionNode.type !== 'solution' || !parentNode) {
      return false
    }
    
    // 检查父问题的selected_solution_id是否匹配
    return parentNode.selected_solution_id === solutionNode.id
  }
  
  /**
   * 获取主题配置
   * @param {Object} context - 转换上下文
   * @returns {Object} 主题配置
   */
  getTheme(context) {
    if (context.isSnapshotView) {
      return {
        name: 'Snapshot',
        palette: [
          MODERN_COLORS.neutral[400],
          MODERN_COLORS.neutral[500],
          MODERN_COLORS.neutral[600],
          MODERN_COLORS.neutral[700],
          MODERN_COLORS.neutral[800]
        ],
        cssVar: {
          '--main-color': MODERN_COLORS.neutral[700],
          '--main-bgcolor': MODERN_COLORS.neutral[50],
          '--color': MODERN_COLORS.neutral[600],
          '--bgcolor': MODERN_COLORS.neutral[100]
        }
      }
    }
    
    return {
      name: 'ModernResearchTree',
      palette: [
        MODERN_COLORS.primary[500],
        MODERN_COLORS.success[500],
        MODERN_COLORS.warning[500],
        MODERN_COLORS.error[500],
        MODERN_COLORS.purple[500]
      ],
      cssVar: {
        '--main-color': MODERN_COLORS.neutral[800],
        '--main-bgcolor': '#ffffff',
        '--color': MODERN_COLORS.neutral[600],
        '--bgcolor': MODERN_COLORS.neutral[50]
      }
    }
  }
  
  /**
   * 创建空的思维导图数据
   * @returns {Object} 空的Mind-elixir数据
   */
  createEmptyMindMap() {
    return {
      nodeData: {
        id: 'empty-root',
        topic: '暂无研究树数据',
        root: true,
        style: {
          background: MODERN_COLORS.neutral[100],
          color: MODERN_COLORS.neutral[600],
          borderColor: MODERN_COLORS.neutral[300],
          fontSize: '16px',
          fontWeight: '500',
          borderRadius: '8px',
          padding: '16px 20px'
        },
        icons: ['📭'],
        children: []
      },
      theme: this.getTheme({})
    }
  }
  
  /**
   * 分析并提取选中的解决方案ID
   * @param {Object} snapshotData - 快照数据
   * @returns {Array} 选中的解决方案ID列表
   */
  extractSelectedSolutionIds(snapshotData) {
    const selectedIds = []
    
    const traverse = (nodes) => {
      if (!nodes) return
      
      nodes.forEach(node => {
        if (node.type === 'problem' && node.selected_solution_id) {
          selectedIds.push(node.selected_solution_id)
        }
        if (node.children) {
          traverse(node.children)
        }
      })
    }
    
    if (snapshotData && snapshotData.roots) {
      traverse(snapshotData.roots)
    }
    
    return selectedIds
  }
  
  /**
   * 判断节点是否在被选中的解决方案路径上
   * 只有在被选中的解决方案路径上的节点才被认为是启用的
   * @param {Array} nodes - 要搜索的节点数组
   * @param {string} targetNodeId - 目标节点ID
   * @param {boolean} isInSelectedPath - 当前路径是否在被选中的路径上（递归参数）
   * @returns {boolean} 节点是否在被选中的路径上
   */
  isNodeInSelectedPath(nodes, targetNodeId, isInSelectedPath = true) {
    for (const node of nodes) {
      // 如果找到目标节点，返回当前路径状态
      if (node.id === targetNodeId) {
        return isInSelectedPath
      }
      
      // 如果当前节点是问题节点且有子节点
      if (node.type === 'problem' && node.children && node.children.length > 0) {
        // 对于问题节点，只有被选中的解决方案子节点才在选中路径上
        for (const child of node.children) {
          if (child.type === 'solution') {
            // 检查这个解决方案是否被选中
            const childIsInSelectedPath = isInSelectedPath && (node.selected_solution_id === child.id)
            const result = this.isNodeInSelectedPath([child], targetNodeId, childIsInSelectedPath)
            if (result !== null) return result
          } else {
            // 对于非解决方案子节点（如果有的话），保持当前路径状态
            const result = this.isNodeInSelectedPath([child], targetNodeId, isInSelectedPath)
            if (result !== null) return result
          }
        }
      } else if (node.children && node.children.length > 0) {
        // 对于其他类型的节点，保持当前路径状态
        const result = this.isNodeInSelectedPath(node.children, targetNodeId, isInSelectedPath)
        if (result !== null) return result
      }
    }
    return null // 没有找到目标节点
  }
}
