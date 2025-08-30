<template>
    <div class="statistic-card">
      <el-statistic :value="value">
        <template #title>
          <div style="display: inline-flex; align-items: center">
            {{ title }}
            <el-tooltip
              v-if="tooltipContent"
              effect="dark"
              :content="tooltipContent"
              placement="top"
            >
              <el-icon style="margin-left: 4px" :size="12">
                <Warning />
              </el-icon>
            </el-tooltip>
          </div>
        </template>
      </el-statistic>
      <div class="statistic-footer">
        <div
          v-for="(item, index) in footerItems"
          :key="index"
          class="footer-item"
        >
          <span v-if="item.label">{{ item.label }}</span>
          <span v-if="item.value" :class="item.color">
            {{ item.value }}
            <el-icon v-if="item.icon">
              <component :is="item.icon" />
            </el-icon>
          </span>
          <el-icon v-if="item.icon && !item.value" :size="item.size">
            <component :is="item.icon" />
          </el-icon>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { Warning } from '@element-plus/icons-vue';
  
  export default {
    components: {
      Warning,
    },
    props: {
      value: {
        type: Number,
        required: true,
      },
      title: {
        type: String,
        required: true,
      },
      tooltipContent: {
        type: String,
        default: '',
      },
      footerItems: {
        type: Array,
        default: () => [],
      },
    },
  };
  </script>
  
  <style scoped>
  .statistic-card {
    height: 100%;
    padding: 20px;
    border-radius: 4px;
    background-color: var(--el-bg-color-overlay);
  }
  
  .statistic-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    font-size: 12px;
    color: var(--el-text-color-regular);
    margin-top: 16px;
  }
  
  .statistic-footer .footer-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .statistic-footer .footer-item span:last-child {
    display: inline-flex;
    align-items: center;
    margin-left: 4px;
  }
  
  .green {
    color: var(--el-color-success);
  }
  .red {
    color: var(--el-color-error);
  }
  </style>