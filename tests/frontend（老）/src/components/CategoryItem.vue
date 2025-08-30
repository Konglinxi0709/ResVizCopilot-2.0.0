<template>
  <custom-sub-menu
    :is-active="isActive"
    :show-children-button="false"
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
        :content="$t('categoryItem.download')" 
        placement="top"
      >
        <el-icon class="action-icon" @click.stop="downloadCategory(nodeId)">
          <Download />
        </el-icon>
      </el-tooltip>

      <el-tooltip :content="$t('categoryItem.copyId')" placement="top">
        <el-icon 
          class="action-icon" 
          :class="{ 'is-disabled': isDisabled }"
          @click.stop="handleCopyClick"
        >
          <DocumentCopy />
        </el-icon>
      </el-tooltip>

      <el-tooltip :content="$t('categoryItem.rename')" placement="top">
        <el-icon class="action-icon" @click.stop="renameCategory(nodeId)">
          <Edit />
        </el-icon>
      </el-tooltip>

      <el-tooltip :content="$t('categoryItem.delete')" placement="top">
        <el-icon class="action-icon delete-icon" @click.stop="deleteCategory(nodeId)">
          <Delete />
        </el-icon>
      </el-tooltip>
    </template>

    <template #expand-content>
      <TargetList 
        :target-list="targetList"
        @submit-target-list="submitTargetList"
      />
      
      <!-- 检索表达式编辑区域 -->
      <div class="search-expression-container">
        <div class="section-header">
          <h4>{{ $t('categoryItem.searchExpression') }}</h4>
          <div v-if="!isEditingExpression" class="action-buttons">
            <el-button type="primary" size="small" @click="startEditExpression">
              <el-icon><Edit /></el-icon>
            </el-button>
          </div>
          <div v-else class="action-buttons">
            <el-button type="success" size="small" @click="saveExpression">
              {{ $t('categoryItem.save') }}
            </el-button>
            <el-button size="small" @click="cancelEditExpression">
              {{ $t('categoryItem.cancel') }}
            </el-button>
          </div>
        </div>
        
        <div v-if="!isEditingExpression" class="expression-display">
          <pre>{{ node.search_expression || $t('categoryItem.noExpression') }}</pre>
        </div>
        <el-input
          v-else
          v-model="editingExpression"
          type="textarea"
          :rows="4"
          :placeholder="$t('categoryItem.expressionPlaceholder')"
        ></el-input>
        
        <!-- AI修改功能 -->
        <div class="ai-modification-section">
          <div class="ai-button-container">
            <el-tooltip :content="$t('categoryItem.aiModify')" placement="top">
              <el-button 
                type="primary" 
                size="small"
                :disabled="isUpdatingExpression"
                @click="showAiUpdateInput = !showAiUpdateInput"
                class="ai-button"
              >
                <el-icon><MagicStick /></el-icon>
              </el-button>
            </el-tooltip>
            
            <el-input
              v-if="showAiUpdateInput"
              v-model="aiUpdateRequirement"
              :placeholder="aiUpdatePlaceholder"
              :disabled="isUpdatingExpression"
              class="ai-input"
            >
              <template #append>
                <el-button @click="requestAiUpdate" :disabled="isUpdatingExpression">
                  {{ $t('categoryItem.modify') }}
                </el-button>
              </template>
            </el-input>
          </div>
        </div>
        
        <!-- 设计理由区域 -->
        <div v-if="node.design_reason" class="design-reason-section">
          <h4>{{ $t('categoryItem.designReason') }}</h4>
          <MarkdownRenderer :content="node.design_reason" />
        </div>
      </div>
      
      <!-- 元数据区域 -->
      <div class="metadata-section">
        <h4>{{ $t('categoryItem.metadata') }}</h4>
        <MarkdownRenderer :content="metadataContent" />
      </div>
    </template>
  </custom-sub-menu>
</template>

<script>
import { Document, Download, DocumentCopy, Edit, Delete, MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import CustomSubMenu from '@/components/CustomSubMenu.vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import TargetList from '@/components/TargetList.vue'
import axios from 'axios'

export default {
  name: 'CategoryItem',
  components: { 
    CustomSubMenu, 
    Document, 
    Download, 
    DocumentCopy, 
    Edit, 
    Delete, 
    MagicStick,
    MarkdownRenderer, 
    TargetList 
  },
  inject: ['getNode', 'selectCategory', 'downloadCategory', 'renameCategory', 'deleteCategory', 'setCategoryTargetList', 'fetchNode', 'handleResult'],
  props: {
    nodeId: {
      type: Number,
      required: true
    },
    activeIndex: Number
  },
  data() {
    return {
      isEditingExpression: false,
      editingExpression: '',
      showAiUpdateInput: false,
      aiUpdateRequirement: '',
      aiUpdatePlaceholder: this.$t('categoryItem.modifyPlaceholder'),
      isUpdatingExpression: false,
      pendingDesignReason: ''
    }
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
    progressPercentage() {
      return Math.floor((this.node.downloading || 0) * 100)
    },
    progressStatus() {
      return this.node.downloading === 1 ? 'success' : undefined
    },
    metadataContent() {
      return `- ${this.$t('categoryItem.nodeId')}: ${ this.node.id }
- ${this.$t('categoryItem.documentCnt')}: ${ this.node.count }
${this.hasDownloading ? `- ${this.$t('categoryItem.downloadProgress')}: ${this.progressPercentage}%` : ''}
${this.node.filter_expression ? `- ${this.$t('categoryItem.filteringExpression')}: ${this.node.filter_expression}` : ''}`
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
            ElMessage.success(this.$t('categoryItem.messages.copySuccess'));
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
              throw new Error(this.$t('categoryItem.messages.copyFailed'));
            }
            ElMessage.success(this.$t('categoryItem.messages.copySuccessUnsecure'));
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
    },
    // 开始编辑检索表达式
    startEditExpression() {
      this.editingExpression = this.node.search_expression || '';
      this.isEditingExpression = true;
    },
    // 取消编辑
    cancelEditExpression() {
      this.isEditingExpression = false;
      this.editingExpression = '';
      if (this.pendingDesignReason) {
        this.node.design_reason = this.pendingDesignReason;
        this.pendingDesignReason = '';
      }
    },
    // 保存检索表达式
    async saveExpression() {
      if (!this.editingExpression.trim()) {
        ElMessage.warning(this.$t('categoryItem.messages.emptyExpression'));
        return;
      }
      
      try {
        const res = await axios.post(`/api/categories/${this.node.id}/update_search_expression`, {
          search_expression: this.editingExpression,
          design_reason: this.node.design_reason || ''
        });
        
        // 重置临时设计理由
        this.pendingDesignReason = '';
        
        // 更新节点数据
        await this.handleResult(res.data);
        
        // 切换回显示模式
        this.isEditingExpression = false;
        
        ElMessage.success(this.$t('categoryItem.messages.expressionUpdateSuccess'));
      } catch (error) {
        ElMessage.error(`${this.$t('categoryItem.messages.expressionUpdateSuccess')}: ${error.response?.data?.detail || error.message}`);
      }
    },
    // 请求AI修改检索表达式
    async requestAiUpdate() {
      if (!this.aiUpdateRequirement.trim() && !this.isUpdatingExpression) {
        ElMessage.warning(this.$t('categoryItem.messages.expressionUpdateSuccess'));
        return;
      }
      const input = this.aiUpdateRequirement
      this.aiUpdateRequirement = ''
      this.isUpdatingExpression = true;
      this.aiUpdatePlaceholder = this.$t('categoryItem.modifying');
      
      try {
        const res = await axios.post(`/api/categories/${this.node.id}/ai_update_search_expression`, {
          requirement: input
        });
        
        if (res.data.success) {
          // 将AI修改的结果填入编辑框
          this.editingExpression = res.data.search_expression;
          // 暂存之前的设计理由，如果用户取消则还原
          this.pendingDesignReason = this.node.design_reason
          this.node.design_reason = res.data.design_reason;
          
          // 自动进入编辑模式
          this.isEditingExpression = true;
          
          ElMessage.success(this.$t('categoryItem.messages.modifySuccess'));
        } else {
          ElMessage.error(res.data.error || this.$t('categoryItem.messages.modifyFailed'));
        }
      } catch (error) {
        ElMessage.error(`${this.$t('categoryItem.messages.modifyFailed')}: ${error.response?.data?.detail || error.message}`);
      } finally {
        this.isUpdatingExpression = false;
        this.aiUpdatePlaceholder = this.$t('categoryItem.modifyPlaceholder');
        this.showAiUpdateInput = false;
      }
    }
  },
  watch: {
    activeIndex: {
      handler(newVal) {
        console.log('当前激活的范畴ID:', newVal)
      }
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

.search-expression-container {
  margin-top: 16px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 12px;
  background-color: #f9f9f9;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.section-header h4 {
  margin: 0;
  font-size: 15px;
  color: #606266;
}

.expression-display {
  background-color: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 8px;
  margin-bottom: 12px;
}

.expression-display pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.ai-modification-section {
  margin-top: 12px;
}

.ai-button-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-input {
  flex-grow: 1;
}

.ai-button {
  background-color: #8e44ad;
  border-color: #8e44ad;
}

.ai-button:hover {
  background-color: #9b59b6;
  border-color: #9b59b6;
}

.design-reason-section {
  margin-top: 16px;
  padding: 8px;
  background-color: #fff;
  border-radius: 4px;
}

.design-reason-section h4 {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

.metadata-section {
  margin-top: 16px;
}

.metadata-section h4 {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}
</style>