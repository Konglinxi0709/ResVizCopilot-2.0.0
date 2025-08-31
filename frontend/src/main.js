import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createI18n } from 'vue-i18n'
import App from './App.vue'
import { messages } from './locales'

// 先创建pinia实例
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

// 创建app并安装pinia
const app = createApp(App)
app.use(pinia)

// 获取UI Store来读取保存的语言设置
import { useUIStore } from './stores/uiStore'
const uiStore = useUIStore()

// 使用保存的语言设置创建i18n实例
const i18n = createI18n({
  locale: uiStore.language || 'zh-CN',
  fallbackLocale: 'en-US',
  messages
})

app.use(ElementPlus)
app.use(i18n)

// 应用启动后初始化UI设置
app.mount('#app')

// 初始化UI设置（需要在mount后执行）
uiStore.initializeUI()