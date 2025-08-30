<template>
  <div class="category-list">
    <div class="global-actions">
      <el-input
        v-model="searchExpression"
        placeholder="输入检索表达式"
        clearable
        @keyup.enter="handleAddCategory"
      />
      <el-button
        type="primary"
        :disabled="!searchExpression.trim()"
        @click="handleAddCategory"
      >
        <el-icon><Plus /></el-icon>新建范畴
      </el-button>
    </div>

    <category-item
      v-for="rootId in rootIds"
      :key="rootId"
      :node-id="rootId"
      :active-index="localActiveCategory?.id"
    />
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
      promoteCategory: this.promoteCategory,
      deleteCategory: this.deleteCategory,
      setCategoryTargetList: this.setCategoryTargetList,
      fetchNode: this.fetchNode,
    }
  },
  data() {
    return {
      localActiveCategory: null, // 本地维护的 activeCategory
      nodes: {},
      rootIds: [],
      searchExpression: ''
    }
  },
  async created() {
    await this.fetchTree()
    //console.log('created', this.nodes, this.rootIds)
  },
  methods: {
    updateActiveCategory(inform) {
      this.localActiveCategory = inform;
      //console.log('localActiveCategory:', this.localActiveCategory)
      this.$emit("update-active-category", inform); // 触发自定义事件
    },
    async handleResult(result) {
      // 1. 处理 update_nodes（覆盖替换）
      if (Array.isArray(result?.update_nodes)) {
        this.nodes = result.update_nodes.reduce((acc, node) => 
          ({ ...acc, [node.id]: node }), {}
        )
      }

      // 2. 处理 root_ids（直接替换）
      if (Array.isArray(result?.root_ids)) {
        this.rootIds = [...result.root_ids] // 新数组保证响应性
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
        const delSet = new Set(result.del_ids)
        this.rootIds = this.rootIds.filter(id => !delSet.has(id))
        result.del_ids.forEach(id => {
          if (id in this.nodes) delete this.nodes[id]
        })
        console.log(`删除nodes:${this.nodes}`)        
      }
    },
    async fetchTree() {
      try {
        const res = await axios.get('/api/categories/fetch_tree')
        await this.handleResult(res.data)
      } catch (error) {
        console.error(`获取范畴树失败: ${error.response?.data?.detail || error.message}`)
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
      if (!this.searchExpression.trim()) return

      try {
        const parentId = this.localActiveCategory?.id
        const res = await axios.post('/api/categories/add', {
          parent_id: parentId,
          search_expression: this.searchExpression.trim()
        })
        await this.handleResult(res.data)
        this.searchExpression = ''
        this.$message.success('添加成功')
      } catch (error) {
        this.$message.error(`添加失败: ${error.response?.data?.detail || error.message}`)
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

    async promoteCategory(id){
      try {
        const res = await axios.post(`/api/categories/${id}/promote`)
        await this.handleResult(res.data)
        ElMessage.success('上浮成功')
      } catch (error) {
        ElMessage.error(`上浮失败: ${error.response?.data?.detail || error.message}`)
      }
    },
    async deleteCategory(id){
      const node = await this.getNode(id)
      if (confirm(`确定删除【${node.name}】及其所有子节点吗？`)) {
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
        ElMessage.info('正在更新数据')
        this.setLocking(id, true)
        await longTaskRequest({
          method: 'post',
          url: `/api/categories/${id}/update_similarity`
        })
        this.setLocking(id, false)
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
.global-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.category-list {
  background: var(--el-bg-color);
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
</style>