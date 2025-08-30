<template>
  <div class="overall-container">
    <div class="header">
      <div class="title-bar">
        <!-- 标题和操作按钮区域 -->
        <div class="title-wrapper">
          <h1 class="vis-title">
            <el-text tag="b" size="large" truncated>
              {{ visConfig.name }}
            </el-text>
          </h1>
          <div class="action-buttons">
            <!-- 修改按钮 -->
            <el-button 
              v-if="!editMode"
              type="primary" 
              link 
              @click="editMode = true"
              class="edit-btn"
            >
              <el-icon><MagicStick /></el-icon>
              <span>修改</span>
            </el-button>
            
            <!-- 删除按钮 -->
            <el-button 
              type="danger" 
              link
              class="delete-btn"
            >
              <el-icon><Delete /></el-icon>
              <span>删除</span>
            </el-button>
          </div>
        </div>

        <!-- 修改输入区域 -->
        <transition name="el-zoom-in-top">
          <div v-if="editMode" class="edit-area">
            <div class="edit-controls">
              <el-icon class="edit-icon"><Avatar /></el-icon>
              <el-input
                v-model="editInput"
                placeholder="输入您的修改要求"
                clearable
                class="edit-input"
              />
              <el-button 
                type="success" 
                link
                class="submit-btn"
              >
                <el-icon><MagicStick /></el-icon>
                <span>提交</span>
              </el-button>
              <el-button 
                type="info" 
                link 
                @click="editMode = false"
                class="cancel-btn"
              >
                <el-icon><Close /></el-icon>
                <span>取消</span>
              </el-button>
            </div>
          </div>
        </transition>
      </div>
    </div>
    <div class="visualization-container">
      <div class="zoom-controls">
        <el-button 
          circle 
          @click="zoomIn"
          icon="Plus"
          class="zoom-button"
        />
        <el-button 
          circle 
          @click="zoomOut"
          icon="Minus"
          class="zoom-button"
        />
      </div>
      <div class="scroll-container">
        <div 
          v-loading="loading"
          :element-loading-text="loadingText"
          ref="svgWrapper" 
          class="svg-wrapper" 
          :style="svgWrapperStyle"
        >
          <div ref="svgContainer" class="svg-container">
            <!-- SVG内容将通过D3渲染到这里 -->
          </div>
        </div>
      </div>
    </div>
    <div class="controls-panel">
      <div class="controls-header">
        <el-select
          v-model="currentOperation"
          class="operation-select"
        >
          <el-option value="single-time" label="新选区" />
          <el-option value="union" label="并集" />
          <el-option value="intersection" label="交集" />
          <el-option value="difference" label="差集" />
        </el-select>
        <el-button
          type="primary"
          @click="handleCreateSelection"
          icon="DocumentAdd"
          class="create-btn"
        >
          创建选区
        </el-button>
      </div>
      <el-slider
        v-model="scoreRange"
        range
        :max="100"
        :format-tooltip="val => `${val}%`"
        class="score-slider"
      />
      
      <!-- 选区列表 -->
      <SelectionList
        :ordered-selections="orderedSelections"
        @copy="copyId"
        @rename="renameSelection"
        @delete="deleteSelection"
      />
    </div>
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      class="error-alert"
    />
  </div>
</template>

<script>
import * as d3 from 'd3';
import * as d3annotation from 'd3-svg-annotation';
import xpack from '@/scripts/xpack';
import * as topojson from "topojson-client";
import seedrandom from "seedrandom";
import * as Papa from "papaparse";
import {voronoiTreemap} from "d3-voronoi-treemap";
import {jLouvain} from "jlouvain";
import ForceGraph3D from "3d-force-graph";
import cloud from "d3-cloud";
import { SelectionTool } from '@/scripts/selection';
import { ElMessage } from 'element-plus';
import { MagicStick, Delete, Avatar, Close } from '@element-plus/icons-vue'
  
import _ from 'lodash';
import SelectionList from '@/components/SelectionList.vue';
import { handleResult } from '@/scripts/handleNodeResult'
import axios from 'axios';

export default {
  components: {
    MagicStick,
    Delete,
    Avatar,
    Close,
    SelectionList,
  },
  props: {
    visConfig: {
      type: Object,
      required: true
    }
  },

  data() {
    return {
      editMode: false,
      editInput: '',
      loading: true,
      loadingText: '正在加载可视化...',
      error: null,
      currentOperation: "single-time",
      scaleFactor: 1,
      containerWidth: 0,
      
      // D3相关引用
      svg: null,
      selectionTool: null,
      visualizationData: null,
      renderFunction: null,
      
      // 尺寸样式
      svgWrapperStyle: {
        width: 2250,
        height: 1000,
        transform: `scale(1)`,
        transformOrigin: '0 0'
      },

      // 滑动条
      scoreRange: [100, 100],
      
      // 防抖相关
      resizeTimeout: null,
      lastWidth: 0,
      resizeObserver: null,

      // 选区列表
      selections: {},
    }
  },

  computed: {
    scaledWidth() {
      return this.svgWrapperStyle.width * this.scaleFactor
    },
    orderedSelections() {
      return Object.values(this.selections)
        .sort((a, b) => b.id - a.id) // 按创建时间排序
    }
  },

  methods: {
    loadVisualization() {
      if (!this.visConfig) {
        this.error = `可视化配置加载失败`;
        this.loading = false;
        return;
      }
      this.visualizationData = _.cloneDeep(this.visConfig.processed_data);
      this.renderFunction = new Function(this.visConfig.visualization_code)();
      this.loading = false;
      this.selections = _.cloneDeep(this.visConfig.selections);
      console.log(this.selections)
    },

    initVisualization() {
      if (!this.$refs.svgContainer || !this.renderFunction) {
        this.error = `容器或函数加载出错`;
        return;
      }
      this.error = null
      const padding = 50;

      // 清空之前的SVG
      d3.select(this.$refs.svgContainer).select('svg').remove();
      this.svg = d3.select(this.$refs.svgContainer)
        .append('svg')
        .attr('width', this.svgWrapperStyle.width)
        .attr('height', this.svgWrapperStyle.height)
        .node();
      // 执行渲染
      this.renderFunction(
        this.visualizationData,
        this.svg,
        this.svgWrapperStyle.width,
        this.svgWrapperStyle.height,
        padding, 
        d3, 
        xpack, 
        d3annotation,
        topojson, 
        seedrandom, 
        Papa, 
        voronoiTreemap, 
        jLouvain, 
        ForceGraph3D, 
        cloud
      );
      
      // 初始化选区工具
      this.selectionTool = new SelectionTool(d3.select(this.svg));
      this.setupEventListeners();
    },

    handleResize(entries) {
      const entry = entries[0];
      if (!entry) return;

      const newWidth = entry.contentRect.width;
      if (Math.abs(newWidth - this.lastWidth) < 1) return;
      this.lastWidth = newWidth;

      if (this.resizeTimeout) {
        cancelAnimationFrame(this.resizeTimeout);
      }
      
      this.resizeTimeout = requestAnimationFrame(() => {
        this.containerWidth = newWidth;
        this.scaleFactor = 1.2 * newWidth / this.svgWrapperStyle.width;
        setTimeout(() => this.initVisualization(), 50);
      });
    },

    zoomIn() {
      this.scaleFactor = Math.min(this.scaleFactor * 1.1, 3);
      this.updateTransform();
    },

    zoomOut() {
      this.scaleFactor = Math.max(this.scaleFactor * 0.9, 0.5);
      this.updateTransform();
    },

    updateTransform() {
      this.svgWrapperStyle.transform = `scale(${this.scaleFactor})`;
    },

    setupEventListeners() {
      const svgNode = this.svg;
      if (!svgNode) return;

      svgNode.addEventListener('mousedown', this.handleMouseDown);
      svgNode.addEventListener('mousemove', this.handleMouseMove);
      svgNode.addEventListener('mouseup', this.handleMouseUp);
    },

    handleMouseDown(event) {
      this.selectionTool?.startDrawing(event);
    },

    handleMouseMove(event) {
      this.selectionTool?.updateDrawing(event);
    },

    handleMouseUp() {
      if (!this.selectionTool) return;
      this.selectionTool.selectType = this.currentOperation || 'single-time';
      this.selectionTool.endDrawing();
    },

    async copyId(selection) {
      const textToCopy = `@${this.visConfig.id}.${selection.id}_${selection.name}`;
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
    },

    async handleCreateSelection() {
      const currentSelection = this.selectionTool.getSelection();
      if (!currentSelection || currentSelection.length === 0) {
        ElMessage.warning('当前没有选中的元素');
        return;
      }
      try {
        const res = await axios.post(`/api/visualizations/${this.visConfig.id}/add_selection`, {
          data: currentSelection
        })
        this.selections = await handleResult(this.selections, res.data)
        this.$message.success('选区创建成功')
      } catch (error) {
        this.$message.error(`选区创建失败: ${error.response?.data?.detail || error.message}`)
      }
    },
    async renameSelection(selection) {
      let new_name = '';
      try {
        const { value: newName } = await this.$prompt('请输入新名称', {
          inputValue: selection.name,
          inputValidator: (value) => {
            if (!value.trim()) return '名称不能为空';
            const isNameExists = Object.values(this.selections).some(
              (s) => s.id !== selection.id && s.name === value
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
          const res = await axios.post(`/api/visualizations/${this.visConfig.id}/rename_selection`, 
            { 
              selection_id: selection.id,
              new_name: new_name,
            }
          );
          this.selections = await handleResult(this.selections, res.data);
          ElMessage.success('重命名成功');
        }
      } catch (error) {
        if (!error.isCancel) {
          ElMessage.error(`重命名失败: ${error.response?.data?.detail || error.message}`);
        }
      }
    },


    async deleteSelection(selection) {
      try {
        await this.$confirm(
          `确定删除选区【${selection.name}】吗？`,
          '删除确认',
          {
            confirmButtonText: '确认',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        // 用户确认后继续执行
        const res = await axios.delete(
          `/api/visualizations/${this.visConfig.id}/delete_selection/${selection.id}`
        )
        this.selections = await handleResult(this.selections, res.data)
        ElMessage.success('删除成功')
        console.log(this.selections)
      } catch (error) {
        // 区分用户取消和真实错误
        if (error !== 'cancel') {
          ElMessage.error(
            `删除失败: ${error.response?.data?.detail || error.message}`
          )
        }
      }
    },

    initResizeObserver() {
      this.resizeObserver = new ResizeObserver(_.debounce(this.handleResize, 100));
      if(this.$refs.svgWrapper) {
        this.resizeObserver.observe(this.$refs.svgWrapper);
      }
    }
  },

  mounted() {
    this.initResizeObserver();
    this.loadVisualization();
    this.initVisualization();
  },

  beforeUnmount() {
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
    if (this.resizeTimeout) {
      cancelAnimationFrame(this.resizeTimeout);
    }
    
    // 清理事件监听
    if (this.svg) {
      this.svg.removeEventListener('mousedown', this.handleMouseDown);
      this.svg.removeEventListener('mousemove', this.handleMouseMove);
      this.svg.removeEventListener('mouseup', this.handleMouseUp);
    }
  },
  watch: {
    visConfig: {
      handler(newVal) {
        if (newVal) {
          this.loadVisualization()
          this.initVisualization()
        }
      },
      immediate: true,
      deep: true
    },
    scoreRange(newRange) {
      if (this.selectionTool) {
        this.selectionTool.setScoreRange(newRange);
        this.selectionTool.highlightSelectedElements();
      }
    },
  }
}
</script>

<style scoped>
/* Header区域样式 */
.header {
  margin-bottom: 10px;
  padding: 0 15px;
  border-radius: 4px;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
}

.title-bar {
  padding: 10px 0;
}

.title-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.vis-title {
  margin: 0;
  font-size: 1.5rem;
  color: #2c3e50;
  flex: 1;
  min-width: 0; /* 确保文本截断生效 */
}

.vis-title :deep(.el-text) {
  display: inline-flex;
  align-items: center;
  max-width: 70%;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-left: 20px;
}

/* 编辑区域样式 */
.edit-area {
  margin-top: 15px;
  padding: 12px;
  background: rgba(236, 238, 242, 0.3);
  border-radius: 6px;
}

.edit-controls {
  display: flex;
  align-items: center;
  gap: 15px;
}

.edit-icon {
  font-size: 1.2rem;
  color: #7c8ca5;
  margin-right: 8px;
}

.edit-input {
  flex: 1;
  max-width: 600px;
  transition: all 0.3s;
}

.submit-btn {
  margin-left: auto;
}

/* 按钮微调 */
:deep(.el-button) {
  padding: 8px 12px;
}

:deep(.el-button span) {
  margin-left: 6px;
}

.delete-btn :deep(.el-icon) {
  color: #f56c6c;
}

.cancel-btn :deep(.el-icon) {
  color: #909399;
}

/* 过渡动画 */
.el-zoom-in-top-enter-active,
.el-zoom-in-top-leave-active {
  transition: all 0.3s cubic-bezier(0.3, 1.3, 0.3, 1);
}

.el-zoom-in-top-enter-from,
.el-zoom-in-top-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}










.overall-container {
  position: relative;
  background-color: #ffffff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  margin: 0 auto 20px; /* 上下20px，左右自动居中 */
  padding: 15px;
  max-width: 100%; /* 确保宽度不超过父容器 */
  box-sizing: border-box; /* 包含内边距和边框在内计算宽度 */
}

.visualization-container {
  position: relative;
  width: 100%;
  height: 50vh;
}

.scroll-container {
  position: relative;
  width: 100%;
  height: 100%;
  background: #f5f7fa;
  overflow: auto;
}

.svg-wrapper {
  position: relative;
  margin-left: -10%; /* 补偿120%宽度带来的偏移 */
}

.controls-panel {
  position: relative;
  top: 20px;
  right: 20px;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.9);
  padding: 10px;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.operation-select {
  width: 200px;
  margin-bottom: 10px;
}

.copy-btn {
  width: 100%;
}

.error-alert {
  margin: 20px;
}

.zoom-controls {
  position: absolute; /* 使用绝对定位 */
  top: 20px;         /* 距离父容器顶部的距离 */
  right: 30px;       /* 距离父容器右侧的距离 */
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 1001;     /* 确保它在其他元素之上 */
}

.zoom-button {
  width: 40px;
  height: 40px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.controls-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 15px; /* 适当增加内边距 */
}

.controls-header {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.score-slider {
  width: 100%;
  margin-top: 10px;
}

/* 选区列表 */
.selection-list {
  margin-top: 20px;
  border-top: 1px solid #ebeef5;
  padding-top: 15px;
}

.selection-title {
  font-weight: 500;
  margin-left: 8px;
}

.create-btn {
  flex-shrink: 0;
}

.el-table {
  margin-top: 10px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,.1);
}

:deep(.el-table__empty-block) {
  min-height: 100px;
}
</style>