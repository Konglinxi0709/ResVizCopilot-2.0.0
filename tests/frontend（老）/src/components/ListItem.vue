<template>
  <div class="list-item">
    <!-- 标题区域 -->
    <div class="list-item__header">
      <div class="header-content">
        <slot name="title"></slot>
      </div>
      
      <!-- 操作按钮容器 -->
      <div class="action-buttons">
        <slot name="actions"></slot>
        
        <!-- 扩展内容展开按钮 -->
        <el-icon 
          v-if="hasExpandContent"
          class="action-icon"
          @click.stop="toggleExpand"
        >
          <ArrowDown v-if="!isExpanded"/>
          <ArrowUp v-else/>
        </el-icon>
      </div>
    </div>

    <!-- 扩展内容区域 -->
    <el-collapse-transition>
      <div 
        v-show="isExpanded"
        class="list-item__expand-content"
      >
        <slot name="expand-content"></slot>
      </div>
    </el-collapse-transition>
  </div>
</template>

<script>
import { ArrowDown, ArrowUp } from '@element-plus/icons-vue'

export default {
  name: 'ListItem',
  components: { ArrowDown, ArrowUp },
  emits: ['header-click'],
  data() {
    return {
      isExpanded: false,
      hasExpandContent: false // 新增变量用于判断是否有扩展内容
    }
  },
  mounted() {
    this.checkExpandContent();
  },
  methods: {
    toggleExpand() {
      this.isExpanded = !this.isExpanded;
    },
    checkExpandContent() {
      // 检查插槽内容是否存在
      this.hasExpandContent = !!this.$slots['expand-content'];
    }
  }
}
</script>

<style scoped>
.list-item {
  width: 100%;
}

.list-item__header {
  display: flex;
  align-items: center;
  height: 60px;
  padding: 0 12px;
  cursor: pointer;
  transition: all 0.3s var(--el-transition-function-ease-in-out-bezier);
  margin: 5px 0;
}

.header-content {
  flex: 1;
  overflow: hidden;
  color: var(--el-text-color-primary);
}

.header-content:hover {
  color: var(--el-color-primary);
}

.action-buttons {
  display: flex;
  gap: 8px;
  margin-left: auto;
  background: inherit;
}

.list-item__expand-content {
  padding: 12px;
  font-size: 0.9em;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
}

</style>