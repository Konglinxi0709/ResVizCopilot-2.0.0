<template>
  <div class="markdown-renderer" :class="{ 'dark-theme': isDarkTheme }">
    <div v-html="renderedContent" class="markdown-content"></div>
  </div>
</template>

<script>
import { defineComponent, computed, watch, ref } from 'vue'
import { useUIStore } from '@/stores/uiStore'

export default defineComponent({
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
    
    // 是否启用数学公式渲染
    enableMath: {
      type: Boolean,
      default: true
    }
  },
  
  setup(props) {
    const uiStore = useUIStore()
    const renderedContent = ref('')
    
    const isDarkTheme = computed(() => uiStore.isDarkTheme)
    
    // 简单的Markdown渲染函数
    const renderMarkdown = (content) => {
      if (!content) return ''
      
      let html = content
      
      // 代码块处理
      html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre><code class="language-${lang || 'text'}">${escapeHtml(code.trim())}</code></pre>`
      })
      
      // 行内代码
      html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
      
      // 标题
      html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
      html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
      html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')
      
      // 粗体和斜体
      html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
      
      // 链接
      html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
      
      // 列表
      html = html.replace(/^[\s]*[-*+] (.+)$/gm, '<li>$1</li>')
      html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
      
      // 数字列表
      html = html.replace(/^[\s]*\d+\. (.+)$/gm, '<li>$1</li>')
      
      // 引用
      html = html.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
      
      // 分割线
      html = html.replace(/^---$/gm, '<hr>')
      
      // 段落处理
      html = html.split('\n\n').map(paragraph => {
        const trimmed = paragraph.trim()
        if (!trimmed) return ''
        
        // 如果已经是HTML标签，直接返回
        if (trimmed.startsWith('<')) {
          return trimmed
        }
        
        // 否则包装成段落
        return `<p>${trimmed.replace(/\n/g, '<br>')}</p>`
      }).join('\n')
      
      return html
    }
    
    // HTML转义函数
    const escapeHtml = (text) => {
      const div = document.createElement('div')
      div.textContent = text
      return div.innerHTML
    }
    
    // 监听内容变化，重新渲染
    watch(() => props.content, (newContent) => {
      renderedContent.value = renderMarkdown(newContent)
    }, { immediate: true })
    
    return {
      renderedContent,
      isDarkTheme
    }
  }
})
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

