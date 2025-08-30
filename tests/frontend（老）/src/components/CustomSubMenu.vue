<template>
  <div 
    class="custom-submenu"
    :class="{ 'is-active': isActive }"
  >
    <ListItem>
      <!-- 标题插槽 -->
      <template #title>
        <slot name="title"></slot>
      </template>

      <!-- 操作按钮插槽 -->
      <template #actions>
        <slot name="actions"></slot>
        
        <!-- 子菜单展开按钮 -->
        <el-icon
          class="children-expand-button"
          :style="{
            visibility: showChildrenButton ? 'visible' : 'hidden',
            pointerEvents: showChildrenButton ? 'auto' : 'none',
          }"
          @click.stop="toggleChildren"
        >
          <CaretRight v-if="!childrenExpanded"/>
          <CaretBottom v-else/>
        </el-icon>
      </template>

      <!-- 扩展内容插槽 -->
      <template #expand-content>
        <slot name="expand-content"></slot>
      </template>
    </ListItem>

    <!-- 子菜单区域 -->
    <el-collapse-transition>
      <div 
        v-show="childrenExpanded"
        class="custom-submenu__children"
      >
        <slot name="children"></slot>
      </div>
    </el-collapse-transition>
  </div>
</template>

<script>
import { CaretRight, CaretBottom } from '@element-plus/icons-vue'
import ListItem from '@/components/ListItem.vue'

export default {
  name: 'CustomSubMenu',
  components: { ListItem, CaretRight, CaretBottom },
  props: {
    isActive: {
      type: Boolean,
      default: false
    },
    showChildrenButton: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      childrenExpanded: false
    }
  },
  methods: {
    toggleChildren() {
      this.childrenExpanded = !this.childrenExpanded
    }
  }
}
</script>

<style scoped>
.custom-submenu {
  position: relative;
  transition: all 0.3s;
  border: 1px solid var(--el-collapse-border-color);
  border-radius: 4px;
  padding-left: 16px;
  margin: 10px 0;
}

.is-active {
  z-index: 1;
  background-color: #f0f0f0;
}

.custom-submenu__children {
  padding-left: 20px;
}

.children-expand-button {
  color: var(--el-text-color-secondary);
  cursor: pointer;
  transition: transform 0.3s;
}

.children-expand-button:hover {
  color: var(--el-color-primary);
}
</style>