<template>
  <div class="paper-list-container">
    <!-- 标题栏 -->
    <div class="header">
      <span class="title">{{ $t('paperList.title') }}</span>
      <div class="header-actions">
        <el-switch
          v-model="showInvalidPapers"
          :active-action-icon="View"
          :inactive-action-icon="Hide"
          :active-text="$t('paperList.showInvalid')"
          :inactive-text="$t('paperList.hideInvalid')"
          style="margin-right: 15px;"
        />
        <el-icon 
          class="action-icon"
          @click.stop="toggleList"
        >
          <ArrowDown v-if="showList"/>
          <ArrowUp v-else/>
        </el-icon>
      </div>
    </div>

    <el-collapse-transition>
      <div 
        v-show="showList" 
        class="table-wrapper"
      >
        <el-table
          :data="filteredTableData"
          :height="tableHeight"
          style="width: 100%"
        >
          <el-table-column :label="$t('paperList.columns.order')" width="50">
            <template #default="{ $index }">
              {{ $index + 1 }}
            </template>
          </el-table-column>
          <el-table-column :label="$t('paperList.columns.literature')" min-width="250">
            <template #default="{ row }">
              <div class="literature-info">
                <div class="title-link">
                  <a 
                    :href="row.link" 
                    target="_blank" 
                    class="literature-title"
                    v-if="row.link"
                  >
                    {{ row.title }}
                  </a>
                  <span v-else>{{ row.title }}</span>
                </div>
                <div class="authors">{{ row.authors }}</div>
                <div class="date">{{ row.date }}</div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="abstract" :label="$t('paperList.columns.abstract')" min-width="600" />
          <el-table-column :label="$t('paperList.columns.aiAnalysis')" min-width="400">
            <template #default="{ row }">
              <div v-if="row.evaluate_state === 0 || row.evaluate_state === 2" class="analyzing">
                <el-icon class="loading-icon"><Loading /></el-icon>
                <span>{{ $t('paperList.analyzing') }}</span>
              </div>
              <div v-else-if="row.evaluate_state === 1" class="value-description">
                {{ row.evaluate_reason || $t('paperList.noAnalysis') }}
              </div>
            </template>
          </el-table-column>
          <el-table-column :label="$t('paperList.columns.aiUsability')" width="100">
            <template #default="{ row }">
              <div v-if="row.evaluate_state === 0 || row.evaluate_state === 2" class="analyzing">
                <el-icon class="loading-icon"><Loading /></el-icon>
                <span>{{ $t('paperList.analyzing') }}</span>
              </div>
              <div v-else-if="row.evaluate_state === 1">
                <el-icon :class="row.evaluate_result ? 'success-icon' : 'error-icon'">
                  <Check v-if="row.evaluate_result" />
                  <Close v-else />
                </el-icon>
              </div>
            </template>
          </el-table-column>
          <el-table-column :label="$t('paperList.columns.similarity')" width="100">
            <template #default="{ row }">
              {{ (row.matching_score * 100).toFixed(1) }}%
            </template>
          </el-table-column>
          <el-table-column prop="publish_location" :label="$t('paperList.columns.publication')" width="100" />
          <el-table-column :label="$t('paperList.columns.citations')" width="100">
            <template #default="{ row }">
              {{row.cited_num || '-'}} / {{ (row.citation_normalized_percentile * 100).toFixed(1) || '-' }}%
            </template>
          </el-table-column>
          <el-table-column :label="$t('paperList.columns.number')" width="50">
            <template #default="{ row }">
              {{ getOriginalIndex(row) + 1 }}
            </template>
          </el-table-column>
        </el-table>

        <!-- 加载更多按钮 -->
        <div class="load-more">
          <el-button 
            v-if="hasMore && !loading"
            type="text"
            @click="load"
          >
            {{ $t('paperList.loadMore') }}
          </el-button>
          <el-button 
            v-else-if="loading"
            type="text"
            disabled
          >
            {{ $t('paperList.loading') }}
          </el-button>
          <p v-if="noMore" class="no-more-text">{{ $t('paperList.noMore') }}</p>
        </div>
      </div>
    </el-collapse-transition>
  </div>
</template>

<script>
import { ArrowUp, ArrowDown, Check, Close, Loading } from '@element-plus/icons-vue'
import axios from 'axios'

export default {
  name: 'PaperList',
  components: {
    ArrowUp,
    ArrowDown,
    Check,
    Close,
    Loading,
  },
  data() {
    return {
      showList: true,
      tableData: [],
      count: 0,
      loading: false,
      hasMore: true,
      tableHeight: 'calc(73vh)', // 为按钮留出空间
      showInvalidPapers: true, // 是否显示不可用文章
      pollingTimer: null, // 轮询定时器
      isEvaluating: false, // 是否正在评估
    };
  },
  props: {
    activeCategory: {
      type: Object,
      required: true
    },
  },
  watch: {
    activeCategory: {
      immediate: true,
      handler(newValue) {
        this.tableData = []
        this.count = 0
        this.hasMore = true
        this.clearPolling() // 切换分类时清除轮询
        if (this.showList && newValue) this.load()
      }
    }
  },
  computed: {
    noMore() {
      return !this.hasMore;
    },
    filteredTableData() {
      if (this.showInvalidPapers) {
        return this.tableData;
      } else {
        // 只显示可用性为true的文章或者还在分析中的文章
        return this.tableData.filter(paper => 
          paper.evaluate_state !== 1 || paper.evaluate_result === true
        );
      }
    }
  },
  methods: {
    getOriginalIndex(row) {
      return this.tableData.findIndex(item => item === row);
    },
    toggleList() {
      this.showList = !this.showList;
      if (this.showList && this.tableData.length === 0) {
        this.load()
      }
    },
    async load() {
      const loadNum = 7;
      if (this.loading || !this.hasMore || !this.activeCategory) return;

      this.loading = true;
      try {
        const category_id = this.activeCategory.id
        const res = await axios.get(`/api/categories/${category_id}/fetch_sorted_papers/${this.count}/${this.count+loadNum}`)
        const newData = res.data

        this.tableData = [...this.tableData, ...newData];
        console.log('当前的文章列表:', this.tableData)
        this.count += newData.length;

        // 判断是否还有更多数据
        this.hasMore = newData.length >= loadNum
        
        // 启动AI评估
        this.startEvaluation();
        
        // 开始轮询文章评估状态
        this.startPolling();
        
      } finally {
        this.loading = false;
      }
    },
    startEvaluation() {
      // 如果已经在评估中，不要重复启动
      if (this.isEvaluating || !this.activeCategory) return;
      
      this.isEvaluating = true;
      
      // 收集所有evaluate_state为0的文章索引
      const pendingEvaluationIndexes = this.tableData
        .map((paper, index) => paper.evaluate_state === 0 ? index : null)
        .filter(index => index !== null);
      
      // 如果没有需要评估的文章，就不进行评估
      if (pendingEvaluationIndexes.length === 0) {
        this.isEvaluating = false;
      }
      
      // 获取最后已加载文章的索引
      const lastIndex = this.count - 1;
      // 添加后10篇文章的索引用于预加载
      for (let i = 1; i <= 10; i++) {
        pendingEvaluationIndexes.push(lastIndex + i);
      }
      console.log('需要评估的文章索引:', pendingEvaluationIndexes)
      // 每10篇为一组进行批量评估
      const batchSize = 10;
      const batches = [];
      
      for (let i = 0; i < pendingEvaluationIndexes.length; i += batchSize) {
        batches.push(pendingEvaluationIndexes.slice(i, i + batchSize));
      }
      
      // 逐批调用评估接口
      batches.forEach(async (batch) => {
        try {
          await axios.post(`/api/categories/${this.activeCategory.id}/evaluate_literature`, {
            literature_index_list: batch
          });
          
          // 更新UI标记为评估中(state=2)
          batch.forEach(indexStr => {
            const index = parseInt(indexStr);
            if (index < this.tableData.length) {
              this.tableData[index].evaluate_state = 2;
            }
          });
          
        } catch (error) {
          console.error('评估文献失败:', error);
        }
      });
      
      this.isEvaluating = false;
    },
    startPolling() {
      // 如果已经有定时器在运行，则不需要重新启动
      if (this.pollingTimer) return;
      
      // 每10秒轮询一次
      this.pollingTimer = setInterval(async () => {
        if (!this.activeCategory) {
          this.clearPolling();
          return;
        }
        
        // 收集所有evaluate_state为0或2的文章索引
        const pendingEvaluationIndexes = this.tableData
          .map((paper, index) => (paper.evaluate_state === 0 || paper.evaluate_state === 2) ? index : null)
          .filter(index => index !== null);
        
        // 如果没有待评估的文章，并且没有评估进行中，则停止轮询
        if (pendingEvaluationIndexes.length === 0) {
          this.clearPolling();
          return;
        }
        
        // 轮询评估状态
        if (pendingEvaluationIndexes.length > 0) {
          try {
            const response = await axios.post(`/api/categories/${this.activeCategory.id}/is_literature_evaluated`, {
              literature_index_list: pendingEvaluationIndexes
            });
            
            // 如果有评估完成的文章，更新列表
            if (response.data.is_evaluated) {
              // 重新获取所有已加载的文章
              const category_id = this.activeCategory.id;
              const res = await axios.get(`/api/categories/${category_id}/fetch_sorted_papers/0/${this.count}`);
              // 更新表格数据
              this.tableData = res.data;
            }
          } catch (error) {
            console.error('检查文献评估状态失败:', error);
          }
        }
      }, 10000);
    },
    clearPolling() {
      if (this.pollingTimer) {
        clearInterval(this.pollingTimer);
        this.pollingTimer = null;
      }
    }
  },
  beforeUnmount() {
    // 组件销毁时清除轮询定时器
    this.clearPolling();
  }
};
</script>

<style scoped>
.table-wrapper {
  height: 83vh;
  margin-top: 10px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden; /* 改为hidden */
}

.paper-list-container {
  width: 100%;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.header-actions {
  display: flex;
  align-items: center;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.load-more {
  text-align: center;
  padding: 10px;
  border-top: 1px solid #ebeef5;
}

:deep(.el-table) {
  --el-table-header-bg-color: #f5f7fa;
}

.no-more-text {
  color: #909399;
  font-size: 14px;
  margin: 10px 0;
}

.success-icon {
  color: #67C23A;
  font-size: 24px; /* 放大两倍 */
}

.error-icon {
  color: #F56C6C;
  font-size: 24px; /* 放大两倍 */
}

.loading-icon {
  animation: rotate 1s linear infinite;
}

.analyzing {
  display: flex;
  align-items: center;
  color: #909399;
  font-size: 14px;
}

.analyzing .loading-icon {
  margin-right: 5px;
}

.value-description {
  height: 100%;
  overflow-y: auto;
}

.literature-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.literature-title {
  font-weight: 600;
  color: #409EFF;
  text-decoration: none;
}

.literature-title:hover {
  text-decoration: underline;
}

.authors {
  color: #606266;
  font-size: 14px;
}

.date {
  color: #909399;
  font-size: 12px;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>