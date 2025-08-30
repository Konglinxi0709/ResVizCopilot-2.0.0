<template>
  <div class="markdown-content" v-html="compiledMarkdown"></div>
</template>

<script>
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import DOMPurify from 'dompurify'

export default {
  props: {
    content: {
      type: String,
      required: true
    }
  },
  computed: {
    compiledMarkdown() {
      // 配置 markdown-it
      const md = new MarkdownIt({
        html: true,         // 允许 HTML 标签
        linkify: true,      // 自动转换 URL 为链接
        typographer: true,  // 优化排版
        highlight: (str, lang) => {
          // 如果语言未指定或无法识别，使用默认语言 'plaintext'
          if (!lang || !hljs.getLanguage(lang)) {
            lang = 'plaintext'; // 使用默认语言
          }

          try {
            return `<pre class="hljs"><code>${
              hljs.highlight(str, { 
                language: lang, 
                ignoreIllegals: true 
              }).value
            }</code></pre>`;
          } catch (__) {
            // 如果高亮失败，返回普通代码块
            return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`;
          }
        }
      });

      // 渲染并净化内容
      const rawHtml = md.render(this.content)
      return DOMPurify.sanitize(rawHtml)
    }
  },
  watch: {
    compiledMarkdown() {
      // 确保在下一次 DOM 更新后高亮代码
      this.$nextTick(() => {
        document.querySelectorAll('pre code').forEach((block) => {
          hljs.highlightElement(block)
        })
      })
    }
  }
}
</script>

<style>
/* 引入代码高亮主题 */
@import 'highlight.js/styles/github-dark.css';

.markdown-content {
  line-height: 1.6;
}

/* 调整段落与后续列表的间距 */
.markdown-content p + ul,
.markdown-content p + ol {
  margin-top: 0.5em !important; /* 减少顶部边距 */
}

/* 调整列表的默认边距 */
.markdown-content ul,
.markdown-content ol {
  margin: 0.5em 0 !important; /* 统一上下边距为较小的值 */
  padding-left: 2em !important; /* 调整缩进以符合常规排版 */
}

/* 嵌套列表的调整（子列表减少顶部边距） */
.markdown-content ul ul,
.markdown-content ol ol,
.markdown-content ul ol,
.markdown-content ol ul {
  margin-top: 0.25em !important;
  margin-bottom: 0.25em !important;
}

/* 代码块样式保持不变 */
.markdown-content pre {
  padding: 1em;
  border-radius: 4px;
  white-space: pre-wrap; /* 允许代码换行 */
  word-wrap: break-word; /* 长单词或URL强制换行 */
  overflow-x: auto;      /* 保留横向滚动条作为备用 */
}

.markdown-content code {
  font-family: 'Fira Code', monospace;
  white-space: pre-wrap !important; /* 覆盖 highlight.js 的 pre 设置 */
  word-break: break-all; /* 更激进的断词策略 */
}

</style>