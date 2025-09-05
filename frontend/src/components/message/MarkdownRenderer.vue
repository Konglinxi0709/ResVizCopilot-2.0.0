<template>
  <div :class="componentClass">
    <div v-html="renderedContent" class="markdown-content" @click="handleLinkClick"></div>
  </div>
</template>

<script>
import MarkdownIt from 'markdown-it'
import { useUIStore } from '@/stores/uiStore'

export default {
  name: 'MarkdownRenderer',
  
  props: {
    content: {
      type: String,
      default: ''
    },
    
    // 是否启用语法高亮
    enableHighlight: {
      type: Boolean,
      default: true
    },
    
    // 是否启用链接
    enableLinks: {
      type: Boolean,
      default: true
    },
    
    // 自定义CSS类
    customClass: {
      type: String,
      default: ''
    }
  },
  
  data() {
    return {
      uiStore: null,
      renderedContent: '',
      md: null
    }
  },
  
  computed: {
    isDarkTheme() {
      return this.uiStore?.isDarkTheme || false
    },
    
    // 渲染后的HTML内容
    htmlContent() {
      if (!this.content) return ''
      
      try {
        return this.md.render(this.content)
      } catch (error) {
        console.error('Markdown渲染失败:', error)
        return `<p>${this.escapeHtml(this.content)}</p>`
      }
    },
    
    // 组件CSS类
    componentClass() {
      const classes = ['markdown-renderer']
      
      if (this.isDarkTheme) {
        classes.push('dark-theme')
      }
      
      if (this.customClass) {
        classes.push(this.customClass)
      }
      
      return classes.join(' ')
    }
  },
  
  watch: {
    content: {
      handler() {
        this.updateRenderedContent()
      },
      immediate: false
    }
  },
  
  mounted() {
    this.uiStore = useUIStore()
    this.initMarkdownIt()
    // 初始化完成后再进行首次渲染，确保this.md已可用
    this.updateRenderedContent()
  },
  
  methods: {
    // 初始化MarkdownIt实例
    initMarkdownIt() {
      this.md = new MarkdownIt({
        html: false,
        linkify: this.enableLinks,
        typographer: true,
        breaks: true
      })
      
      // 配置插件
      if (this.enableHighlight) {
        this.configureHighlight()
      }
      
      // 配置链接处理
      if (this.enableLinks) {
        this.configureLinks()
      }
    },
    
    // 配置语法高亮
    configureHighlight() {
      // 这里可以添加语法高亮插件
      // 例如：highlight.js 或 prism.js
    },
    
    // 配置链接处理
    configureLinks() {
      // 自定义链接渲染
      const defaultRender = this.md.renderer.rules.link_open || function(tokens, idx, options, env, self) {
        return self.renderToken(tokens, idx, options)
      }
      
      this.md.renderer.rules.link_open = function (tokens, idx, options, env, self) {
        const token = tokens[idx]
        const hrefIndex = token.attrIndex('href')
        
        if (hrefIndex >= 0) {
          const href = token.attrs[hrefIndex][1]
          
          // 添加target="_blank"和rel="noopener noreferrer"
          token.attrPush(['target', '_blank'])
          token.attrPush(['rel', 'noopener noreferrer'])
          
          // 添加安全提示
          if (href.startsWith('http')) {
            token.attrPush(['title', `外部链接: ${href}`])
          }
        }
        
        return defaultRender(tokens, idx, options, env, self)
      }
    },
    
    // 更新渲染内容
    updateRenderedContent() {
      this.renderedContent = this.htmlContent
    },
    
    // HTML转义
    escapeHtml(text) {
      const div = document.createElement('div')
      div.textContent = text
      return div.innerHTML
    },
    
    // 处理链接点击
    handleLinkClick(event) {
      const link = event.target.closest('a')
      if (!link) return
      
      const href = link.getAttribute('href')
      if (!href) return
      
      // 如果是外部链接，使用默认行为
      if (href.startsWith('http')) {
        return
      }
      
      // 如果是内部链接，可以在这里处理
      event.preventDefault()
      console.log('内部链接点击:', href)
    }
  }
}
</script>

<style scoped>
.markdown-renderer {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.6;
  color: var(--text-color);
}

.markdown-content {
  word-wrap: break-word;
  overflow-wrap: break-word;
}

/* 标题样式 */
.markdown-content :deep(h1) {
  font-size: 2em;
  font-weight: 600;
  margin: 1em 0 0.5em 0;
  color: var(--text-color);
  border-bottom: 2px solid var(--border-color);
  padding-bottom: 0.5em;
}

.markdown-content :deep(h2) {
  font-size: 1.5em;
  font-weight: 600;
  margin: 1em 0 0.5em 0;
  color: var(--text-color);
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.3em;
}

.markdown-content :deep(h3) {
  font-size: 1.25em;
  font-weight: 600;
  margin: 1em 0 0.5em 0;
  color: var(--text-color);
}

/* 段落样式 */
.markdown-content :deep(p) {
  margin: 0.8em 0;
  line-height: 1.7;
}

/* 代码样式 */
.markdown-content :deep(pre) {
  background: var(--bg-color-light, #f6f8fa);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 16px;
  overflow-x: auto;
  margin: 1em 0;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 85%;
  line-height: 1.45;
}

.markdown-content :deep(code) {
  background: var(--bg-color-light, #f6f8fa);
  border-radius: 3px;
  padding: 2px 4px;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 85%;
}

.markdown-content :deep(.inline-code) {
  background: var(--bg-color-light, #f6f8fa);
  border-radius: 3px;
  padding: 2px 4px;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 85%;
  color: var(--danger-color, #d73a49);
}

.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
  border-radius: 0;
}

/* 列表样式 */
.markdown-content :deep(ul) {
  padding-left: 2em;
  margin: 1em 0;
}

.markdown-content :deep(ol) {
  padding-left: 2em;
  margin: 1em 0;
}

.markdown-content :deep(li) {
  margin: 0.5em 0;
  line-height: 1.7;
}

/* 引用样式 */
.markdown-content :deep(blockquote) {
  margin: 1em 0;
  padding: 0 1em;
  color: var(--text-color-secondary, #6a737d);
  border-left: 4px solid var(--border-color);
  background: var(--bg-color-light, #f6f8fa);
  border-radius: 0 6px 6px 0;
}

/* 链接样式 */
.markdown-content :deep(a) {
  color: var(--primary-color, #0366d6);
  text-decoration: none;
}

.markdown-content :deep(a:hover) {
  text-decoration: underline;
}

/* 分割线样式 */
.markdown-content :deep(hr) {
  height: 2px;
  padding: 0;
  margin: 24px 0;
  background-color: var(--border-color);
  border: 0;
}

/* 表格样式 */
.markdown-content :deep(table) {
  border-collapse: collapse;
  margin: 1em 0;
  width: 100%;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid var(--border-color);
  padding: 8px 12px;
  text-align: left;
}

.markdown-content :deep(th) {
  background: var(--bg-color-light, #f6f8fa);
  font-weight: 600;
}

/* 暗色主题样式 */
.dark-theme .markdown-content :deep(pre) {
  background: var(--bg-color-dark, #0d1117);
  border-color: var(--border-color-dark, #30363d);
}

.dark-theme .markdown-content :deep(.inline-code) {
  background: var(--bg-color-dark, #0d1117);
  color: var(--warning-color, #f85149);
}

.dark-theme .markdown-content :deep(blockquote) {
  background: var(--bg-color-dark, #0d1117);
  border-left-color: var(--border-color-dark, #30363d);
  color: var(--text-color-secondary-dark, #8b949e);
}

.dark-theme .markdown-content :deep(th) {
  background: var(--bg-color-dark, #0d1117);
}

/* 代码语法高亮（基础样式） */
.markdown-content :deep(.language-javascript) .token.keyword {
  color: var(--syntax-keyword, #d73a49);
}

.markdown-content :deep(.language-javascript) .token.string {
  color: var(--syntax-string, #032f62);
}

.markdown-content :deep(.language-javascript) .token.comment {
  color: var(--syntax-comment, #6a737d);
  font-style: italic;
}

.markdown-content :deep(.language-python) .token.keyword {
  color: var(--syntax-keyword, #d73a49);
}

.markdown-content :deep(.language-python) .token.string {
  color: var(--syntax-string, #032f62);
}

/* 响应式设计 */
@media (max-width: 767px) {
  .markdown-content :deep(pre) {
    padding: 12px;
    font-size: 14px;
  }
  
  .markdown-content :deep(h1) {
    font-size: 1.6em;
  }
  
  .markdown-content :deep(h2) {
    font-size: 1.4em;
  }
  
  .markdown-content :deep(h3) {
    font-size: 1.2em;
  }
}
</style>

