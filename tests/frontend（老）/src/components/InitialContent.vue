<template>
  <div class="initial-content">
    <img src="@/assets/logo-lab.png" alt="Logo" class="logo" />
    <div class="preset-questions">
      <el-button
        v-for="(question, index) in presetQuestions"
        :key="index"
        @click="$emit('question-click', question)"
        class="preset-question-button"
      >
        {{ question }}
      </el-button>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    presetQuestions: {
      type: Array,
      default: () => []
    }
  }
}
</script>

<style scoped>
.initial-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.logo {
  width: 150px;
  height: 150px;
  margin-bottom: 20px;
  margin-left: 20px;
}

.preset-questions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
}

.preset-question-button {
  width: 350px;
  min-height: 40px;       /* 使用最小高度以适应内容 */
  height: auto;           /* 高度自适应 */
  padding: 8px 16px;      /* 添加内边距 */
  white-space: normal;    /* 允许换行 */
  overflow-wrap: break-word; /* 允许单词内换行 */
  text-align: center;     /* 文字居中 */
  display: inline-flex;   /* 保持原有 flex 布局 */
  justify-content: center;
  align-items: center;
  line-height: 1.2;       /* 调整行高 */
}
</style>