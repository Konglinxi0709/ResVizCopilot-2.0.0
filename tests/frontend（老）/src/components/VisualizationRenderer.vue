<!-- VisualizationRenderer.vue -->
<template>
  <div class="overall-container">
    <div class="header">
      <div class="title-bar">
        <div class="title-wrapper">
          <h1 class="vis-title">
            <el-text tag="b" size="large" truncated>
              {{ visConfig.name }}
            </el-text>
          </h1>
          <div class="action-buttons">
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
            <el-button 
              type="danger" 
              link
              class="delete-btn"
              @click="handleDelete"
            >
              <el-icon><Delete /></el-icon>
              <span>删除</span>
            </el-button>
          </div>
        </div>

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
                @click="handleSubmitEdit"
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
    
    <D3Renderer
      :vis-config="visConfig"
      @error="handleError"
      @delete-visualization="$emit('delete', $event)"
    />

    <el-alert v-if="error" :title="error" type="error" show-icon class="error-alert" />
  </div>
</template>

<script>
import D3Renderer from './D3Renderer.vue';

export default {
  components: { D3Renderer },
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
      error: null
    }
  },
  methods: {
    handleError(message) {
      this.error = message;
      setTimeout(() => this.error = null, 5000);
    }
  }
}
</script>

<style scoped>
/* 保持原有header部分样式 */
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
  min-width: 0;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-left: 20px;
}

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

.edit-input {
  flex: 1;
  max-width: 600px;
}

.error-alert {
  margin: 20px;
}

/* 保持全局容器样式 */
.overall-container {
  position: relative;
  background-color: #ffffff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  margin: 0 auto 20px;
  padding: 15px;
  max-width: 100%;
  box-sizing: border-box;
}
</style>