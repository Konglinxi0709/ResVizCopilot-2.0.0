import { defineStore } from 'pinia'

export const useUIStore = defineStore('ui', {
  state: () => ({
    // 主题设置
    theme: 'light', // 'light' | 'dark'
    
    // 语言设置
    language: 'zh-CN', // 'zh-CN' | 'en-US'
    
    // 面板折叠状态
    leftPanelCollapsed: false,
    rightPanelCollapsed: false,
    
    // 全局加载状态
    isLoading: false,
    loadingText: '',
    
    // 错误信息
    error: null,
    
    // 通知设置
    notifications: {
      success: true,
      warning: true,
      error: true,
      info: true
    },
    
    // 界面尺寸设置
    sidebarWidth: 300,
    headerHeight: 60,
    
    // 响应式断点
    isMobile: false,
    isTablet: false,
    isDesktop: true
  }),
  
  getters: {
    // 检查是否为暗色主题
    isDarkTheme: (state) => {
      return state.theme === 'dark'
    },
    
    // 检查是否为中文
    isChinese: (state) => {
      return state.language === 'zh-CN'
    },
    
    // 检查是否有面板折叠
    hasCollapsedPanel: (state) => {
      return state.leftPanelCollapsed || state.rightPanelCollapsed
    },
    
    // 获取当前设备类型
    deviceType: (state) => {
      if (state.isMobile) return 'mobile'
      if (state.isTablet) return 'tablet'
      return 'desktop'
    },
    
    // 检查是否可以显示侧边栏
    canShowSidebar: (state) => {
      return !state.isMobile
    }
  },
  
  actions: {
    // 设置主题
    setTheme(theme) {
      this.theme = theme
      this.applyTheme(theme)
    },
    
    // 应用主题到DOM
    applyTheme(theme) {
      document.documentElement.setAttribute('data-theme', theme)
      
      // 更新meta标签颜色
      const metaThemeColor = document.querySelector('meta[name="theme-color"]')
      if (metaThemeColor) {
        metaThemeColor.setAttribute('content', theme === 'dark' ? '#1a1a1a' : '#ffffff')
      }
    },
    
    // 切换主题
    toggleTheme() {
      const newTheme = this.theme === 'light' ? 'dark' : 'light'
      this.setTheme(newTheme)
    },
    
    // 设置语言
    setLanguage(language) {
      this.language = language
      
      // 更新HTML lang属性
      document.documentElement.setAttribute('lang', language)
    },
    
    // 切换语言
    toggleLanguage() {
      const newLanguage = this.language === 'zh-CN' ? 'en-US' : 'zh-CN'
      this.setLanguage(newLanguage)
    },
    
    // 设置左侧面板折叠状态
    setLeftPanelCollapsed(collapsed) {
      this.leftPanelCollapsed = collapsed
    },
    
    // 切换左侧面板
    toggleLeftPanel() {
      this.leftPanelCollapsed = !this.leftPanelCollapsed
    },
    
    // 设置右侧面板折叠状态
    setRightPanelCollapsed(collapsed) {
      this.rightPanelCollapsed = collapsed
    },
    
    // 切换右侧面板
    toggleRightPanel() {
      this.rightPanelCollapsed = !this.rightPanelCollapsed
    },
    
    // 设置加载状态
    setLoading(loading, text = '') {
      this.isLoading = loading
      this.loadingText = text
    },
    
    // 设置错误信息
    setError(error) {
      this.error = error
    },
    
    // 清除错误信息
    clearError() {
      this.error = null
    },
    
    // 设置通知配置
    setNotificationConfig(type, enabled) {
      if (Object.prototype.hasOwnProperty.call(this.notifications, type)) {
        this.notifications[type] = enabled
      }
    },
    
    // 设置侧边栏宽度
    setSidebarWidth(width) {
      this.sidebarWidth = Math.max(200, Math.min(500, width))
    },
    
    // 更新响应式状态
    updateResponsiveState() {
      const width = window.innerWidth
      
      this.isMobile = width < 768
      this.isTablet = width >= 768 && width < 1200
      this.isDesktop = width >= 1200
      
      // 在移动端自动折叠面板
      if (this.isMobile) {
        this.leftPanelCollapsed = true
        this.rightPanelCollapsed = true
      }
    },
    
    // 初始化UI设置
    initializeUI() {
      // 应用主题
      this.applyTheme(this.theme)
      
      // 设置语言
      this.setLanguage(this.language)
      
      // 更新响应式状态
      this.updateResponsiveState()
      
      // 监听窗口大小变化
      window.addEventListener('resize', () => {
        this.updateResponsiveState()
      })
      
      // 监听系统主题变化
      if (window.matchMedia) {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
        mediaQuery.addEventListener('change', () => {
          // 可选：自动跟随系统主题
          // this.setTheme(e.matches ? 'dark' : 'light')
        })
      }
    },
    
    // 重置UI设置
    resetUI() {
      this.theme = 'light'
      this.language = 'zh-CN'
      this.leftPanelCollapsed = false
      this.rightPanelCollapsed = false
      this.isLoading = false
      this.loadingText = ''
      this.error = null
      this.sidebarWidth = 300
      
      this.initializeUI()
    }
  },
  
  // 持久化配置
  persist: {
    key: 'resviz-ui-store',
    storage: localStorage,
    paths: [
      'theme', 
      'language', 
      'leftPanelCollapsed', 
      'rightPanelCollapsed',
      'notifications',
      'sidebarWidth'
    ]
  }
})