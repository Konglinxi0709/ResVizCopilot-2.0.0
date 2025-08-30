<!-- D3Renderer.vue -->
<template>
  <div class="d3-renderer">
    <div class="visualization-container">
      <div class="zoom-controls">
        <el-button circle @click="zoomIn" icon="Plus" />
        <el-button circle @click="zoomOut" icon="Minus" />
      </div>
      <div class="scroll-container">
        <div 
          v-loading="loading"
          :element-loading-text="loadingText"
          ref="svgWrapper" 
          class="svg-wrapper" 
          :style="svgWrapperStyle"
        >
          <div ref="svgContainer" class="svg-container"></div>
        </div>
      </div>
    </div>

    <div class="controls-panel">
      <div class="controls-header">
        <el-select v-model="currentOperation" class="operation-select">
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
      <SelectionList
        :ordered-selections="orderedSelections"
        @copy="copyId"
        @rename="renameSelection"
        @delete="deleteSelection"
      />
    </div>
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
import { ElMessage, ElMessageBox } from 'element-plus';
import _ from 'lodash';
import SelectionList from '@/components/SelectionList.vue';
import { handleResult } from '@/scripts/handleNodeResult';
import axios from 'axios';

export default {
  components: { SelectionList },
  props: {
    visConfig: Object,
  },
  emits: ['error', 'delete-visualization'],
  data() {
    return {
      selections: _.cloneDeep(this.visConfig.selections),
      loading: true,
      loadingText: '正在加载可视化...',
      currentOperation: "single-time",
      scaleFactor: 1,
      containerWidth: 0,
      svg: null,
      selectionTool: null,
      visualizationData: null,
      renderFunction: null,
      svgWrapperStyle: {
        width: 2250,
        height: 1000,
        transform: 'scale(1)',
        transformOrigin: '0 0'
      },
      scoreRange: [100, 100],
      resizeObserver: null,
      resizeTimeout: null,
      lastWidth: 0
    }
  },
  computed: {
    orderedSelections() {
      return Object.values(this.selections).sort((a, b) => b.id - a.id);
    }
  },
  methods: {
    async handleCreateSelection() {
      try {
        const res = await axios.post(`/api/visualizations/${this.visConfig.id}/add_selection`, {
          data: this.selectionTool.getSelection()
        });
        this.selections = await handleResult(this.selections, res.data);
        ElMessage.success('选区创建成功');
      } catch (error) {
        this.$emit('error', `选区创建失败: ${error.message}`);
      }
    },

    async renameSelection(selection) {
      try {
        const { value: newName } = await this.$prompt('请输入新名称', {
          inputValue: selection.name,
          inputValidator: (value) => this.validateSelectionName(value, selection)
        });

        const res = await axios.post(`/api/visualizations/${this.visConfig.id}/rename_selection`, {
          selection_id: selection.id,
          new_name: newName
        });
        this.selections = await handleResult(this.selections, res.data);
        ElMessage.success('重命名成功');
      } catch (error) {
        if (!error.toString().includes('cancel')) {
          ElMessage.error(`重命名失败: ${error.message}`);
        }
      }
    },

    async deleteSelection(selection) {
      try {
        await ElMessageBox.confirm(
          `确定删除选区【${selection.name}】吗？`,
          '删除确认',
          { type: 'warning' }
        );

        const res = await axios.delete(
          `/api/visualizations/${this.visConfig.id}/delete_selection/${selection.id}`
        );
        this.selections = await handleResult(this.selections, res.data);
        ElMessage.success('删除成功');
      } catch (error) {
        if (!error.toString().includes('cancel')) {
          ElMessage.error(`删除失败: ${error.message}`);
        }
      }
    },

    validateSelectionName(value, currentSelection) {
      if (!value.trim()) return '名称不能为空';
      return !Object.values(this.selections).some(
        s => s.id !== currentSelection.id && s.name === value
      );
    },

    async copyId(selection) {
      const textToCopy = `@${this.visConfig.id}.${selection.id}_${selection.name} `;
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


    initRenderer() {
      this.visualizationData = _.cloneDeep(this.visConfig.processed_data);
      try {
        this.renderFunction = new Function(this.visConfig.visualization_code)();
        setTimeout(this.initVisualization, 50);
      } catch (e) {
        this.$emit('error', `初始化渲染代码执行错误: ${e.message}`);
      }
    },
    initVisualization() {
      if (!this.$refs.svgContainer || !this.renderFunction) {
        this.$emit('error', '容器或函数加载出错');
        console.log(this.$refs.svgContainer, this.renderFunction)
        return;
      }
      
      d3.select(this.$refs.svgContainer).select('svg').remove();
      this.svg = d3.select(this.$refs.svgContainer)
        .append('svg')
        .attr('width', this.svgWrapperStyle.width)
        .attr('height', this.svgWrapperStyle.height)
        .node();

      this.renderFunction(
        this.visualizationData,
        this.svg,
        this.svgWrapperStyle.width,
        this.svgWrapperStyle.height,
        50, // padding
        d3, xpack, d3annotation, topojson, seedrandom, Papa,
        voronoiTreemap, jLouvain, ForceGraph3D, cloud
      );

      this.selectionTool = new SelectionTool(d3.select(this.svg));
      this.setupEventListeners();
      this.loading = false;
    },
    handleResize(entries) {
      const entry = entries[0];
      if (!entry) return;

      const newWidth = entry.contentRect.width;
      if (Math.abs(newWidth - this.lastWidth) < 1) return;
      this.lastWidth = newWidth;

      cancelAnimationFrame(this.resizeTimeout);
      this.resizeTimeout = requestAnimationFrame(() => {
        this.containerWidth = newWidth;
        this.scaleFactor = 1.2 * newWidth / this.svgWrapperStyle.width;
        this.updateTransform();
        setTimeout(this.initVisualization, 50);
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
      this.selectionTool.selectType = this.currentOperation;
      this.selectionTool.endDrawing();
    },
    initResizeObserver() {
      this.resizeObserver = new ResizeObserver(_.debounce(this.handleResize, 100));
      if (this.$refs.svgWrapper) {
        this.resizeObserver.observe(this.$refs.svgWrapper);
      }
    }
  },
  mounted() {
    this.selections = _.cloneDeep(this.visConfig.selections);
    this.initRenderer();
    this.initResizeObserver();
  },
  beforeUnmount() {
    if (this.resizeObserver) this.resizeObserver.disconnect();
    if (this.resizeTimeout) cancelAnimationFrame(this.resizeTimeout);
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
          this.selections = _.cloneDeep(newVal.selections);
          this.initRenderer();
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
    }
  }
}
</script>

<style scoped>
.d3-renderer {
  position: relative;
  margin: 0 auto 20px; /* 上下20px，左右自动居中 */
  padding: 15px;
  max-width: 100%; /* 确保宽度不超过父容器 */
  box-sizing: border-box; /* 包含内边距和边框在内计算宽度 */
}

.visualization-container {
  position: relative;
  width: 100%;
  height: 60vh;
  background: #f8f9fa;
  border-radius: 8px;
  overflow: hidden;
}

.scroll-container {
  height: 100%;
  overflow: auto;
  background: #f5f7fa;
}

.svg-wrapper {
  position: relative;
  margin-left: -10%;
}

.controls-panel {
  position: relative;
  top: 20px;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.9);
  padding: 10px;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
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

.zoom-controls {
  position: absolute;
  top: 20px;
  right: 30px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 1001;
}

.operation-select {
  width: 200px;
}

.create-btn {
  flex-shrink: 0;
}

.score-slider {
  margin: 15px 0;
}
</style>