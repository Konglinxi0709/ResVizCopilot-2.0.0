import { defineStore } from 'pinia'
import { apiService } from '../services/apiService'

export const useTreeStore = defineStore('tree', {
  state: () => ({
    // 当前快照数据
    currentSnapshot: null,
    
    // Mind-elixir格式的数据
    mindElixirData: null,
    
    // 选中的节点ID
    selectedNodeId: null,
    
    // 是否正在查看快照
    isViewingSnapshot: false,
    
    // 临时快照ID（用于快照查看）
    tempSnapshotId: null,
    
    // 临时快照数据
    tempSnapshotData: null,
    
    // 智能体正在操作的节点ID
    agentOperatingNodeId: null,
    
    // 加载状态
    isLoading: false,
    
    // 错误信息
    error: null
  }),
  
  getters: {
    // 获取当前显示的快照数据（可能是当前快照或临时快照）
    displaySnapshotData: (state) => {
      return state.isViewingSnapshot ? state.tempSnapshotData : state.currentSnapshot
    },
    
    // 检查是否有快照数据
    hasSnapshotData: (state) => {
      return !!(state.currentSnapshot || state.tempSnapshotData)
    },
    
    // 检查是否有选中节点
    hasSelectedNode: (state) => {
      return !!state.selectedNodeId
    },
    
    // 检查智能体是否正在工作
    isAgentWorking: (state) => {
      return !!state.agentOperatingNodeId
    }
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
    
    // 加载当前快照
    async loadCurrentSnapshot() {
      try {
        this.setLoading(true)
        this.clearError()
        
        const response = await apiService.get('/research-tree/snapshots/current')
        this.currentSnapshot = response.data
        
        return this.currentSnapshot
      } catch (error) {
        console.error('加载当前快照失败:', error)
        this.setError('加载研究树数据失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },
    
    // 获取指定快照
    async getSnapshot(snapshotId) {
      try {
        const response = await apiService.get(`/research-tree/snapshots/${snapshotId}`)
        
        // 检查响应是否包含错误
        if (response.data && response.data.error) {
          throw new Error(response.data.error)
        }
        
        return response.data
      } catch (error) {
        console.error('获取快照失败:', error)
        throw error
      }
    },
    
    // 查看快照（临时显示）
    async viewSnapshot(snapshotId) {
      try {
        this.setLoading(true)
        this.clearError()
        
        // 获取快照数据
        const snapshotData = await this.getSnapshot(snapshotId)
        
        // 设置临时快照状态
        this.tempSnapshotId = snapshotId
        this.tempSnapshotData = snapshotData
        this.isViewingSnapshot = true
        
        return snapshotData
      } catch (error) {
        console.error('查看快照失败:', error)
        this.setError('查看快照失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },
    
    // 退出快照查看
    exitSnapshotView() {
      this.isViewingSnapshot = false
      this.tempSnapshotId = null
      this.tempSnapshotData = null
    },
    
    // 设置选中节点
    setSelectedNode(nodeId) {
      this.selectedNodeId = nodeId
    },
    
    // 清除选中节点
    clearSelectedNode() {
      this.selectedNodeId = null
    },
    
    // 设置智能体操作节点
    setAgentOperatingNode(nodeId) {
      this.agentOperatingNodeId = nodeId
    },
    
    // 清除智能体操作节点
    clearAgentOperatingNode() {
      this.agentOperatingNodeId = null
    },
    
    // 更新当前快照（当有新的数据库操作时）
    updateCurrentSnapshot(snapshotData) {
      this.currentSnapshot = snapshotData
      
      // 如果正在查看快照，退出快照查看模式
      if (this.isViewingSnapshot) {
        this.exitSnapshotView()
      }
    },
    
    // 设置Mind-elixir数据
    setMindElixirData(data) {
      this.mindElixirData = data
    },
    
    // 清除所有数据
    clearAllData() {
      this.currentSnapshot = null
      this.mindElixirData = null
      this.selectedNodeId = null
      this.isViewingSnapshot = false
      this.tempSnapshotId = null
      this.tempSnapshotData = null
      this.agentOperatingNodeId = null
      this.error = null
    },
    
    // 刷新当前快照
    async refreshCurrentSnapshot() {
      if (this.isViewingSnapshot) {
        // 如果正在查看快照，不刷新
        return
      }
      
      try {
        await this.loadCurrentSnapshot()
      } catch (error) {
        console.error('刷新快照失败:', error)
        // 不抛出错误，避免影响用户体验
      }
    }
  },
  
  // 持久化配置
  persist: {
    key: 'resviz-tree-store',
    storage: sessionStorage,
    paths: ['selectedNodeId']
  }
})
