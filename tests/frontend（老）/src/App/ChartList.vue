<template>
  <div
    class="global-actions"
    v-if = "this.activeCategory"
  >
    <!--"输入您需要创建的可视化图表描述和要求"-->
    <el-input
      v-model="chartRequirement"
      placeholder="Enter description and requirements for visualization charts to be created"
      clearable
    />
    <el-button
      type="primary"
      :disabled="!chartRequirement.trim()"
      @click.stop="handleAddVisualization"
    >
      <el-icon><DataLine /></el-icon>创建可视化
    </el-button>
  </div>
  <div 
    v-loading="chartLoading"
    element-loading-text="正在加载可视化列表..."
    class="app-container"
  >
    <VisualizationRenderer
      v-for="(config, id) in nodes"
      :key="id"
      :vis-config="config"
    />
  </div>
</template>

<script>
import VisualizationRenderer from '@/components/VisualizationRenderer.vue';
import axios from 'axios';
import { handleResult } from '@/scripts/handleNodeResult'
import { DataLine } from '@element-plus/icons-vue'
export default {
  components: {
    VisualizationRenderer,
    DataLine
  },
  props: {
    activeCategory: {
      type: [Object, null],
      required: true,
    },
  },
  data() {
    return {
      chartLoading: false,
      nodes: {},
      chartRequirement: ''
    };
  },
  methods: {
    async handleAddVisualization() {
      console.log('正在添加可视化：', this.chartRequirement)
      if (!this.chartRequirement.trim()) return
      try {
        const categoryId = this.activeCategory?.id
        const res = await axios.post('/api/visualizations/add', {
          category_id: categoryId,
          question: this.chartRequirement
        })
        this.nodes = await handleResult(this.nodes, res.data)
        this.chartRequirement = ''
        this.$message.success('创建成功')
      } catch (error) {
        this.$message.error(`创建可视化图表失败: ${error.response?.data?.detail || error.message}`)
      }
    },
    async fetchVisualizations() {
      this.chartLoading = true; // 开始加载
      try {
        const res = await axios.get(`/api/categories/${this.activeCategory.id}/fetch_all_visualizations`);
        this.nodes = await handleResult(this.nodes, res.data)
      } catch (error) {
        console.error(`获取范畴图表失败: ${error.response?.data?.detail || error.message}`);
      } finally {
        this.chartLoading = false; // 结束加载
      }
    },
  },
  watch: {
    activeCategory: {
      immediate: true,
      deep: true,
      async handler(newVal) {
        if (newVal !== null) {
          if (newVal.locking) {
            this.chartLoading = true;
          }
          else {
            await this.fetchVisualizations();
          }
        }
        else{
          this.chartLoading = false
          this.nodes = {};
        }
      },
    },
  },
};
</script>

<style scoped>
.app-container {
  overflow-y: auto;
}

.global-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
</style>