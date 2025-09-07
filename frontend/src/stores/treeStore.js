import { defineStore } from 'pinia'
import { apiService } from '../services/apiService'
import { ResearchTreeTransformer } from '../services/ResearchTreeTransformer'

export const useTreeStore = defineStore('tree', {
  state: () => ({
    // 当前快照数据，结构与后端一致
    currentSnapshot: null,

    // 临时快照数据（查看快照时使用）
    tempSnapshotData: null,

    // 智能体正在操作的节点ID（为空值代表智能体不在执行，为"-"代表当前正在传输系统消息）
    agentOperatingNodeId: null,

    // 加载状态
    isLoading: false,

    // 错误信息
    error: null
  }),

  getters: {
    /**
     * 获取显示的快照数据
     * 每次都重新生成，不使用缓存
     */
    getDisplaySnapshotData: (state) => {
      // 获取要显示的数据源
      let snapshotData = null
      let isSnapshotView = false

      if (state.tempSnapshotData && Object.keys(state.tempSnapshotData).length > 0) {
        // 如果正在查看临时快照，使用临时快照数据
        snapshotData = state.tempSnapshotData
        isSnapshotView = true
      } else if (state.currentSnapshot && Object.keys(state.currentSnapshot).length > 0) {
        // 否则使用当前快照数据
        snapshotData = state.currentSnapshot
        isSnapshotView = false
      }

      // 如果没有快照数据，返回null
      if (!snapshotData || !snapshotData.roots || snapshotData.roots.length === 0) {
        const store = useTreeStore()
        store._syncCurrentSnapshot()
        return null
      }

      // 使用transformer重新生成mindElixirData
      try {
        const transformer = new ResearchTreeTransformer()
        const context = {
          isSnapshotView: isSnapshotView,
          agentOperatingNodeId: state.agentOperatingNodeId
        }
        return transformer.transformToMindElixir(snapshotData, context)
      } catch (error) {
        console.error('生成Mind-elixir数据失败:', error)
        return null
      }
    },

    /**
     * 获取当前快照数据
     * 若为null则触发同步当前快照并返回null
     */
    getCurrentSnapshot: (state) => {
      if (state.currentSnapshot === null) {
        // 触发同步但立即返回null
        const store = useTreeStore()
        store._syncCurrentSnapshot()
        return null
      }
      return state.currentSnapshot
    },

    /**
     * 返回是否正在查看快照
     * tempSnapshotData是否不为空值，如果tempSnapshotData为null则触发同步临时快照并返回null
     */
    getIsViewingSnapshot: (state) => {
      if (state.tempSnapshotData === null) {
        // 触发同步临时快照但立即返回false
        const store = useTreeStore()
        store._syncTempSnapshot()
        return false
      }
      // 如果不为null但为{}，则返回false
      if (Object.keys(state.tempSnapshotData).length === 0) {
        return false
      }
      return true
    },

    /**
     * 返回智能体操作中的节点ID
     */
    getAgentOperatingNodeId: (state) => state.agentOperatingNodeId,

    /**
     * 根据节点ID获取智能体名称
     * @param {string} nodeId - 节点ID
     * @returns {string} 智能体名称
     */
    getAgentNameByNodeId: (state) => (nodeId) => {
      if (!nodeId) {
        return "智能体"
      }

      if (nodeId === "-") {
        return "系统消息"
      }

      // 如果当前快照不存在，返回null
      if (state.currentSnapshot === null) {
        const treeStore = useTreeStore()
        treeStore._syncCurrentSnapshot()
        return "智能体"
      }

      const node = useTreeStore()._findNodeById(state.currentSnapshot.roots, nodeId)
      if (!node) {
        return "未知专家"
      }

      // 如果是解决方案节点，获取其父问题节点
      if (node.type === "solution") {
        const parentProblemId = useTreeStore()._findParentNodeId(state.currentSnapshot.roots, nodeId)
        if (parentProblemId) {
          const parentProblem = useTreeStore()._findNodeById(state.currentSnapshot.roots, parentProblemId)
          if (parentProblem) {
            return `「${parentProblem.title}」问题的负责专家`
          }
        }
      }

      // 如果是问题节点，直接使用
      if (node.type === "problem") {
        return `「${node.title}」问题的负责专家`
      }

      return "未知专家"
    },

    /**
     * 获取当前智能体名称
     * 将智能体操作中的问题节点标题组装为智能体名称
     * 如果id是方案节点，则找到其父问题节点
     * 如果agentOperatingNodeId为"-"，则返回"系统消息"
     */
    getCurrentAgentName: (state) => {
      if (state.agentOperatingNodeId === null) {
        return null
      }

      const store = useTreeStore()
      return store.getAgentNameByNodeId(state.agentOperatingNodeId)
    },

    /**
     * 获取当前研究树中所有解决方案节点的标题
     * @param {boolean} onlySelectedSolution - 如果为true，则只搜索选中的解决方案及其下级节点
     */
    getAllSolutionTitles: (state) => (onlySelectedSolution = true) => {
      if (state.currentSnapshot === null) {
        const store = useTreeStore()
        store._syncCurrentSnapshot()
        return []
      }

      const titles = []
      const findSolutionTitles = (nodes, parentNode = null) => {
        for (const node of nodes) {
          // 如果只搜索选中的解决方案，且当前是解决方案节点，且父节点是问题节点
          // 则检查该解决方案是否被选中，如果未被选中则跳过
          if (onlySelectedSolution && node.type === "solution" && parentNode && 
              parentNode.type === "problem" && parentNode.selected_solution_id !== node.id) {
            continue
          }
          
          if (node.type === "solution") {
            titles.push(node.title)
          }
          
          if (node.children) {
            findSolutionTitles(node.children, node)
          }
        }
      }

      if (state.currentSnapshot.roots) {
        findSolutionTitles(state.currentSnapshot.roots)
      }
      return titles
    },

    /**
     * 获取当前研究树所有实施问题节点的标题
     * @param {boolean} onlySelectedSolution - 如果为true，则只搜索选中的解决方案及其下级节点
     */
    getAllImplementaionProblemTitles: (state) => (onlySelectedSolution = true) => {
      if (state.currentSnapshot === null) {
        const store = useTreeStore()
        store._syncCurrentSnapshot()
        return []
      }

      const titles = []
      const findImplementationProblemTitles = (nodes, parentNode = null) => {
        for (const node of nodes) {
          if (node.type === "problem" && node.problem_type === "implementation") {
            titles.push(node.title)
          }
          if (onlySelectedSolution && node.type === "solution" && parentNode && 
              parentNode.type === "problem" && parentNode.selected_solution_id !== node.id) {
            continue
          }
          
          if (node.children) {
            findImplementationProblemTitles(node.children, node)
          }
        }
      }

      if (state.currentSnapshot.roots) {
        findImplementationProblemTitles(state.currentSnapshot.roots)
      }
      return titles
    },

    /**
     * 根据标题得到节点id
     * @param {string} title - 节点标题
     * @param {boolean} onlySelectedSolution - 如果为true，则只搜索选中的解决方案及其下级节点
     * @returns {string|null} 节点ID
     */
    getNodeIdByTitle: (state) => (title, onlySelectedSolution = true) => {
      if (state.currentSnapshot === null) {
        const store = useTreeStore()
        store._syncCurrentSnapshot()
        return null
      }

      if (state.currentSnapshot.roots) {
        const store = useTreeStore()
        const nodeId = store._findNodeByTitle(state.currentSnapshot.roots, title, null, [], onlySelectedSolution)
        if (nodeId) {
          return nodeId
        }
      }
      return null
    },
    
    /**
     * 检查节点标题是否已存在
     * @param {string} title - 节点标题
     * @param {string[]} excludeNodeIds - 排除的节点ID列表
     * @param {boolean} onlySelectedSolution - 如果为true，则只搜索选中的解决方案及其下级节点
     * @returns {boolean} 标题是否存在
     */
    getIsNodeTitleExists: (state) => (title, excludeNodeIds = [], onlySelectedSolution = true) => {
      const store = useTreeStore()
      if (state.currentSnapshot === null) {
        store._syncCurrentSnapshot()
        return true
      }
      return store._findNodeByTitle(state.currentSnapshot.roots, title, null, excludeNodeIds, onlySelectedSolution) !== null
    },

    /**
     * 根据节点ID获取节点类型
     */
    getNodeType: (state) => (nodeId) => {
      if (!nodeId || !state.currentSnapshot) return null
      const node = useTreeStore()._findNodeById(state.currentSnapshot.roots, nodeId)
      return node ? node.type : null
    },

    /**
     * 判断问题节点的问题类型
     */
    getProblemNodeType: (state) => (problemNodeId) => {
      if (!problemNodeId || !state.currentSnapshot) return null
      const node = useTreeStore()._findNodeById(state.currentSnapshot.roots, problemNodeId)
      return node ? node.problem_type : null
    },


    /**
     * 根据解决方案ID获取解决方案面板所需数据
     * @param {string} solutionId - 解决方案ID
     * @returns {Object|null} 解决方案数据
     */
    getSolutionPanelData: (state) => (solutionId) => {
      if (!solutionId || !state.currentSnapshot) return null

      const solutionNode = useTreeStore()._findNodeById(state.currentSnapshot.roots, solutionId)
      if (!solutionNode || solutionNode.type !== "solution") {
        return null
      }

      const parentProblemId = useTreeStore()._findParentNodeId(state.currentSnapshot.roots, solutionId)
      if (!parentProblemId) {
        console.error('无法找到解决方案的父问题节点:', solutionId)
        return null
      }

      const parentProblemNode = useTreeStore()._findNodeById(state.currentSnapshot.roots, parentProblemId)
      const isSelected = parentProblemNode?.selected_solution_id === solutionId

      // 提取子问题，并转换为ProblemRequest格式
      const childrenProblems = (solutionNode.children || []).map(child => ({
        id: child.id,
        title: child.title,
        significance: child.significance,
        criteria: child.criteria,
        problem_type: child.problem_type
      }))

      return {
        id: solutionNode.id,
        title: solutionNode.title,
        top_level_thoughts: solutionNode.top_level_thoughts,
        implementation_plan: solutionNode.implementation_plan,
        plan_justification: solutionNode.plan_justification,
        state: solutionNode.state,
        final_report: solutionNode.final_report,
        selected: isSelected,
        children: childrenProblems,
        parentProblemId: parentProblemId, // 添加父问题ID
      }
    },

    /**
     * 判断节点是否为根研究问题
     * @param {string} nodeId - 节点ID
     * @returns {boolean} 是否为根研究问题
     */
    getIsRootProblem: (state) => (nodeId) => {
      if (!nodeId || !state.currentSnapshot) return false
      
      // 检查是否在根节点列表中
      const rootNode = state.currentSnapshot.roots?.find(root => root.id === nodeId)
      return rootNode && rootNode.type === 'problem'
    },

    /**
     * 根据根问题ID获取根问题面板所需数据
     * @param {string} problemId - 根问题ID，如果为null则返回空数据用于创建
     * @returns {Object|null} 根问题数据
     */
    getRootProblemPanelData: (state) => (problemId) => {
      if (!state.currentSnapshot) return null
      
      if (!problemId) {
        // 创建模式：返回空数据
        return {
          id: null,
          title: '',
          significance: '',
          criteria: '',
          problem_type: 'implementation' // 根问题默认为实施问题
        }
      }
      
      const rootNode = state.currentSnapshot.roots?.find(root => root.id === problemId)
      if (!rootNode || rootNode.type !== 'problem') {
        return null
      }
      
      return {
        id: rootNode.id,
        title: rootNode.title,
        significance: rootNode.significance,
        criteria: rootNode.criteria,
        problem_type: rootNode.problem_type
      }
    },

    /**
     * 判断节点是否启用（只有在被选中的解决方案路径上的节点才被认为是启用的）
     * @param {string} nodeId - 节点ID
     * @returns {boolean} 节点是否启用
     */
    getIsNodeEnabled: (state) => (nodeId) => {
      if (!nodeId || !state.currentSnapshot) return false
      
      const store = useTreeStore()
      return store._isNodeInSelectedPath(state.currentSnapshot.roots, nodeId)
    },

    /**
     * 返回加载状态
     */
    getIsLoading: (state) => state.isLoading
  },

  actions: {
    // 设置加载状态
    setLoading(loading) {
      this.isLoading = loading
    },

    // 设置错误信息
    setError(error) {
      this.error = error
    },

    // 清除错误信息
    clearError() {
      this.error = null
    },

    /**
     * 工具方法：根据ID递归查找节点
     */
    _findNodeById(nodes, targetId) {
      if (!nodes || !Array.isArray(nodes)) {
        return null
      }
      for (const node of nodes) {
        if (node.id === targetId) {
          return node
        }
        if (node.children) {
          const result = this._findNodeById(node.children, targetId)
          if (result) return result
        }
      }
      return null
    },

    /**
     * 根据标题递归查找节点
     * @param {Array} nodes - 要搜索的节点数组
     * @param {string} targetTitle - 目标标题
     * @param {string[]} excludeNodeIds - 排除的节点ID列表
     * @param {boolean} onlySelectedSolution - 如果为true，则只搜索选中的解决方案及其下级节点
     * @returns {string|null} 找到的节点ID
     */
    _findNodeByTitle(nodes, targetTitle, parrentNode = null, excludeNodeIds = [], onlySelectedSolution = true) {
      console.log("用标题找节点，排除节点：", excludeNodeIds)
      for (const node of nodes) {
        
        // 如果只搜索选中的解决方案，且当前是解决方案节点，检查是否被选中
        if (onlySelectedSolution && node.type === "solution") {
          if (parrentNode.selected_solution_id !== node.id) {
            continue // 跳过未被选中的解决方案
          }
        }
        
        if (node.title === targetTitle) {
          if (!excludeNodeIds.includes(node.id)) {
              console.log("找到节点：", node.id, node.title)
              return node.id
          }
        }
        
        if (node.children) {
          const result = this._findNodeByTitle(node.children, targetTitle, node, excludeNodeIds, onlySelectedSolution)
          if (result) return result
        }
      }
      return null
    },

    /**
     * 工具方法：查找父节点ID
     */
    _findParentNodeId(nodes, targetId, parentId = null) {
      if (!nodes || !Array.isArray(nodes)) {
        return null
      }
      for (const node of nodes) {
        if (node.id === targetId) {
          return parentId
        }
        if (node.children) {
          const result = this._findParentNodeId(node.children, targetId, node.id)
          if (result !== null) return result
        }
      }
      return null
    },

    /**
     * 同步当前快照（内部接口）
     * 1. 调用/research-tree/snapshots/current-id获取current_snapshot_id
     * 2. 调用/research-tree/snapshots/{snapshot_id}获取真实快照，更新currentSnapshot
     * 3. 同步临时快照（传入空值）
     * 4. agentOperatingNodeId设置为空值
     */
    async _syncCurrentSnapshot() {
      // 如果正在同步中，直接返回
      if (this.isLoading) {
        return
      }

      try {
        this.setLoading(true)
        this.clearError()

        // 1. 获取当前快照ID
        console.log('获取当前快照ID...')
        const snapshotIdResponse = await apiService.get('/research-tree/snapshots/current-id')
        console.log('快照ID API响应:', snapshotIdResponse)

        if (!snapshotIdResponse.success || !snapshotIdResponse.data?.current_snapshot_id) {
          console.warn('当前工程没有快照数据')
          this.currentSnapshot = {}
          this.agentOperatingNodeId = null
          await this._syncTempSnapshot()
          return
        }

        const snapshotId = snapshotIdResponse.data.current_snapshot_id
        console.log('获取到快照ID:', snapshotId)

        // 2. 获取真实快照数据
        console.log('获取快照数据...')
        const snapshotResponse = await apiService.get(`/research-tree/snapshots/${snapshotId}`)
        console.log('快照数据API响应:', snapshotResponse)

        if (snapshotResponse.success && snapshotResponse.data) {
          this.currentSnapshot = snapshotResponse.data
          console.log('设置当前快照:', this.currentSnapshot)
        } else {
          console.log('快照数据响应无效，使用空对象')
          this.currentSnapshot = {}
        }

        // 3. 同步临时快照（传入空值）
        await this._syncTempSnapshot()

        // 4. agentOperatingNodeId设置为空值
        this.agentOperatingNodeId = null

      } catch (error) {
        console.error('同步当前快照失败:', error)
        this.setError('同步研究树数据失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    /**
     * 同步临时快照（内部接口）
     * 传入快照id（可空）（tempSnapshotData为null时代表尚未同步）
     * 1. 如果id为空，设置tempSnapshotData为{}
     * 2. 如果id不为空，调用/research-tree/snapshots/{snapshot_id}获取快照，更新tempSnapshotData
     *    并调用ResearchTreeTransformer，用tempSnapshotData生成mindElixirData
     */
    async _syncTempSnapshot(snapshotId = null) {
      // 如果正在同步中，直接返回
      if (this.isLoading) {
        return
      }

      try {
        this.setLoading(true)
        this.clearError()

        if (snapshotId === null) {
          // 如果id为空，使用currentSnapshot生成mindElixirData
          this.tempSnapshotData = {}
        } else {
          // 如果id不为空，获取快照数据
          const snapshotResponse = await apiService.get(`/research-tree/snapshots/${snapshotId}`)

          if (snapshotResponse.success && snapshotResponse.data) {
            this.tempSnapshotData = snapshotResponse.data
          } else {
            this.tempSnapshotData = {}
          }
        }

      } catch (error) {
        console.error('同步临时快照失败:', error)
        this.setError('同步临时快照失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    /**
     * 查看快照（临时显示）
     * 调用同步临时快照，传入snapshotId
     */
    async viewSnapshot(snapshotId) {
      try {
        this.clearError()

        await this._syncTempSnapshot(snapshotId)

      } catch (error) {
        console.error('查看快照失败:', error)
        this.setError('查看快照失败')
        throw error
      }
    },

    /**
     * 退出查看态
     * 调用同步临时快照，传入空值
     */
    async exitSnapshotView() {
      try {
        this.clearError()

        await this._syncTempSnapshot(null)

      } catch (error) {
        console.error('退出快照查看失败:', error)
        this.setError('退出快照查看失败')
        throw error
      }
    },

    /**
     * 设置选中节点（这里先实现一个基础版本，后续可扩展）
     */

    /**
     * 设置智能体操作节点
     */
    setAgentOperatingNode(nodeId) {
      this.agentOperatingNodeId = nodeId
    },

    /**
     * 接收SSE快照更新并覆盖currentSnapshot
     */
    updateCurrentSnapshot(snapshotData) {
      this.currentSnapshot = snapshotData
    },

    /**
     * 判断节点是否在被选中的解决方案路径上
     * 只有在被选中的解决方案路径上的节点才被认为是启用的
     * @param {Array} nodes - 要搜索的节点数组
     * @param {string} targetNodeId - 目标节点ID
     * @param {boolean} isInSelectedPath - 当前路径是否在被选中的路径上（递归参数）
     * @returns {boolean} 节点是否在被选中的路径上
     */
    _isNodeInSelectedPath(nodes, targetNodeId, isInSelectedPath = true) {
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
              const result = this._isNodeInSelectedPath([child], targetNodeId, childIsInSelectedPath)
              if (result !== null) return result
            } else {
              // 对于非解决方案子节点（如果有的话），保持当前路径状态
              const result = this._isNodeInSelectedPath([child], targetNodeId, isInSelectedPath)
              if (result !== null) return result
            }
          }
        } else if (node.children && node.children.length > 0) {
          // 对于其他类型的节点，保持当前路径状态
          const result = this._isNodeInSelectedPath(node.children, targetNodeId, isInSelectedPath)
          if (result !== null) return result
        }
      }
      return null // 没有找到目标节点
    },

    /**
     * 强制重新同步当前快照
     * 用于需要强制刷新研究树数据的场景
     */
    async refreshCurrentSnapshot() {
      await this._syncCurrentSnapshot()
    },
  }
})
