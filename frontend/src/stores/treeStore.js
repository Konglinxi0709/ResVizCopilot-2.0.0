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
     */
    getAllSolutionTitles: (state) => {
      if (state.currentSnapshot === null) {
        const store = useTreeStore()
        store._syncCurrentSnapshot()
        return []
      }

      const titles = []
      const findSolutionTitles = (nodes) => {
        for (const node of nodes) {
          if (node.type === "solution") {
            titles.push(node.title)
          }
          if (node.children) {
            findSolutionTitles(node.children)
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
     */
    getAllImplementaionProblemTitles: (state) => {
      if (state.currentSnapshot === null) {
        const store = useTreeStore()
        store._syncCurrentSnapshot()
        return []
      }

      const titles = []
      const findImplementationProblemTitles = (nodes) => {
        for (const node of nodes) {
          if (node.type === "problem" && node.problem_type === "implementation") {
            titles.push(node.title)
          }
          if (node.children) {
            findImplementationProblemTitles(node.children)
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
     */
    getNodeIdByTitle: (state) => (title) => {
      if (state.currentSnapshot === null) {
        const store = useTreeStore()
        store._syncCurrentSnapshot()
        return null
      }

      const findNodeByTitle = (nodes) => {
        for (const node of nodes) {
          if (node.title === title) {
            return node.id
          }
          if (node.children) {
            const result = findNodeByTitle(node.children)
            if (result) return result
          }
        }
        return null
      }

      if (state.currentSnapshot.roots) {
        return findNodeByTitle(state.currentSnapshot.roots)
      }
      return null
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
     * 强制重新同步当前快照
     * 用于需要强制刷新研究树数据的场景
     */
    async refreshCurrentSnapshot() {
      await this._syncCurrentSnapshot()
    },
  }
})
