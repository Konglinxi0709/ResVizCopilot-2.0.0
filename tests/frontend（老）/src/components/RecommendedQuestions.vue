<template>
  <div class="recommended-questions" v-if="questions.length > 0">
    <el-button
      v-for="(question, index) in questions"
      :key="index"
      class="recommended-button"
      @click="$emit('question-click', question)"
    >
      {{ question }}
    </el-button>
  </div>
</template>

<script>
export default {
  props: {
    questions: {
      type: Array,
      default: () => []
    }
  }
}
</script>

<style scoped>
.recommended-questions {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  background-color: #fdfdfd;
}

.recommended-button {
  margin-left: 11px;
  border-radius: 20px;
  background-color: #e0e0e0;
  padding: 5px 10px;
  font-size: 14px;
  text-align: center;
}
</style>