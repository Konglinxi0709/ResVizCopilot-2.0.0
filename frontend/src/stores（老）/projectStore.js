import { defineStore } from 'pinia'
import { apiService } from '../services/apiService'

export const useProjectStore = defineStore('project', {
  state: () => ({
    // 当前工程信息
    currentProject: null,
    
    // 工程列表
    projectList: [],
    
    // 最后保存时间
    lastSaveTime: null,
    
    // 加载状态
    isLoading: false,
    
    // 错误信息
    error: null
  }),
  
  getters: {
    // 获取当前工程名称
    currentProjectName: (state) => {
      return state.currentProject?.name || null
    },
    
    // 检查是否有当前工程
    hasCurrentProject: (state) => {
      return !!state.currentProject
    },
    
    // 获取工程数量
    projectCount: (state) => {
      return state.projectList.length
    },
    
    // 检查工程名称是否已存在
    isProjectNameExists: (state) => {
      return (name) => {
        return state.projectList.some(project => project.name === name)
      }
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
    
    // 获取工程列表
    async fetchProjectList() {
      try {
        this.setLoading(true)
        this.clearError()
        
        const response = await apiService.get('/projects')
        
        // 处理后端返回的数据结构
        if (response.success && response.projects) {
          // 转换数据格式，将 project_name 转为 name，过滤掉无效数据
          this.projectList = response.projects
            .filter(project => project && project.project_name) // 过滤掉空值和缺少project_name的项
            .map(project => ({
              name: project.project_name,
              created_at: project.created_at,
              updated_at: project.updated_at,
              file_path: project.file_path
            }))
        } else {
          this.projectList = []
        }
        
        return this.projectList
      } catch (error) {
        console.error('获取工程列表失败:', error)
        this.setError('获取工程列表失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },
    
    // 创建新工程
    async createProject(projectName) {
      try {
        this.setLoading(true)
        this.clearError()
        
        // 检查工程名称是否已存在
        if (this.isProjectNameExists(projectName)) {
          throw new Error(`工程名称 "${projectName}" 已存在`)
        }
        
        const response = await apiService.post(`/projects?project_name=${encodeURIComponent(projectName)}`)
        
        const newProject = {
          name: response.project_name || projectName,
          created_at: response.created_at,
          updated_at: response.updated_at
        }
        
        // 更新工程列表（只有当newProject有效时才添加）
        if (newProject && newProject.name) {
          this.projectList.push(newProject)
        }
        
        // 设置为当前工程
        this.currentProject = newProject
        this.lastSaveTime = new Date()
        
        return newProject
      } catch (error) {
        console.error('创建工程失败:', error)
        this.setError(error.message || '创建工程失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },
    
    // 加载工程
    async loadProject(projectName) {
      try {
        this.setLoading(true)
        this.clearError()
        
        const response = await apiService.get(`/projects/${projectName}`)
        const project = {
          name: response.project_name || projectName,
          created_at: response.created_at,
          updated_at: response.updated_at
        }
        
        // 设置为当前工程
        this.currentProject = project
        this.lastSaveTime = new Date()
        
        return project
      } catch (error) {
        console.error('加载工程失败:', error)
        this.setError('加载工程失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },
    
    // 保存当前工程
    async saveProject() {
      try {
        if (!this.currentProject) {
          throw new Error('没有当前工程可保存')
        }
        
        this.setLoading(true)
        this.clearError()
        
        const response = await apiService.post('/projects/save')
        
        // 更新最后保存时间
        this.lastSaveTime = new Date()
        
        return response.data
      } catch (error) {
        console.error('保存工程失败:', error)
        this.setError('保存工程失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },
    
    // 另存为工程
    async saveAsProject(newProjectName) {
      try {
        this.setLoading(true)
        this.clearError()
        
        // 检查工程名称是否已存在
        if (this.isProjectNameExists(newProjectName)) {
          throw new Error(`工程名称 "${newProjectName}" 已存在`)
        }
        
        const response = await apiService.post(`/projects/save-as?new_project_name=${encodeURIComponent(newProjectName)}`)
        
        const newProject = {
          name: response.project_name || newProjectName,
          created_at: response.created_at,
          updated_at: response.updated_at
        }
        
        // 更新工程列表（只有当newProject有效时才添加）
        if (newProject && newProject.name) {
          this.projectList.push(newProject)
        }
        
        // 设置为当前工程
        this.currentProject = newProject
        this.lastSaveTime = new Date()
        
        return newProject
      } catch (error) {
        console.error('另存为工程失败:', error)
        this.setError(error.message || '另存为工程失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },
    
    // 删除工程
    async deleteProject(projectName) {
      try {
        this.setLoading(true)
        this.clearError()
        
        await apiService.delete(`/projects/${projectName}`)
        
        // 从工程列表中移除
        this.projectList = this.projectList.filter(
          project => project.name !== projectName
        )
        
        // 如果删除的是当前工程，清空当前工程
        if (this.currentProject?.name === projectName) {
          this.currentProject = null
          this.lastSaveTime = null
        }
        
        return true
      } catch (error) {
        console.error('删除工程失败:', error)
        this.setError('删除工程失败')
        throw error
      } finally {
        this.setLoading(false)
      }
    },
    
    // 设置当前工程
    setCurrentProject(project) {
      this.currentProject = project
      this.lastSaveTime = new Date()
    },
    
    // 清空当前工程
    clearCurrentProject() {
      this.currentProject = null
      this.lastSaveTime = null
    },
    
    // 获取当前工程信息
    async getCurrentProjectInfo() {
      try {
        const response = await apiService.get('/projects/current/info')
        return response.data
      } catch (error) {
        console.error('获取当前工程信息失败:', error)
        throw error
      }
    },
    
    // 获取当前工程完整数据
    async getCurrentProjectFullData() {
      try {
        const response = await apiService.get('/projects/current/full-data')
        return response.data
      } catch (error) {
        console.error('获取当前工程完整数据失败:', error)
        throw error
      }
    }
  },
  
  // 持久化配置
  persist: {
    key: 'resviz-project-store',
    storage: localStorage,
    paths: ['currentProject', 'lastSaveTime']
  }
})
