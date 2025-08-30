<template>
  <custom-sub-menu
    :is-active="isActive"
    :show-children-button="shouldRenderChildren"
  >
    <template #title>
      <div 
        class="category-title"
        :class="{ 'is-disabled': isDisabled }"
        @click.stop="handleHeaderClick"
      >
        <el-icon v-if="hasDownloading" class="document-icon">
          <Document />
        </el-icon>
        <span class="label-text">{{ node.name }}</span>
      </div>
    </template>

    <template #actions>
      <el-progress
        v-if="showProgressBar"
        :percentage="progressPercentage"
        :status="progressStatus"
        :show-text="false"
        stroke-width="2"
        class="progress-bar"
      />
      <el-tooltip 
        v-if="showDownloadButton"
        content="下载数据" 
        placement="top"
      >
        <el-icon class="action-icon" @click.stop="downloadCategory(nodeId)">
          <Download />
        </el-icon>
      </el-tooltip>

      <el-tooltip content="复制标识符" placement="top">
        <el-icon 
          class="action-icon" 
          :class="{ 'is-disabled': isDisabled }"
          @click.stop="handleCopyClick"
        >
          <DocumentCopy />
        </el-icon>
      </el-tooltip>

      <el-tooltip content="重命名" placement="top">
        <el-icon class="action-icon" @click.stop="renameCategory(nodeId)">
          <Edit />
        </el-icon>
      </el-tooltip>

      <el-tooltip v-if="showPromoteButton" content="上浮" placement="top">
        <el-icon class="action-icon" @click.stop="promoteCategory(nodeId)">
          <Promotion />
        </el-icon>
      </el-tooltip>

      <el-tooltip content="删除" placement="top">
        <el-icon class="action-icon delete-icon" @click.stop="deleteCategory(nodeId)">
          <Delete />
        </el-icon>
      </el-tooltip>
    </template>

    <template #expand-content>
      <TargetList 
        :target-list = "targetList"
        @submit-target-list = "submitTargetList"
      />
      <MarkdownRenderer :content="expandContent" />
    </template>

    <template #children v-if="shouldRenderChildren">
      <category-item
        v-for="childId in node.children_ids"
        :key="childId"
        :node-id="childId"
        :active-index="activeIndex"
      />
    </template>
  </custom-sub-menu>
</template>

<script>
import { Document, Download, DocumentCopy, Edit, Promotion, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import CustomSubMenu from '@/components/CustomSubMenu.vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import TargetList from '@/components/TargetList.vue'

export default {
  name: 'CategoryItem',
  components: { CustomSubMenu, Document, Download, DocumentCopy, Edit, Promotion, Delete, MarkdownRenderer, TargetList },
  inject: ['getNode', 'selectCategory', 'downloadCategory', 'renameCategory', 'promoteCategory', 'deleteCategory', 'setCategoryTargetList', 'fetchNode'],
  props: {
    nodeId: {
      type: Number,
      required: true
    },
    activeIndex: Number
  },
  computed: {
    node() {
      return this.getNode(this.nodeId) || {}
    },
    hasDownloading() {
      return 'downloading' in this.node && this.node.downloading !== null
    },
    isDisabled() {
      return this.hasDownloading && this.node.downloading < 1
    },
    isActive() {
      return this.activeIndex === this.nodeId
    },
    showDownloadButton() {
      return this.hasDownloading && this.node.downloading < 0
    },
    showProgressBar() {
      return this.hasDownloading && this.node.downloading >= 0
    },
    showPromoteButton() {
      return this.node.parent_id !== null
    },
    progressPercentage() {
      return Math.floor((this.node.downloading || 0) * 100)
    },
    progressStatus() {
      return this.node.downloading === 1 ? 'success' : undefined
    },
    shouldRenderChildren() {
      return this.node.children_ids?.length > 0 && !this.isDisabled
    },
    expandContent() {
      const filter_expression = (this.node.filter_expression && this.node.filter_expression.trim() !== '') ? `
**过滤表达式**: 
\`\`\`
${this.node.filter_expression}
\`\`\`` : ''
      const search_expression = (this.node.search_expression && this.node.search_expression.trim() !== '') ? `
**检索表达式**: 
\`\`\`
${this.node.search_expression}
\`\`\`` : ''

      return `**范畴元数据**: 
- 节点ID：${ this.node.id }
- 父节点ID：${ this.node.parent_id ?? '无' }
- 文章总数: ${ this.node.count }
${this.hasDownloading ? `- 下载进度：${this.progressPercentage}%` : ''}

${filter_expression}

${search_expression}
      `
    },
    downloading() {
      return this.node?.downloading
    },
    targetList() {
      return this.node?.target_list
    }
  },
  methods: {
    handleHeaderClick() {
      if (!this.isDisabled) {
        this.selectCategory(this.nodeId)
      }
    },
    async handleCopyClick() {
      if (!this.isDisabled) {
        const textToCopy = `#${this.node.id}_${this.node.name}`;

        try {
          // 方案 1: 优先尝试现代 Clipboard API
          if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(textToCopy);
            ElMessage.success('标识符已复制');
          } 
          // 方案 2: 非安全上下文下的回退方案
          else {
            const textArea = document.createElement('textarea');
            textArea.value = textToCopy;
            textArea.style.position = 'fixed'; // 避免滚动到文本框
            document.body.appendChild(textArea);
            textArea.select();
            const success = document.execCommand('copy');
            document.body.removeChild(textArea);
            if (!success) {
              throw new Error('复制失败，请手动复制');
            }
            ElMessage.success('标识符已复制(当前服务器未认证)');
          }
        } catch (err) {
          // 统一错误处理
          const errorMessage = window.isSecureContext 
            ? `复制失败: ${err.message}`
            : '请在 HTTPS 环境或 localhost 中使用复制功能';
          ElMessage.error(errorMessage);
          // 降级方案：自动选中文本供手动复制
          const tempInput = document.createElement('input');
          tempInput.value = textToCopy;
          document.body.appendChild(tempInput);
          tempInput.select();
          setTimeout(() => document.body.removeChild(tempInput), 2000);
        }
      }
    },
    submitTargetList(payload){
      this.setCategoryTargetList(this.node.id, payload)
    }
  },
}
</script>

<style scoped>

.delete-icon:hover {
  color: var(--el-color-danger);
}

.progress-bar {
  width: 60px;
  margin-right: 8px;
}

.document-icon {
  margin-right: 4px;
}

</style>