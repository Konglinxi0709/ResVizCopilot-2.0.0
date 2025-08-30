<template>
  <div class="selection-list">
    <ListItem
      v-for="selection in orderedSelections"
      :key="selection.id"
      :disabled="false"
      :is-active="false"
    >
      <template #title>
        <span class="selection-title">{{ selection.name }}</span>
      </template>
      
      <template #actions>
        <el-tooltip content="复制标识符" placement="top">
          <el-button
            size="small"
            circle
            @click.stop="$emit('copy', selection)"
            icon="DocumentCopy"
          />
        </el-tooltip>
        <el-tooltip content="重命名" placement="top">
          <el-button
            size="small"
            circle
            @click.stop="$emit('rename', selection)"
            icon="Edit"
          />
        </el-tooltip>
        <el-tooltip content="删除" placement="top">
          <el-button
            size="small"
            circle
            @click.stop="$emit('delete', selection)"
            icon="Delete"
            type="danger"
            plain
          />
        </el-tooltip>
      </template>

      <template #expand-content>
        <el-table
          :data="selection.data"
          height="100vh"
          style="width: 100%"
          empty-text="暂无数据"
        >
          <el-table-column
            v-for="col in generatedColumns(selection.data)"
            :key="col.prop"
            :prop="col.prop"
            :label="col.label"
            :width="col.width"
          />
        </el-table>
      </template>
    </ListItem>
  </div>
</template>

<script>
import ListItem from '@/components/ListItem.vue';

export default {
  components: { ListItem },
  props: {
    orderedSelections: {
      type: Array,
      required: true
    }
  },
  methods: {
    generatedColumns(data) {
      if (!data?.length) return [];
        
      const columns = [];
      const sampleItem = data[0];
        
      Object.keys(sampleItem)
        .filter(key => key !== 'id')
        .forEach(key => {
          const maxLength = this.calculateMaxLength(data, key);
          const width = this.calculateColumnWidth(maxLength);
          columns.push({ prop: key, label: key, width });
        });

      return columns;
    },
    
    calculateMaxLength(data, key) {
      return data.reduce((max, item) => {
        const length = String(item[key] ?? '').length;
        return length > max ? length : max;
      }, 0);
    },
    
    calculateColumnWidth(maxLength) {
      const BASE_WIDTH = 10;
      const MIN_WIDTH = 80;
      const MAX_WIDTH = 440;
      const calculated = maxLength * BASE_WIDTH + 20; // 添加 padding
      return Math.min(Math.max(calculated, MIN_WIDTH), MAX_WIDTH);
    }
  }
};
</script>

<style scoped>
.selection-list {
  margin-top: 20px;
  border-top: 1px solid #ebeef5;
  padding-top: 15px;
}

.selection-title {
  font-weight: 500;
  margin-left: 8px;
}
</style>