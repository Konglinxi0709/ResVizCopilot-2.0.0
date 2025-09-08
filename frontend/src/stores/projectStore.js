import { defineStore } from 'pinia'
import { apiService } from '../services/apiService'

export const useProjectStore = defineStore('project', {
  state: () => ({
    // 当前工程信息（/projects/current/info接口数据，包含name、created_at、updated_at三个字段）
    currentProject: null,

    // 工程列表（数组类型，/projects接口数据）
    projectList: null,

    // 加载状态
    isLoading: false,

    // 错误信息
    error: null
  }),

  getters: {
    /**
     * 获取当前工程对象
     * 若本地无数据则自动触发同步，立即返回null
     */
    getCurrentProject: (state) => {
      if (state.currentProject === null) {
        // 触发同步但立即返回null
        const store = useProjectStore()
        store._syncStore()
        return null
      }
      return state.currentProject
    },

    /**
     * 获取工程列表
     * 若本地无数据（为null）则自动触发同步，立即返回null
     */
    getProjectList: (state) => {
      if (state.projectList === null) {
        // 触发同步但立即返回null
        const store = useProjectStore()
        store._syncStore()
        return null
      }
      return state.projectList
    },

    /**
     * 检查工程名称是否已存在，用于表单校验
     */
    getIsProjectNameExists: (state) => (name) => {
      if (state.projectList === null) {
        // 触发同步但立即返回false
        const store = useProjectStore()
        store._syncStore()
        return false
      }
      return state.projectList.some(project => project.project_name === name)
    },

    /**
     * 返回currentProject.updated_at
     * 若为空值则视为"未保存"
     */
    getLastSaveTime: (state) => {
      if (state.currentProject === null) {
        // 触发同步但立即返回"未保存"
        const store = useProjectStore()
        store._syncStore()
        return "未保存"
      }
      return state.currentProject?.updated_at || "未保存"
    },

    /**
     * 返回加载状态，仅用于按钮禁用等UI逻辑
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
     * 同步整个存储（内部接口）
     * 1. /projects获取工程列表，更新projectList。projectList为null代表尚未同步
     * 2. /projects/current/info获取当前工程信息，更新currentProject。currentProject为null代表尚未同步
     */
    async _syncStore() {
      // 如果正在同步中，直接返回
      if (this.isLoading) {
        return
      }

      try {
        this.setLoading(true)
        this.clearError()

        // 并行获取工程列表和当前工程信息
        const [projectsResponse, currentProjectResponse] = await Promise.all([
          apiService.get('/projects'),
          apiService.get('/projects/current/info')
        ])

        // 更新工程列表
        console.log('工程列表API响应:', projectsResponse)
        if (projectsResponse.success && projectsResponse.projects) {
          // 处理包装后的响应
          this.projectList = projectsResponse.projects
          console.log('设置工程列表:', this.projectList)
        } else if (Array.isArray(projectsResponse)) {
          // 处理直接返回数组的情况
          this.projectList = projectsResponse
          console.log('设置工程列表(直接数组):', this.projectList)
      } else {
          console.log('工程列表响应无效，使用空数组')
          this.projectList = []
        }

        // 更新当前工程信息
        console.log('当前工程API响应:', currentProjectResponse)
        if (currentProjectResponse.success && currentProjectResponse.data) {
          // 处理包装后的响应
          this.currentProject = currentProjectResponse.data
          console.log('设置当前工程:', this.currentProject)
        } else if (currentProjectResponse.project_name) {
          // 处理直接返回的数据对象
          this.currentProject = currentProjectResponse
          console.log('设置当前工程(直接数据):', this.currentProject)
        } else {
          console.log('当前工程响应无效，使用空对象')
          this.currentProject = {}
        }

      } catch (error) {
        console.error('同步工程存储失败:', error)
        this.setError('同步工程数据失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    /**
     * 创建新工程
     * 调用/projects?project_name=接口，之后同步projectStore
     */
    async createProject(projectName) {
      console.log("正在创建工程：", projectName)
      try {
        this.clearError()

        const response = await apiService.post(`/projects?project_name=${encodeURIComponent(projectName)}`)

      if (response.success) {
            // 创建成功后同步整个存储
            await this._syncStore()
        return response
      } else {
        throw new Error(response.message || '创建工程失败')
        }

        } catch (error) {
          console.error('创建工程失败:', error)
          this.setError(error.message || '创建工程失败')
          throw error
      }
    },

    /**
     * 加载工程
     * 调用/projects/接口，直接更新currentProject，无需全部同步
     */
    async loadProject(projectName) {
      try {
        this.clearError()

        const response = await apiService.get(`/projects/${projectName}`)

      if (response.success) {
            // 只更新当前工程信息
            this.currentProject = {
              name: response.project_name || projectName,
          created_at: response.created_at,
          updated_at: response.updated_at
        }
        return response
      } else {
        throw new Error(response.message || '加载工程失败')
        }

        } catch (error) {
          console.error('加载工程失败:', error)
          this.setError('加载工程失败')
          throw error
      }
    },

    /**
     * 保存当前工程
     * 调用/projects/save接口，直接更新currentProject的updated_at，无需全部同步
     */
    async saveProject() {
      try {
        this.clearError()

        const response = await apiService.post('/projects/save')

      if (response.success) {
            // 更新当前工程的updated_at
            if (this.currentProject) {
              this.currentProject.updated_at = new Date().toISOString()
        }
        return response
      } else {
        throw new Error(response.message || '保存工程失败')
        }
      
        } catch (error) {
          console.error('保存工程失败:', error)
          this.setError('保存工程失败')
          throw error
      }
    },

    /**
     * 另存为工程
     * 调用/projects/save-as?new_project_name=接口，之后同步projectStore
     */
    async saveAsProject(newProjectName) {
      try {
        this.clearError()

        const response = await apiService.post(`/projects/save-as?new_project_name=${encodeURIComponent(newProjectName)}`)

      if (response.success) {
            // 另存为成功后同步整个存储
            await this._syncStore()
        return response
      } else {
        throw new Error(response.message || '另存为工程失败')
        }

        } catch (error) {
          console.error('另存为工程失败:', error)
          this.setError(error.message || '另存为工程失败')
          throw error
      }
    },

    /**
     * 删除工程
     * 调用delete /projects/接口，之后同步projectStore
     */
    async deleteProject(projectName) {
      try {
        this.clearError()

        await apiService.delete(`/projects/${projectName}`)

        // 删除成功后同步整个存储
        await this._syncStore()

      } catch (error) {
        console.error('删除工程失败:', error)
        this.setError('删除工程失败')
        throw error
      }
    },

    /**
     * 强制重新同步工程数据
     * 用于需要强制刷新工程数据的场景
     */
    async refreshProjects() {
      await this._syncStore()
    }
  }
})
