<template>
  <div class="category-list">
    <!-- 固定区域 - 只有在选中问题时显示 -->
    <div v-if="currentProblemId" class="fixed-header">
      <!-- 问题详情信息 -->
      <div class="problem-info">
        <div class="problem-header">
          <h3>{{ $t('categoryList.currentProblem', { name: currentProblemViewName }) }}</h3>
        </div>
      </div>

      <!-- 范畴创建区域 -->
    <div class="global-actions">
      <el-input
          v-model="retrievalRequirement"
          :placeholder="placeholderText"
        clearable
          :disabled="isCreatingCategory"
        @keyup.enter="handleAddCategory"
      />
      <el-button
        type="primary"
          :disabled="!currentProblemId || isCreatingCategory"
        @click="handleAddCategory"
          :loading="isCreatingCategory"
      >
        <el-icon><Plus /></el-icon>{{ $t('categoryList.createCategory') }}
      </el-button>
    </div>
    </div>

    <!-- 可滚动区域 -->
    <div class="scrollable-content">
      <el-empty v-if="!currentProblemId" :description="$t('categoryList.selectProblem')"></el-empty>
      
      <div v-else-if="Object.keys(nodes).length === 0" class="empty-message">
        {{ $t('categoryList.noCategories') }}
      </div>

    <category-item
        v-else
      v-for="id in Object.keys(nodes)"
      :key="id"
        :node-id="String(id)"
        :active-index="String(localActiveCategory?.id)"
    />
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { Plus } from '@element-plus/icons-vue'
import CategoryItem from '@/components/CategoryItem.vue'
import { ElMessage } from 'element-plus'
import { longTaskRequest } from '@/scripts/longTask'

export default {
  components: { CategoryItem, Plus },
  provide() {
    return {
      getNode: this.getNode,
      selectCategory: this.selectCategory,
      downloadCategory: this.downloadCategory,
      renameCategory: this.renameCategory,
      deleteCategory: this.deleteCategory,
      setCategoryTargetList: this.setCategoryTargetList,
      fetchNode: this.fetchNode,
      handleResult: this.handleResult
    }
  },
  props: {
    currentProblemId: {
      type: String,
      default: null
    }
  },
  computed: {
    placeholderText() {
      return this.isCreatingCategory 
        ? this.$t('categoryList.creating')
        : this.$t('categoryList.placeholder')
    }
  },
  data() {
    return {
      localActiveCategory: null, // 本地维护的 activeCategory
      nodes: {},
      retrievalRequirement: '',
      isCreatingCategory: false, // 添加创建范畴的状态标志
      currentProblemViewName: '',
    }
  },
  watch: {
    //currentProblemId: {
    //  immediate: true,
    //  handler(newId) {
    //    if (newId) {
    //      this.fetchProblemInfo(newId);
    //      this.fetchCategoriesByProblem(newId);
    //    } else {
    //      this.nodes = {};
    //      this.localActiveCategory = null;
    //      this.updateActiveCategory(null);
    //    }
    //  }
    //}
  },
  methods: {
    updateActiveCategory(inform) {
      this.localActiveCategory = inform;
      this.$emit("update-active-category", inform); // 触发自定义事件
    },
    async handleResult(result) {
      // 1. 处理 update_nodes（覆盖替换）
      if (Array.isArray(result?.update_nodes)) {
        this.nodes = result.update_nodes.reduce((acc, node) => 
          ({ ...acc, [node.id]: node }), {}
        )
      }

      // 3. 处理 add_nodes（合并新增）
      if (Array.isArray(result?.add_nodes)) {
        this.nodes = { 
          ...this.nodes,
          ...result.add_nodes.reduce((acc, node) => 
            ({ ...acc, [node.id]: node }), {}
          )
        }
      }

      // 4. 处理 del_ids（删除操作）
      if (result?.del_ids?.length > 0) {
        result.del_ids.forEach(id => {
          if (id in this.nodes) delete this.nodes[id]
        })
      }
    },
    
    // 强制刷新问题数据，即使问题ID相同
    async refreshProblemData(problemId) {
      if (problemId) {
        // 强制刷新问题信息
        await this.fetchProblemInfo(problemId);
        // 重新加载问题关联的范畴
        await this.fetchCategoriesByProblem(problemId);
      } else {
        // 清空数据
        this.nodes = {};
        this.localActiveCategory = null;
        this.updateActiveCategory(null);
        this.currentProblemViewName = ''
      }
    },
    async fetchCategoriesByProblem(problemId) {
      if (!problemId) return;
      
      try {
        const res = await axios.get(`/api/categories/by-problem/${problemId}`)
        // 清空当前范畴列表，加载新问题的范畴
        this.nodes = {};
        this.localActiveCategory = null;
        this.updateActiveCategory(null);
        
        await this.handleResult(res.data)
      } catch (error) {
        console.error(`获取问题范畴失败: ${error.response?.data?.detail || error.message}`)
      }
    },
    async fetchProblemInfo(problemId) {
      if (!problemId) return;
      
      try {
        const res = await axios.get(`/api/research/problem/${problemId}`)
        if (res.data && res.data.success) {
          const problem = res.data.problem;
          this.currentProblemViewName = problem.viewName || '';
        }
      } catch (error) {
        console.error(`获取问题信息失败: ${error.response?.data?.detail || error.message}`)
      }
    },
    async fetchNode(id) {
      try {
        const res = await axios.get(`/api/categories/${id}`)
        await this.handleResult(res.data)
      } catch (error) {
        console.error(`获取节点失败: ${error.response?.data?.detail || error.message}`)
      }
    },

    getNode(id) {
      return this.nodes[id]
    },

    setLocking(id, flag) {
      this.nodes[id].locking = flag
      if (this.localActiveCategory?.id == id) {
        this.localActiveCategory.locking = flag
        const inform = {
          'id': id,
          'locking': flag
        }
        this.updateActiveCategory(inform)
      }
    },

    async handleAddCategory() {
      if (!this.currentProblemId) return
      this.isCreatingCategory = true // 设置创建中状态
      const userRequirement = this.retrievalRequirement.trim()
      this.retrievalRequirement = ""
      
      try {
        // 使用新的API接口创建范畴
        const response = await axios.post('/api/categories/ai_create_category', {
          requirement: userRequirement
        }, {
          params: {
            problem_id: this.currentProblemId
          }
        });
        
        if (response.data.success) {
          // 刷新范畴列表
          await this.fetchCategoriesByProblem(this.currentProblemId);
          this.$message.success(this.$t('categoryList.messages.createSuccess'));
        } else {
          this.$message.error(response.data.error || this.$t('categoryList.messages.createFailed'));
        }
      } catch (error) {
        this.$message.error(this.$t('categoryList.messages.createError', { error: error.response?.data?.detail || error.message }));
      } finally {
        this.isCreatingCategory = false; // 重置创建状态
      }
    },

    selectCategory(id) {
      const inform = {
        'id': id,
        'locking': this.getNode(id).locking
      }
      this.updateActiveCategory(this.localActiveCategory?.id === id ? null : inform)
    },

    async downloadCategory(id) {
      try {
        this.nodes[id].downloading = 0.0
        const promise = longTaskRequest({
          method: 'post',
          url: `/api/categories/${id}/download`
        }).progress(progress => {
          this.nodes[id].downloading = progress
        })
        await promise
      } catch (error) {
        ElMessage.error(`下载失败: ${error.message}`)
        this.nodes[id].downloading = -1.0
      }
    },
    
    async renameCategory(id) {
      let new_name = '';
      try {
        const { value: newName } = await this.$prompt('请输入新名称', {
          inputValue: this.nodes[id].name,
          inputValidator: (value) => {
            if (!value.trim()) return '名称不能为空';
            const isNameExists = Object.values(this.nodes).some(
              (s) => s.id !== id && s.name === value
            );
            if (isNameExists) return '名称已存在';
            return true;
          }
        })
        new_name = newName;
      } catch (error) {
        void 0;
      }
      try {  
        if (new_name) {
          const res = await axios.post(`/api/categories/${id}/rename`, { new_name: new_name });
          await this.handleResult(res.data);
          ElMessage.success('重命名成功');
        }
      } catch (error) {
          ElMessage.error(`重命名失败: ${error.response?.data?.detail || error.message}`);
      }
    },

    async deleteCategory(id){
      const node = await this.getNode(id)
      if (confirm(`确定删除【${node.name}】节点吗？`)) {
        try {
          const res = await axios.delete(`/api/categories/${id}/delete`)
          await this.handleResult(res.data)
          ElMessage.success('删除成功')
        } catch (error) {
          ElMessage.error(`删除失败: ${error.response?.data?.detail || error.message}`)
        }
      }
    },
    
    async setCategoryTargetList(id, targetList){
      try {
        const res = await axios.post(`/api/categories/${id}/set_target`, targetList)
        await this.handleResult(res.data)
        const currentNode = this.getNode(id)
        if (currentNode.downloading === 1){
        ElMessage.info('正在更新数据')
        this.setLocking(id, true)
        await longTaskRequest({
          method: 'post',
          url: `/api/categories/${id}/update_similarity`
        })
        this.setLocking(id, false)
          console.log('当前选中范畴:', this.localActiveCategory)
        }
        ElMessage.success('修改成功')
      } catch (error) {
        this.setLocking(id, false)
        ElMessage.error(`修改失败: ${error.response?.data?.detail || error.message}`)
      }
    },
  }
}
</script>

<style scoped>
.category-list {
  background: var(--el-bg-color);
  padding: 8px;
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
}

.fixed-header {
  flex-shrink: 0;
}

.scrollable-content {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.global-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.problem-info {
  background: #f0f9ff;
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 12px;
  border-left: 3px solid #409EFF;
  transition: all 0.3s;
}


.problem-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.problem-header h3 {
  margin: 0;
  color: #409EFF;
}

.empty-message {
  text-align: center;
  color: #909399;
  padding: 20px;
  font-size: 14px;
}
</style>